// static/js/script.js
document.addEventListener('DOMContentLoaded', () => {
    const startButton = document.getElementById('startRecording');
    const stopButton = document.getElementById('stopRecording');
    const queryText = document.getElementById('queryText');
    const queryForm = document.getElementById('queryForm');
    const submitButton = document.getElementById('submitButton');

    // Start recording
    startButton.addEventListener('click', async () => {
        try {
            const response = await fetch('/start_recording', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();

            if (data.status === "Recording started") {
                console.log('Recording started on server...');
                startButton.classList.add('hidden');
                stopButton.classList.remove('hidden');
            } else {
                console.error('Recording already in progress');
                alert('Recording already in progress');
            }
        } catch (err) {
            console.error('Error starting recording:', err);
            alert('Error starting recording: ' + err.message);
        }
    });

    // Stop recording
    stopButton.addEventListener('click', async () => {
        try {
            const response = await fetch('/stop_recording', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (response.ok) {
                const html = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const transcribedText = doc.querySelector('input[name="query_text"]').value;

                if (transcribedText) {
                    queryText.value = transcribedText;
                    queryText.readOnly = false; // Allow editing if needed
                    submitButton.disabled = false;
                    console.log('Transcribed text received:', transcribedText);
                } else {
                    const error = doc.querySelector('.text-red-700 p')?.textContent || 'Unknown error';
                    console.error('Transcription error:', error);
                    alert(error);
                }

                startButton.classList.remove('hidden');
                stopButton.classList.add('hidden');
            } else {
                console.error('Error stopping recording:', response.statusText);
                alert('Error stopping recording');
            }
        } catch (err) {
            console.error('Error stopping recording:', err);
            alert('Error stopping recording: ' + err.message);
        }
    });

    // Handle form submission
    queryForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(queryForm);

        const response = await fetch('/query', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const html = await response.text();
            document.body.innerHTML = html; // Update the page with query results
            console.log('Query processed successfully');
        } else {
            console.error('Error processing query:', response.statusText);
            alert('Error processing query');
        }
    });

    // Enable submit button if there's pre-filled text
    if (queryText.value.trim() !== '') {
        submitButton.disabled = false;
        console.log('Form auto-filled with initial text:', queryText.value);
    }
});