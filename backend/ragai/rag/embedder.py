from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Optional

# Initialize the model once at module level
model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_text(text: str) -> Optional[np.ndarray]:
    """
    Generate embeddings for a single text using sentence-transformers.
    
    Args:
        text (str): Text to embed
        
    Returns:
        Optional[np.ndarray]: Embedding vector or None if generation fails
    """
    try:
        # Generate embedding and ensure it's float32
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.astype('float32')
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def embed_chunks(chunks: List[str]) -> Optional[np.ndarray]:
    """
    Generate embeddings for multiple text chunks efficiently.
    
    Args:
        chunks (List[str]): List of text chunks to embed
        
    Returns:
        Optional[np.ndarray]: Array of embedding vectors or None if generation fails
    """
    try:
        if not chunks:
            return None
        # Batch encode all chunks at once - much more efficient
        embeddings = model.encode(chunks, convert_to_numpy=True)
        return embeddings.astype('float32')
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        # Fallback to individual processing
        results = []
        for chunk in chunks:
            embedding = embed_text(chunk)
            if embedding is not None:
                results.append(embedding)
        return np.array(results).astype('float32') if results else None 