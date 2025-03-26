let mediaRecorder;
let audioChunks = [];
let audioStream; // To store the stream so we can stop it later

// Start recording
document.getElementById('startButton').addEventListener('click', async () => {
    try {
        audioChunks = []; // Clear previous recordings
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioStream = stream; // Store the stream for later
        mediaRecorder = new MediaRecorder(stream);
        
        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const audioUrl = URL.createObjectURL(audioBlob);
            document.getElementById('audioPlayback').src = audioUrl;
        };
        
        mediaRecorder.start(1000); // Collect data every 1 second
        document.getElementById('startButton').disabled = true;
        document.getElementById('stopButton').disabled = false;
        document.getElementById('responseText').textContent = "Recording...";
    } catch (error) {
        console.error('Error accessing microphone:', error);
        document.getElementById('responseText').textContent = "Error accessing microphone";
    }
});

// Stop recording - THIS WAS MISSING
document.getElementById('stopButton').addEventListener('click', () => {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        
        // Stop all tracks in the stream
        if (audioStream) {
            audioStream.getTracks().forEach(track => track.stop());
        }
        
        document.getElementById('startButton').disabled = false;
        document.getElementById('stopButton').disabled = true;
        document.getElementById('responseText').textContent = "Recording stopped";
    }
});

async function sendAudio() {
    if (audioChunks.length === 0) {
        console.error('No audio data available');
        document.getElementById('responseText').textContent = "No recording to send";
        return;
    }

    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');
    
    try {
        document.getElementById('responseText').textContent = "Sending audio...";
        const response = await fetch("http://127.0.0.1:8080/submit-audio", {
            method: "POST",
            body: formData
        });
        
        const data = await response.json();
        document.getElementById('responseText').textContent = data.message || "Audio sent successfully";
    } catch (error) {
        console.error("Error:", error);
        document.getElementById('responseText').textContent = "Error sending audio";
    }
}