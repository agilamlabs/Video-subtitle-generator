#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 22 17:45:50 2024

@author: gn
"""

from flask import Flask, request, jsonify, send_file, render_template
import whisper
import ffmpeg
import tempfile
import os
import uuid
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 10GB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Store processing status
processing_status = {}

def generate_subtitles_whisper(audio_path):
    """Generate subtitles from an audio file."""
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, fp16=False)
    return result

def save_subtitles_srt(result, output_path):
    """Save subtitles to an SRT file."""
    with open(output_path, "w", encoding="utf-8") as srt_file:
        for i, segment in enumerate(result['segments']):
            start_time = format_time(segment['start'])
            end_time = format_time(segment['end'])
            text = segment['text']

            srt_file.write(f"{i+1}\n{start_time} --> {end_time}\n{text.strip()}\n\n")

def format_time(seconds):
    """Format time in SRT style (hh:mm:ss,ms)."""
    millis = int((seconds % 1) * 1000)
    seconds = int(seconds)
    mins, secs = divmod(seconds, 60)
    hrs, mins = divmod(mins, 60)
    return f"{hrs:02}:{mins:02}:{secs:02},{millis:03}"

@app.route('/')
def index():
    """Serve the main HTML page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    """Handle video upload and start processing."""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Generate unique ID for this upload
    upload_id = str(uuid.uuid4())
    
    # Save uploaded video
    filename = secure_filename(file.filename)
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{upload_id}_{filename}")
    file.save(video_path)
    
    # Initialize processing status
    processing_status[upload_id] = {
        'status': 'processing',
        'progress': 0,
        'message': 'Starting processing...'
    }
    
    # Start processing in background (in production, use Celery or similar)
    import threading
    thread = threading.Thread(target=process_video, args=(upload_id, video_path))
    thread.start()
    
    return jsonify({
        'upload_id': upload_id,
        'message': 'Upload successful, processing started'
    })

def process_video(upload_id, video_path):
    """Process video in background thread."""
    try:
        # Update status
        processing_status[upload_id]['message'] = 'Extracting audio from video...'
        processing_status[upload_id]['progress'] = 20
        
        # Extract audio from video
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{upload_id}_audio.wav")
        ffmpeg.input(video_path).output(audio_path, ac=1, ar=16000).run(overwrite_output=True)
        
        # Update status
        processing_status[upload_id]['message'] = 'Generating subtitles...'
        processing_status[upload_id]['progress'] = 40
        
        # Generate subtitles
        result = generate_subtitles_whisper(audio_path)
        
        # Update status
        processing_status[upload_id]['message'] = 'Saving subtitles...'
        processing_status[upload_id]['progress'] = 60
        
        # Save subtitles to SRT
        srt_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{upload_id}_subtitles.srt")
        save_subtitles_srt(result, srt_path)
        
        # Update status
        processing_status[upload_id]['message'] = 'Embedding subtitles into video...'
        processing_status[upload_id]['progress'] = 80
        
        # Embed subtitles into the video
        merged_video_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{upload_id}_with_subtitles.mp4")
        
        try:
            (
                ffmpeg
                .input(video_path)
                .output(merged_video_path, vf=f"subtitles='{srt_path}'", vcodec='libx264', acodec='aac', strict='experimental')
                .run(overwrite_output=True)
            )
        except ffmpeg.Error as e:
            processing_status[upload_id]['status'] = 'error'
            processing_status[upload_id]['message'] = f'Error embedding subtitles: {str(e)}'
            return
        
        # Clean up temporary files
        os.remove(audio_path)
        
        # Update final status
        processing_status[upload_id]['status'] = 'completed'
        processing_status[upload_id]['progress'] = 100
        processing_status[upload_id]['message'] = 'Processing completed successfully!'
        processing_status[upload_id]['srt_path'] = srt_path
        processing_status[upload_id]['video_path'] = merged_video_path
        
    except Exception as e:
        processing_status[upload_id]['status'] = 'error'
        processing_status[upload_id]['message'] = f'Error during processing: {str(e)}'

@app.route('/status/<upload_id>')
def get_status(upload_id):
    """Get processing status for an upload."""
    if upload_id not in processing_status:
        return jsonify({'error': 'Upload ID not found'}), 404
    
    return jsonify(processing_status[upload_id])

@app.route('/download/srt/<upload_id>')
def download_srt(upload_id):
    """Download SRT file."""
    if upload_id not in processing_status or processing_status[upload_id]['status'] != 'completed':
        return jsonify({'error': 'SRT file not ready'}), 404
    
    srt_path = processing_status[upload_id]['srt_path']
    return send_file(srt_path, as_attachment=True, download_name='subtitles.srt')

@app.route('/download/video/<upload_id>')
def download_video(upload_id):
    """Download processed video with subtitles."""
    if upload_id not in processing_status or processing_status[upload_id]['status'] != 'completed':
        return jsonify({'error': 'Video file not ready'}), 404
    
    video_path = processing_status[upload_id]['video_path']
    return send_file(video_path, as_attachment=True, download_name='video_with_subtitles.mp4')

@app.route('/video/<upload_id>')
def serve_video(upload_id):
    """Serve processed video for playback."""
    if upload_id not in processing_status or processing_status[upload_id]['status'] != 'completed':
        return jsonify({'error': 'Video file not ready'}), 404
    
    video_path = processing_status[upload_id]['video_path']
    return send_file(video_path, mimetype='video/mp4')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 