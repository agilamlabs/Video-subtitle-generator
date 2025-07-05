// Global variables
let currentUploadId = null;
let statusCheckInterval = null;

// DOM elements
const uploadArea = document.getElementById('uploadArea');
const videoFileInput = document.getElementById('videoFile');
const uploadSection = document.getElementById('uploadSection');
const processingSection = document.getElementById('processingSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const videoPlayer = document.getElementById('videoPlayer');
const videoSource = document.getElementById('videoSource');
const errorMessage = document.getElementById('errorMessage');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    setupDragAndDrop();
    setupFileInput();
});

// Setup drag and drop functionality
function setupDragAndDrop() {
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (isValidVideoFile(file)) {
                handleFileUpload(file);
            } else {
                showError('Please select a valid video file (MP4, MKV, AVI, or MOV)');
            }
        }
    });

    // Click to upload
    uploadArea.addEventListener('click', function() {
        videoFileInput.click();
    });
}

// Setup file input
function setupFileInput() {
    videoFileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file && isValidVideoFile(file)) {
            handleFileUpload(file);
        } else if (file) {
            showError('Please select a valid video file (MP4, MKV, AVI, or MOV)');
        }
    });
}

// Validate video file
function isValidVideoFile(file) {
    const validTypes = ['video/mp4', 'video/x-matroska', 'video/x-msvideo', 'video/quicktime'];
    const validExtensions = ['.mp4', '.mkv', '.avi', '.mov'];
    
    // Check MIME type
    if (validTypes.includes(file.type)) {
        return true;
    }
    
    // Check file extension as fallback
    const fileName = file.name.toLowerCase();
    return validExtensions.some(ext => fileName.endsWith(ext));
}

// Handle file upload
async function handleFileUpload(file) {
    try {
        // Show processing section
        showProcessingSection();
        
        // Create FormData
        const formData = new FormData();
        formData.append('video', file);
        
        // Upload file
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Upload failed');
        }
        
        const data = await response.json();
        currentUploadId = data.upload_id;
        
        // Start monitoring progress
        startProgressMonitoring();
        
    } catch (error) {
        console.error('Upload error:', error);
        showError(error.message || 'Failed to upload video');
    }
}

// Show processing section
function showProcessingSection() {
    uploadSection.style.display = 'none';
    processingSection.style.display = 'block';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
    
    // Reset progress
    progressFill.style.width = '0%';
    progressText.textContent = 'Starting processing...';
    resetSteps();
}

// Start progress monitoring
function startProgressMonitoring() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    statusCheckInterval = setInterval(async () => {
        try {
            const response = await fetch(`/status/${currentUploadId}`);
            if (!response.ok) {
                throw new Error('Failed to get status');
            }
            
            const status = await response.json();
            updateProgress(status);
            
            if (status.status === 'completed') {
                clearInterval(statusCheckInterval);
                showResults();
            } else if (status.status === 'error') {
                clearInterval(statusCheckInterval);
                showError(status.message);
            }
            
        } catch (error) {
            console.error('Status check error:', error);
            clearInterval(statusCheckInterval);
            showError('Failed to check processing status');
        }
    }, 2000); // Check every 2 seconds
}

// Update progress display
function updateProgress(status) {
    const progress = status.progress || 0;
    const message = status.message || 'Processing...';
    
    progressFill.style.width = `${progress}%`;
    progressText.textContent = message;
    
    // Update steps based on progress
    updateSteps(progress);
}

// Update processing steps
function updateSteps(progress) {
    const steps = document.querySelectorAll('.step');
    
    steps.forEach((step, index) => {
        step.classList.remove('active', 'completed');
        
        if (progress >= (index + 1) * 25) {
            step.classList.add('completed');
        } else if (progress >= index * 25) {
            step.classList.add('active');
        }
    });
}

// Reset steps
function resetSteps() {
    const steps = document.querySelectorAll('.step');
    steps.forEach(step => {
        step.classList.remove('active', 'completed');
    });
}

// Show results section
function showResults() {
    processingSection.style.display = 'none';
    resultsSection.style.display = 'block';
    
    // Set video source
    videoSource.src = `/video/${currentUploadId}`;
    videoPlayer.load();
}

// Show error section
function showError(message) {
    uploadSection.style.display = 'none';
    processingSection.style.display = 'none';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'block';
    
    errorMessage.textContent = message;
}

// Download video with subtitles
function downloadVideo() {
    if (currentUploadId) {
        window.open(`/download/video/${currentUploadId}`, '_blank');
    }
}

// Download SRT file
function downloadSRT() {
    if (currentUploadId) {
        window.open(`/download/srt/${currentUploadId}`, '_blank');
    }
}

// Reset application
function resetApp() {
    // Clear intervals
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
        statusCheckInterval = null;
    }
    
    // Reset variables
    currentUploadId = null;
    
    // Reset file input
    videoFileInput.value = '';
    
    // Show upload section
    uploadSection.style.display = 'block';
    processingSection.style.display = 'none';
    resultsSection.style.display = 'none';
    errorSection.style.display = 'none';
    
    // Reset progress
    progressFill.style.width = '0%';
    progressText.textContent = 'Starting processing...';
    resetSteps();
}

// Utility function to show loading state
function showLoading(element) {
    element.disabled = true;
    const originalText = element.textContent;
    element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
    return originalText;
}

// Utility function to hide loading state
function hideLoading(element, originalText) {
    element.disabled = false;
    element.textContent = originalText;
}

// Add some visual feedback for file selection
function addFileSelectionFeedback(file) {
    const uploadContent = uploadArea.querySelector('.upload-content');
    const originalHTML = uploadContent.innerHTML;
    
    uploadContent.innerHTML = `
        <i class="fas fa-file-video" style="font-size: 4rem; color: #48bb78; margin-bottom: 20px;"></i>
        <h3>File Selected</h3>
        <p style="color: #48bb78; font-weight: 600;">${file.name}</p>
        <p style="color: #a0aec0; font-size: 0.9rem;">Size: ${formatFileSize(file.size)}</p>
        <p style="color: #a0aec0; font-size: 0.9rem;">Uploading...</p>
    `;
    
    // Restore original content after a delay
    setTimeout(() => {
        uploadContent.innerHTML = originalHTML;
    }, 3000);
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
} 