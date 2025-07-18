import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Get API key
API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure Gemini API - do this once at module level
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("Warning: GOOGLE_API_KEY not found in environment")

def generate_answer(context, question, stream=False, model="gemini-2.5-flash"):
    if not API_KEY:
        return "Error: GOOGLE_API_KEY not found in environment. Please set up your API key."

    try:
        # Initialize the generative model
        model_instance = genai.GenerativeModel(model)
        
        # Create the prompt with context and question
        prompt = f"""You are a helpful assistant. Use the provided context to answer questions accurately.
        If the context doesn't contain enough information to answer the question, say so.
        Don't make up information that's not in the context.

Context:
{context}

Question: {question}"""

        # Generate response
        response = model_instance.generate_content(prompt, stream=stream)
        
        if stream:
            return response
        elif response.text:
            return response.text.strip()
        else:
            return "Error: No response generated."
            
    except Exception as e:
        print("❌ Gemini API request failed:", e)
        return f"Error: Could not reach Gemini API. Details: {str(e)}" 