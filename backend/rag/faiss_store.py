import faiss
import numpy as np
import json

def store_embeddings(embeddings, path="index/faiss_index.index"):
    # Convert to numpy array if not already
    matrix = np.array(embeddings).astype("float32")
    # Create index with the correct dimension
    dimension = matrix.shape[1]  # Get embedding dimension
    index = faiss.IndexFlatL2(dimension)
    index.add(matrix)
    faiss.write_index(index, path)

def save_chunks(chunks, path="index/chunks.json"):
    with open(path, "w") as f:
        json.dump(chunks, f)

def load_index_and_chunks(index_path="index/faiss_index.index", chunks_path="index/chunks.json"):
    index = faiss.read_index(index_path)
    with open(chunks_path) as f:
        chunks = json.load(f)
    return index, chunks

def search(index, vector, k=3):
    # Ensure vector is 2D array
    if len(vector.shape) == 1:
        vector = vector.reshape(1, -1)
    vector = vector.astype("float32")
    
    # Perform search
    D, I = index.search(vector, k)
    return I[0]  # Return just the indices 