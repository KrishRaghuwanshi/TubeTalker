document.addEventListener("DOMContentLoaded", () => {
    const processBtn = document.getElementById("process-btn");
    const queryBtn = document.getElementById("query-btn");
    const urlInput = document.getElementById("youtube-url");
    const queryInput = document.getElementById("query-text");

    const statusContainer = document.getElementById("status-container");
    const statusMessage = document.getElementById("status-message");
    const querySection = document.getElementById("query-section");
    const resultsSection = document.getElementById("results-section");
    const answerDiv = document.getElementById("answer");
    const stopBtn = document.getElementById("stop-btn");

    const API_URL = "http://127.0.0.1:8000"; // Your FastAPI server URL

    let sessionId = null;

    processBtn.addEventListener("click", async () => {
        const url = urlInput.value;
        if (!url) {
            alert("Please enter a YouTube URL.");
            return;
        }

        // Reset UI
        querySection.style.display = "none";
        resultsSection.style.display = "none";
        statusContainer.style.display = "block";
        processBtn.disabled = true;

        try {
            const response = await fetch(`${API_URL}/process-video-async`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: url }),
            });

            if (!response.ok) throw new Error("Failed to start job.");

            const data = await response.json();
            pollJobStatus(data.job_id);

        } catch (error) {
            statusMessage.textContent = `Error: ${error.message}`;
            processBtn.disabled = false;
        }
    });

    async function pollJobStatus(jobId) {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`${API_URL}/job-status/${jobId}`);
                const data = await response.json();

                statusMessage.textContent = data.message || "Processing...";

                if (data.status === "completed") {
                    clearInterval(interval);
                    statusContainer.style.display = "none";
                    querySection.style.display = "block";
                    processBtn.disabled = false;
                    sessionId = data.result; // Save the session ID
                } else if (data.status === "failed") {
                    clearInterval(interval);
                    statusMessage.textContent = `Error: ${data.message}`;
                    processBtn.disabled = false;
                }
            } catch (error) {
                clearInterval(interval);
                statusMessage.textContent = `Error polling status: ${error.message}`;
                processBtn.disabled = false;
            }
        }, 3000); // Poll every 3 seconds
    }

    queryBtn.addEventListener("click", async () => {
        const query = queryInput.value;
        if (!query || !sessionId) {
            alert("Please enter a query and ensure a video is processed.");
            return;
        }
        
        resultsSection.style.display = "block";
        answerDiv.innerHTML = "Thinking...";
        queryBtn.disabled = true;

        try {
            const response = await fetch(`${API_URL}/query`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: query, session_id: sessionId }),
            });

            if (!response.ok) throw new Error("Query failed.");

            const data = await response.json();
            answerDiv.textContent = data.answer;

        } catch (error) {
            answerDiv.textContent = `Error: ${error.message}`;
        } finally {
            queryBtn.disabled = false;
        }
    });
   
    stopBtn.addEventListener("click", async () => {
    if (!sessionId) {
        alert("No active session to stop.");
        return;
    }

    try {
        await fetch(`${API_URL}/stop-session`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: sessionId }),
        });

        alert("Session has been stopped. You can now process a new video.");
        
        // Reset the UI to its initial state
        querySection.style.display = "none";
        resultsSection.style.display = "none";
        statusContainer.style.display = "none";
        sessionId = null;

    } catch (error) {
        console.error("Failed to stop session:", error);
        alert("Could not stop the session. Please check the console.");
    }
});
});
