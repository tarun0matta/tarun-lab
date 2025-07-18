from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import google.generativeai as genai
import os
import uuid
import shutil
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path

# Import RAG components
from rag.pdf_loader import pdf_to_text
from rag.chunker import chunk_text
from rag.embedder import embed_text, embed_chunks
from rag.faiss_store import store_embeddings, save_chunks, load_index_and_chunks, search
from rag.gemini import generate_answer

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create temp directory structure
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

class SessionManager:
    @staticmethod
    def create_session():
        session_id = str(uuid.uuid4())
        session_dir = TEMP_DIR / session_id
        session_dir.mkdir(exist_ok=True)
        (session_dir / "files").mkdir(exist_ok=True)
        (session_dir / "chunks").mkdir(exist_ok=True)
        (session_dir / "indices").mkdir(exist_ok=True)
        
        # Create and update session file with timestamp
        session_file = session_dir / "session.json"
        session_data = {
            "created_at": datetime.now().isoformat(),
            "last_access": datetime.now().isoformat()
        }
        with open(session_file, "w") as f:
            json.dump(session_data, f)
            
        return session_id

    @staticmethod
    def update_session_access(session_id: str) -> bool:
        try:
            session_dir = TEMP_DIR / session_id
            session_file = session_dir / "session.json"
            
            if not session_file.exists():
                return False
                
            # Read existing data
            with open(session_file, "r") as f:
                session_data = json.load(f)
                
            # Update last access
            session_data["last_access"] = datetime.now().isoformat()
            
            # Write back
            with open(session_file, "w") as f:
                json.dump(session_data, f)
                
            return True
        except Exception as e:
            print(f"Error updating session access: {e}")
            return False

    @staticmethod
    def is_session_valid(session_id: str) -> bool:
        try:
            if not session_id:
                print("No session ID provided")
                return False
            
            session_dir = TEMP_DIR / session_id
            session_file = session_dir / "session.json"
            
            if not session_file.exists():
                print(f"Session file not found for {session_id}")
                return False
                
            # Read session data
            with open(session_file, "r") as f:
                session_data = json.load(f)
                
            last_access = datetime.fromisoformat(session_data["last_access"])
            
            # Check if session has expired (1 hour timeout)
            if datetime.now() - last_access > timedelta(hours=1):
                print(f"Session {session_id} has expired")
                SessionManager.cleanup_session(session_id)
                return False
            
            return True
        except Exception as e:
            print(f"Error validating session: {e}")
            return False

    @staticmethod
    def get_session_dir(session_id: str) -> Path:
        session_dir = TEMP_DIR / session_id
        if SessionManager.update_session_access(session_id):
            return session_dir
        raise ValueError("Invalid or expired session")

    @staticmethod
    def cleanup_session(session_id: str):
        try:
            session_dir = TEMP_DIR / session_id
            if session_dir.exists():
                shutil.rmtree(session_dir)
                print(f"Cleaned up session {session_id}")
        except Exception as e:
            print(f"Error cleaning up session: {e}")

    @staticmethod
    async def cleanup_old_sessions():
        try:
            for session_dir in TEMP_DIR.iterdir():
                session_file = session_dir / "session.json"
                if not session_file.exists():
                    shutil.rmtree(session_dir)
                    continue
                    
                with open(session_file, "r") as f:
                    session_data = json.load(f)
                    
                last_access = datetime.fromisoformat(session_data["last_access"])
                if datetime.now() - last_access > timedelta(hours=1):
                    shutil.rmtree(session_dir)
        except Exception as e:
            print(f"Error in cleanup_old_sessions: {e}")

class FileManager:
    @staticmethod
    async def save_upload(file: UploadFile, session_id: str) -> str:
        file_id = str(uuid.uuid4())
        file_path = TEMP_DIR / session_id / "files" / f"{file_id}.pdf"
        
        try:
            with file_path.open("wb") as f:
                shutil.copyfileobj(file.file, f)
        finally:
            file.file.close()
            
        return file_id, str(file_path)

    @staticmethod
    async def process_pdf(file_path: str, file_id: str, session_id: str):
        try:
            # Extract text from PDF
            text = pdf_to_text(file_path)
            if not text:
                raise ValueError("Failed to extract text from PDF")
            
            # Split into chunks
            chunks = chunk_text(text)
            if not chunks:
                raise ValueError("Failed to create text chunks")
            
            # Generate embeddings
            embeddings = embed_chunks(chunks)
            if embeddings is None:
                raise ValueError("Failed to generate embeddings")
            
            # Save embeddings and chunks
            index_path = TEMP_DIR / session_id / "indices" / f"{file_id}.index"
            chunks_path = TEMP_DIR / session_id / "chunks" / f"{file_id}.json"
            
            store_embeddings(embeddings, str(index_path))
            save_chunks(chunks, str(chunks_path))
            
            return len(chunks)
        except Exception as e:
            print(f"Error processing PDF: {e}")
            raise

class Message(BaseModel):
    role: str
    content: str

