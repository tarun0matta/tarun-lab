import faiss
import numpy as np
import json
from typing import List, Tuple, Optional

def store_embeddings(embeddings: np.ndarray, index_path: str) -> bool:
    """
    Store embeddings in a FAISS index.
    
    Args:
        embeddings (np.ndarray): Array of embedding vectors
        index_path (str): Path to save the FAISS index
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create index with the correct dimension
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        
        # Add embeddings to index
        index.add(embeddings.astype('float32'))
        
        # Save index to file
        faiss.write_index(index, index_path)
        return True
    except Exception as e:
        print(f"Error storing embeddings: {e}")
        return False

def save_chunks(chunks: List[str], chunks_path: str) -> bool:
    """
    Save text chunks to a JSON file.
    
    Args:
        chunks (List[str]): List of text chunks
        chunks_path (str): Path to save the chunks
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(chunks_path, 'w') as f:
            json.dump(chunks, f)
        return True
    except Exception as e:
        print(f"Error saving chunks: {e}")
        return False

def load_index_and_chunks(index_path: str, chunks_path: str) -> Tuple[Optional[faiss.Index], Optional[List[str]]]:
    """
    Load FAISS index and text chunks.
    
    Args:
        index_path (str): Path to the FAISS index
        chunks_path (str): Path to the chunks file
        
    Returns:
        Tuple[Optional[faiss.Index], Optional[List[str]]]: Loaded index and chunks
    """
    try:
        # Load FAISS index
        index = faiss.read_index(index_path)
        
        # Load chunks
        with open(chunks_path, 'r') as f:
            chunks = json.load(f)
            
        return index, chunks
    except Exception as e:
        print(f"Error loading index and chunks: {e}")
        return None, None

def search(index: faiss.Index, query_vector: np.ndarray, k: int = 3) -> Optional[List[int]]:
    """
    Search for similar vectors in the FAISS index.
    
    Args:
        index (faiss.Index): FAISS index to search
        query_vector (np.ndarray): Query vector
        k (int): Number of results to return
        
    Returns:
        Optional[List[int]]: Indices of similar vectors or None if search fails
    """
    try:
        # Reshape query vector if needed
        if len(query_vector.shape) == 1:
            query_vector = query_vector.reshape(1, -1)
            
        # Convert to float32
        query_vector = query_vector.astype('float32')
        
        # Search the index
        D, I = index.search(query_vector, k)
        return I[0].tolist()  # Return indices of nearest neighbors
    except Exception as e:
        print(f"Error searching index: {e}")
        return None 