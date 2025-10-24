📺 TubeTalker

Chat with any YouTube video instantly. Ask questions, get summaries, and find key moments just by talking to the video.

TubeTalker is an AI-powered API that ingests a YouTube video, transcribes its audio, samples its visual frames, and uses a multi-modal Retrieval-Augmented Generation (RAG) pipeline to allow you to have a conversation with it.

🚀 Core Features

YouTube Video Processing: Simply provide a YouTube URL to ingest the video's content.

AI-Powered Transcription: Uses Whisper to generate highly-accurate, timestamped transcripts from the video's audio.

Deep Content Analysis: Uses the CLIP multi-modal embedding model to understand both the transcribed text and the visual frames from the video.

Conversational AI Chat: Ask questions in natural language (e.g., "Show me the part where they talk about AI safety") and get direct, context-aware answers that can reference both text and images.

FastAPI Backend: Built as a high-performance, asynchronous API, ready to be integrated with any frontend (Streamlit, React, etc.).

⚙️ How It Works (Multi-Modal RAG)

TubeTalker employs a modern multi-modal RAG (Retrieval-Augmented Generation) pipeline:

Ingestion: A user submits a YouTube URL to the /process-video endpoint.

Download, Sample & Transcribe: The backend server downloads the video using pytube, samples key visual frames (e.g., one per second), and uses Whisper to generate a high-quality transcript from the audio.

Chunking: The transcript is cleaned and split into small, logical chunks of text, aligned with their timestamps.

Multi-Modal Embedding: Each text chunk and each visual frame is passed through the CLIP embedding model to create a vector representation of its meaning.

Vector Storage: These text and image vectors are stored in a LanceDB vector database. LanceDB is optimized for multi-modal data and fast, efficient retrieval.

Chat (RAG):

A user sends a question (e.g., "What did the speaker say about AI?") to the /chat endpoint.

The question is vectorized using the same CLIP model.

A similarity search is performed on the LanceDB database to find the most relevant data (which can be a mix of text chunks and image frames).

This relevant context (text and references to images), along with the user's question, are inserted into a prompt.

The prompt is sent to a powerful LLM (like Google's Gemini) which generates a final, human-readable answer based on the retrieved context.

🛠️ Getting Started

Follow these steps to get the backend server running on your local machine.

1. Prerequisites

Python 3.10+

Git

A Google Gemini API Key

An OpenAI API Key (for Whisper)

2. Clone the Repository

git clone [https://github.com/YourUsername/TubeTalker.git](https://github.com/YourUsername/TubeTalker.git)
cd TubeTalker


3. Set Up a Virtual Environment

It is highly recommended to use a virtual environment.

# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate


4. Install Dependencies

Install all the required Python packages.

pip install -r requirements.txt


5. Configure Environment Variables

Create a file named .env in the root of the project directory. This file will securely store your API keys.

# .env
GOOGLE_API_KEY="your_secret_gemini_api_key_here"
OPENAI_API_KEY="your_secret_openai_api_key_for_whisper_here"


IMPORTANT: Add .env to your .gitignore file to ensure you never commit your secret keys to GitHub.

6. Run the API Server

Use uvicorn to run the FastAPI server. The --reload flag will automatically restart the server when you make code changes.

uvicorn api.main:app --reload


Your API is now running and accessible at http://127.0.0.1:8000.

📖 How to Use (API Endpoints)

The easiest way to test the API is by using the built-in FastAPI documentation.

Go to: http://127.0.0.1:8000/docs

You will see a "Swagger UI" page where you can test the endpoints live from your browser.

Key Endpoints

1. Process a Video

Endpoint: POST /process-video

Description: Ingests, transcribes, and embeds a new YouTube video.

Request Body:

{
  "video_url": "[https://www.youtube.com/watch?v=dQw4w9WgXcQ](https://www.youtube.com/watch?v=dQw4w9WgXcQ)"
}


Response: A message indicating the video has been processed successfully.

2. Chat with the Video

Endpoint: POST /chat

Description: Ask a question about the most recently processed video.

Request Body:

{
  "query": "What is the main topic of this video?"
}


Response: An AI-generated answer.

{
  "answer": "The main topic of this video is a discussion about the artist's feelings and a declaration that they are 'no stranger to love'..."
}


🔬 Tech Stack

Backend: FastAPI

Server: Uvicorn

Generative AI: Google Gemini

AI Frameworks: LangChain (principles)

Video Downloader: Pytube

Transcription: OpenAI Whisper

Vector Database: LanceDB

Embeddings: OpenAI CLIP

Created by Krish Raghuwanshi