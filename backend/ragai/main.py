from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import google.generativeai as genai
import os
import uuid
import shutil
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import json
from pathlib import Path

# Import RAG components
from rag.pdf_loader import pdf_to_text
from rag.chunker import chunk_text
from rag.embedder import embed_text, embed_chunks
from rag.faiss_store import store_embeddings, save_chunks, load_index_and_chunks, search

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure Google API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")
genai.configure(api_key=GOOGLE_API_KEY)

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

# Store conversation history
CONVERSATIONS: Dict[str, List[dict]] = {}

class Message(BaseModel):
    role: str
    content: str

class RAGQueryRequest(BaseModel):
    message: str
    session_id: str
    file_id: str
    history: Optional[List[Message]] = []

def cleanup_old_files():
    """Clean up files older than 1 hour"""
    try:
        current_time = datetime.now()
        for item in TEMP_DIR.glob("*"):
            if item.is_dir():
                # Check if directory is older than 1 hour
                if current_time - datetime.fromtimestamp(item.stat().st_mtime) > timedelta(hours=1):
                    shutil.rmtree(item)
                    # Clean up conversation history
                    if str(item.name) in CONVERSATIONS:
                        del CONVERSATIONS[str(item.name)]
    except Exception as e:
        print(f"Error cleaning up old files: {e}")

def get_enhanced_query(original_query: str, conversation_history: List[dict]) -> str:
    """
    Enhance the query with conversation context.
    """
    if not conversation_history:
        return original_query

    # Create a context-aware query
    recent_messages = conversation_history[-4:]  # Last 4 messages
    context = "\n".join([
        f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
        for msg in recent_messages
    ])
    
    # Handle generic "explain" requests more intelligently
    lower_query = original_query.lower()
    if any(phrase in lower_query for phrase in ["explain it", "tell me more", "elaborate", "explain this"]):
        # Look for the most recent topic in conversation
        for msg in reversed(conversation_history[:-1]):  # Exclude current message
            if msg['role'] == 'assistant' and len(msg['content']) > 50:  # Substantial response
                return f"Explain in detail the following topic from the document: {msg['content'][:200]}..."
    
    enhanced_query = f"""
    Recent conversation context:
    {context}

    Current request: {original_query}

    Based on this conversation context and the current request, provide information about:
    {original_query}
    """
    
    return enhanced_query

@app.post("/api/rag/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Handle PDF upload, text extraction, chunking, and embedding generation.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    try:
        # Create session directory
        session_id = str(uuid.uuid4())
        session_dir = TEMP_DIR / session_id
        session_dir.mkdir(parents=True)
        
        # Initialize conversation history
        CONVERSATIONS[session_id] = []
        
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_path = session_dir / f"{file_id}.pdf"
        
        try:
            with file_path.open("wb") as f:
                shutil.copyfileobj(file.file, f)
        finally:
            file.file.close()

        # Extract text from PDF
        text = pdf_to_text(str(file_path))
        if not text:
            raise ValueError("Failed to extract text from PDF")

        # Create chunks
        chunks = chunk_text(text)
        if not chunks:
            raise ValueError("Failed to create text chunks")

        # Generate embeddings
        embeddings = embed_chunks(chunks)
        if embeddings is None:
            raise ValueError("Failed to generate embeddings")

        # Save embeddings and chunks
        index_path = session_dir / "index.faiss"
        chunks_path = session_dir / "chunks.json"
        
        if not store_embeddings(embeddings, str(index_path)):
            raise ValueError("Failed to store embeddings")
        
        if not save_chunks(chunks, str(chunks_path)):
            raise ValueError("Failed to save chunks")

        return {
            "status": "success",
            "session_id": session_id,
            "file_id": file_id,
            "message": "File processed successfully"
        }

    except Exception as e:
        # Clean up on error
        if 'session_dir' in locals() and session_dir.exists():
            shutil.rmtree(session_dir)
        if 'session_id' in locals() and session_id in CONVERSATIONS:
            del CONVERSATIONS[session_id]
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag/query")
async def query_document(request: RAGQueryRequest):
    """
    Process queries using RAG approach with conversation history.
    """
    async def error_stream(error_msg: str):
        yield f"Error: {error_msg}"

    try:
        session_dir = TEMP_DIR / request.session_id
        if not session_dir.exists():
            return StreamingResponse(error_stream("Session not found"))

        # Initialize conversation history if not exists
        if request.session_id not in CONVERSATIONS:
            CONVERSATIONS[request.session_id] = []

        # Get conversation history
        conversation = CONVERSATIONS[request.session_id]
        
        # Format conversation context
        conversation_context = "\n".join([
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
            for msg in conversation[-4:] if msg['content'].strip()  # Last 4 non-empty messages
        ])

        # Load index and chunks
        index_path = session_dir / "index.faiss"
        chunks_path = session_dir / "chunks.json"
        
        if not index_path.exists() or not chunks_path.exists():
            return StreamingResponse(error_stream("Session data not found"))

        # Load index and chunks
        index, chunks = load_index_and_chunks(str(index_path), str(chunks_path))
        if index is None or chunks is None:
            return StreamingResponse(error_stream("Failed to load session data"))

        # Generate embedding for enhanced query
        enhanced_query = get_enhanced_query(request.message, conversation)
        query_embedding = embed_text(enhanced_query)
        if query_embedding is None:
            return StreamingResponse(error_stream("Failed to process query"))

        # Search for relevant chunks
        relevant_indices = search(index, query_embedding, k=5)  # Increased k for more context
        if not relevant_indices:
            return StreamingResponse(error_stream("No relevant content found"))

        # Get relevant chunks
        context = "\n\n".join([chunks[i] for i in relevant_indices])

        # Add user message to conversation
        conversation.append({"role": "user", "content": request.message})

        # Prepare prompt for Gemini
        prompt = f"""You are an intelligent assistant helping with document understanding. Based on the following context and conversation history, provide a detailed and helpful response.

        If the user asks to explain something in detail:
        1. If it's clear what they're referring to, provide a comprehensive explanation
        2. If it's ambiguous, explain the most recently discussed topic in detail
        3. Only ask for clarification if there are multiple possible topics and no recent context

        Context from document:
        {context}

        Current request: {request.message}

        Previous conversation:
        {conversation_context}

        Instructions:
        1. If the request is clear, provide a detailed response using the context
        2. If the request is for more detail about a previous topic, expand on that topic
        3. If the request is truly ambiguous (multiple possible topics with no clear recent context), politely ask for clarification
        4. Always provide specific information from the document rather than generic responses
        5. If information cannot be found in the context, say "I cannot find specific information about this in the document."

        Please provide a detailed and accurate response:"""

        # Generate response with Gemini
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt, stream=True)

        async def generate():
            full_response = ""
            try:
                for chunk in response:
                    if chunk.text:
                        full_response += chunk.text
                        yield chunk.text
                # Add assistant response to conversation history
                conversation.append({"role": "assistant", "content": full_response})
            except Exception as e:
                error_msg = f"\nError during response generation: {str(e)}"
                yield error_msg
                conversation.append({"role": "assistant", "content": error_msg})

        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        return StreamingResponse(error_stream(str(e)))

@app.delete("/api/rag/cleanup/{session_id}")
async def cleanup_session(session_id: str):
    """
    Clean up session files and conversation history.
    """
    try:
        session_dir = TEMP_DIR / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir)
        if session_id in CONVERSATIONS:
            del CONVERSATIONS[session_id]
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Clean up old files on startup
@app.on_event("startup")
async def startup_event():
    cleanup_old_files() 