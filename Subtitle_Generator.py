#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 22 17:45:50 2024

@author: gn
"""

import streamlit as st
import whisper
import ffmpeg
import tempfile

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

# Streamlit UI
st.title("Video Subtitle Generator")


# Adding LinkedIn link and creator information
st.markdown("""
<div style="display: flex; align-items: center; background-color: black; padding: 5px; border-radius: 3px;">
    <span style="font-size: 18px; color: #2e8b57; font-weight: bold; margin-right: 10px;">Created by:</span>
    <a href="https://www.linkedin.com/in/gn-raavanan" target="_blank" style="text-decoration: none; display: flex; align-items: center;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/c/ca/LinkedIn_logo_initials.png" alt="LinkedIn" style="width: 20px; height: 20px; margin-right: 5px;">
        <span style="font-size: 18px; font-weight: bold; color: #fff;">Gokul nath</span>
    </a>
</div>
""", unsafe_allow_html=True)  # Adding a LinkedIn link with an icon and creator's name


st.write("Upload a video file to generate subtitles")

if "subtitles_generated" not in st.session_state:
    st.session_state.subtitles_generated = False

uploaded_file = st.file_uploader("Choose a video file...", type=["mp4", "mkv", "avi", "mov"])

if uploaded_file is not None and not st.session_state.subtitles_generated:
    # Extract audio from the uploaded video
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        temp_video.write(uploaded_file.read())
        video_path = temp_video.name

    # Extract audio from video
    st.write("Extracting audio from video...")
    audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
    ffmpeg.input(video_path).output(audio_path, ac=1, ar=16000).run(overwrite_output=True)

    # Generate subtitles
    st.write("Generating subtitles...")
    result = generate_subtitles_whisper(audio_path)

    # Save subtitles to SRT
    srt_path = tempfile.NamedTemporaryFile(delete=False, suffix=".srt").name
    save_subtitles_srt(result, srt_path)

    # Store the path in session state to avoid re-running
    st.session_state.srt_path = srt_path
    st.session_state.subtitles_generated = True

if st.session_state.subtitles_generated:
    # Provide download link for the generated subtitles
    with open(st.session_state.srt_path, "r") as file:
        st.download_button(
            label="Download Subtitles",
            data=file,
            file_name="subtitles.srt",
            mime="text/plain"
        )


