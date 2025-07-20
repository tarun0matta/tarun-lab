import tiktoken
from typing import List

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks using tiktoken for token counting.
    
    Args:
        text (str): Text to split into chunks
        chunk_size (int): Maximum number of tokens per chunk
        overlap (int): Number of tokens to overlap between chunks
        
    Returns:
        List[str]: List of text chunks
    """
    if not text:
        return []

    try:
        # Get the encoding
        enc = tiktoken.get_encoding("cl100k_base")  # Using OpenAI's encoding
        
        # Encode the text into tokens
        tokens = enc.encode(text)
        chunks = []
        start = 0
        
        while start < len(tokens):
            # Get the chunk's end position
            end = start + chunk_size
            
            # If this is not the last chunk, try to find a good break point
            if end < len(tokens):
                # Look for a period or newline in the overlap region
                overlap_start = max(start, end - overlap)
                decoded_overlap = enc.decode(tokens[overlap_start:end])
                
                # Try to find a good break point
                break_point = decoded_overlap.rfind(". ")
                if break_point == -1:
                    break_point = decoded_overlap.rfind("\n")
                
                if break_point != -1:
                    # Adjust end to the break point
                    end = overlap_start + break_point + 2  # +2 to include the period and space
            
            # Decode the chunk and add it to the list
            chunk = enc.decode(tokens[start:end]).strip()
            if chunk:
                chunks.append(chunk)
            
            # Move the start pointer, accounting for overlap
            start = max(start + chunk_size - overlap, end - overlap)
        
        return chunks
    except Exception as e:
        print(f"Error chunking text: {e}")
        # Fallback to simple character-based chunking
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size-overlap)] 