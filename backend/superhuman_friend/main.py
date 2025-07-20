from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import google.generativeai as genai
from typing import List
from dotenv import load_dotenv
import os

# Load environment variables
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

class Message(BaseModel):
    role: str
    content: str

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