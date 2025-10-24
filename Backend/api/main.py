import uvicorn
import uuid
import time
import os
import shutil
import traceback
from threading import Thread
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from dotenv import load_dotenv
import clip

# --- LlamaIndex Import ---
from llama_index.core.node_parser import SentenceSplitter
from src.embedding import clip_tokenizer, generate_text_embedding, generate_image_embedding

# --- Local Imports ---
from .models import VideoRequest, QueryRequest, SessionRequest
from src import video_processor, transcriber, rag

# Load environment variables
load_dotenv()

# --- App Setup ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-memory Stores ---
jobs = {}
session_dbs = {}
SESSION_TIMEOUT_SECONDS = 1800  # 30 minutes

# --- Sessions Folder ---
SESSIONS_DIR = os.path.join(os.getcwd(), "sessions_data")
os.makedirs(SESSIONS_DIR, exist_ok=True)

# --- Serve Frontend ---
app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")
templates = Jinja2Templates(directory="../frontend/templates")

@app.get("/")
async def serve_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- Automatic session cleanup ---
def session_cleaner():
    while True:
        now = time.time()
        expired = [sid for sid, v in session_dbs.items() if now - v['timestamp'] > SESSION_TIMEOUT_SECONDS]
        for sid in expired:
            folder = session_dbs[sid]['folder']
            try:
                if os.path.exists(folder):
                    shutil.rmtree(folder, ignore_errors=True)
            except:
                pass
            del session_dbs[sid]
            print(f"[Cleaner] Session {sid} expired and removed.")
        time.sleep(60)

Thread(target=session_cleaner, daemon=True).start()

# --- Background Worker ---
def process_video_worker(url: str, job_id: str):
    session_id = str(uuid.uuid4())
    session_folder = os.path.join(SESSIONS_DIR, session_id)
    os.makedirs(session_folder, exist_ok=True)

    video_file = os.path.join(session_folder, f"{uuid.uuid4()}.mp4")
    audio_file = os.path.join(session_folder, f"{uuid.uuid4()}.wav")
    frames_dir = os.path.join(session_folder, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    try:
        # 1. Download Video
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["message"] = "Downloading video..."
        downloaded_path = video_processor.download_video(url, session_folder)

        # Move downloaded video to our session file path
        shutil.move(downloaded_path, video_file)

        # Small delay for Windows FS
        time.sleep(0.5)

        # 2. Extract Audio & Frames
        jobs[job_id]["message"] = "Extracting audio and frames..."
        video_processor.extract_audio(video_file, audio_file)
        frame_files = video_processor.extract_frames(video_file, frames_dir)

        # 3. Transcribe Audio
        jobs[job_id]["message"] = "Transcribing audio..."
        transcript = transcriber.transcribe_audio(audio_file)

        # 4. Generate embeddings
        jobs[job_id]["message"] = "Generating embeddings..."
        import lancedb
        # Use session folder for DB
        db_folder = os.path.join(session_folder, "lancedb")
        os.makedirs(db_folder, exist_ok=True)
        db = lancedb.connect(db_folder)

        data = []
        text_splitter = SentenceSplitter(
            chunk_size=70,
            chunk_overlap=10,
            tokenizer=clip_tokenizer
        )
        text_chunks = text_splitter.split_text(transcript)

        for chunk in text_chunks:
            data.append({"vector": generate_text_embedding(chunk), "text": chunk, "type": "text"})

        for frame in frame_files:
            data.append({
                "vector": generate_image_embedding(frame),
                "text": os.path.basename(frame),
                "type": "image"
            })

        table = db.create_table(f"session_{session_id}", data=data)

        session_dbs[session_id] = {"table": table, "timestamp": time.time(), "folder": session_folder}

        # 5. Mark job complete
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = session_id
        jobs[job_id]["message"] = "Ready to answer questions!"

    except Exception as e:
        print("--- BACKGROUND TASK FAILED ---")
        traceback.print_exc()
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = str(e)

# --- API Endpoints ---
@app.post("/process-video-async")
async def process_video_async(request: VideoRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "pending", "message": "Job accepted"}
    background_tasks.add_task(process_video_worker, request.url, job_id)
    return {"job_id": job_id}

@app.get("/job-status/{job_id}")
async def get_job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.post("/stop-session")
async def stop_session(request: SessionRequest):
    session_id = request.session_id
    if session_id in session_dbs:
        folder = session_dbs[session_id]['folder']
        try:
            if os.path.exists(folder):
                shutil.rmtree(folder, ignore_errors=True)
        except:
            pass
        del session_dbs[session_id]
        print(f"Successfully stopped session: {session_id}")
        return {"message": f"Session {session_id} stopped successfully."}
    else:
        return {"message": "Session not found or already stopped."}

@app.post("/query")
async def handle_query(request: QueryRequest):
    session_id = request.session_id
    if session_id not in session_dbs:
        raise HTTPException(status_code=404, detail="Session expired or not found")

    # Keep session alive
    session_dbs[session_id]['timestamp'] = time.time()

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured.")

    result = rag.retrieve_and_answer(
        session_id=session_id,
        query=request.query,
        api_key=api_key
    )
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
