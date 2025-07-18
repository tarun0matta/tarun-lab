from sentence_transformers import SentenceTransformer
import numpy as np

# Initialize the model once at module level
model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_text(text):
    try:
        # Handle single text input
        if isinstance(text, str):
            # Convert to embedding and ensure it's float32
            embedding = model.encode(text, convert_to_numpy=True)
            return embedding.astype('float32')
        return None
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def embed_chunks(chunks):
    try:
        if not chunks:
            return None
        # Batch encode all chunks at once - much faster
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