class RAGQueryRequest(BaseModel):
    message: str
    session_id: str
    file_id: str
    history: Optional[List[Message]] = []

@app.post("/api/rag/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = None,
    background_tasks: BackgroundTasks = None
):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        # Create new session if none exists or if existing session is invalid
        if not session_id or not SessionManager.is_session_valid(session_id):
            session_id = SessionManager.create_session()
            print(f"Created new session: {session_id}")
        else:
            print(f"Using existing session: {session_id}")
            SessionManager.update_session_access(session_id)

        # Save file
        file_id, file_path = await FileManager.save_upload(file, session_id)
        print(f"Saved file {file_id} in session {session_id}")
        
        # Process PDF
        await FileManager.process_pdf(file_path, file_id, session_id)
        print(f"Processed file {file_id}")
        
        # Don't schedule immediate cleanup - let the session expire naturally
        # or be cleaned up by the periodic task
        
        return {
            "status": "success",
            "session_id": session_id,
            "file_id": file_id,
            "message": "File processed successfully"
        }
    except Exception as e:
        print(f"Error in upload_file: {e}")
        # Cleanup on error only
        if session_id:
            SessionManager.cleanup_session(session_id)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag/query")
async def query_document(request: RAGQueryRequest):
    async def error_stream(error_msg: str):
        yield f"Error: {error_msg}"

    try:
        print(f"Processing query for session {request.session_id}, file {request.file_id}")
        
        # Validate and update session
        if not SessionManager.is_session_valid(request.session_id):
            print(f"Session {request.session_id} is invalid or expired")
            return StreamingResponse(error_stream("Session expired or invalid"))
            
        SessionManager.update_session_access(request.session_id)
        
        session_dir = TEMP_DIR / request.session_id
        
        # Load index and chunks
        index_path = session_dir / "indices" / f"{request.file_id}.index"
        chunks_path = session_dir / "chunks" / f"{request.file_id}.json"
        
        if not index_path.exists() or not chunks_path.exists():
            print(f"Files not found: index_path={index_path.exists()}, chunks_path={chunks_path.exists()}")
            return StreamingResponse(error_stream("File not found or processing incomplete"))

        print("Loading index and chunks...")
        index, chunks = load_index_and_chunks(str(index_path), str(chunks_path))
        
        # Generate embedding for question
        print("Generating query embedding...")
        query_embedding = embed_text(request.message)
        if query_embedding is None:
            return StreamingResponse(error_stream("Failed to generate query embedding"))
            
        # Get relevant chunks
        print("Searching for relevant chunks...")
        relevant_indices = search(index, query_embedding)
        if relevant_indices is None or len(relevant_indices) == 0:
            return StreamingResponse(error_stream("No relevant content found"))
            
        context = "\n\n".join([chunks[i] for i in relevant_indices])
        
        # Generate answer
        print("Generating answer...")
        response = generate_answer(context, request.message, stream=True)
        if response is None:
            return StreamingResponse(error_stream("Failed to generate answer"))

        async def generate():
            try:
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
            except Exception as e:
                print(f"Error in generate: {e}")
                yield f"\nError during response generation: {str(e)}"

        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        print(f"Error processing query: {e}")
        return StreamingResponse(error_stream(str(e)))

@app.delete("/api/rag/cleanup/{session_id}")
async def cleanup_session(session_id: str):
    SessionManager.cleanup_session(session_id)
    return {"status": "success"}

@app.on_event("startup")
async def startup_event():
    # Create temp directory if it doesn't exist
    TEMP_DIR.mkdir(exist_ok=True)
    # Start periodic cleanup task
    asyncio.create_task(periodic_cleanup())

async def periodic_cleanup():
    while True:
        try:
            print("Running periodic cleanup...")
            await SessionManager.cleanup_old_sessions()
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            print(f"Error in periodic cleanup: {e}")
            await asyncio.sleep(60)  # Wait a minute before retrying on error

# Existing chat endpoint
class ChatRequest(BaseModel):
    message: str
    history: List[Message]

@app.post("/api/chat")
async def chat(req: ChatRequest):
    async def error_stream(error_msg: str):
        yield f"Error: {error_msg}"

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Instead of rebuilding chat history, send context with the current message
        context = ""
        # Only use last 4 message pairs to keep context focused and reduce latency
        relevant_history = req.history[-8:] if len(req.history) > 8 else req.history
        
        if relevant_history:
            context = "Previous conversation:\n"
            for msg in relevant_history:
                prefix = "User: " if msg.role == "user" else "Assistant: "
                context += f"{prefix}{msg.content}\n"
            context += "\nCurrent conversation:\n"
        
        # Combine context with current message
        full_prompt = f"{context}User: {req.message}\nAssistant:"
        
        # Generate response with the combined prompt
        response = model.generate_content(full_prompt, stream=True)

        def gemini_stream():
            for chunk in response:
                if chunk.text:
                    yield chunk.text

        return StreamingResponse(gemini_stream(), media_type="text/plain")
    except Exception as e:
        return StreamingResponse(error_stream(str(e)), media_type="text/plain")