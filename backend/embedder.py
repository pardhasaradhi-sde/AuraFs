import numpy as np

# Lazy-load the model to avoid slow transformers import at startup
_model = None

# Model's max token limit is ~256 word pieces, so we chunk at ~500 chars
CHUNK_SIZE = 500  # characters per chunk
MAX_CHUNKS = 20   # max chunks to process per file (covers ~10,000 chars)


def _get_model():
    """Lazy-load the SentenceTransformer model on first use."""
    global _model
    if _model is None:
        print("[EMBEDDER] Loading embedding model...")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        print("[EMBEDDER] Model loaded ✓")
    return _model


def embed_text(text: str) -> np.ndarray:
    """
    Convert text into a 384-dimensional embedding vector.
    
    For short texts: embeds directly.
    For long texts: splits into chunks, embeds each, then averages.
    This ensures the full document's meaning is captured without exceeding
    the model's token limit.
    """
    if not text or not text.strip():
        return np.zeros(384)
    
    text = text.strip()
    model = _get_model()
    
    # Short text — embed directly
    if len(text) <= CHUNK_SIZE:
        return model.encode(text, convert_to_numpy=True)
    
    # Long text — chunk and average
    chunks = _split_into_chunks(text)
    
    if not chunks:
        return np.zeros(384)
    
    # Embed all chunks at once (batch processing — much faster)
    chunk_embeddings = model.encode(chunks, convert_to_numpy=True, batch_size=8)
    
    # Weighted average: give more weight to earlier chunks (intro/abstract matters more)
    weights = np.array([1.0 / (1 + 0.1 * i) for i in range(len(chunk_embeddings))])
    weights /= weights.sum()  # normalize
    
    # Weighted average embedding
    avg_embedding = np.average(chunk_embeddings, axis=0, weights=weights)
    
    # Normalize to unit vector (cosine similarity works better with normalized vectors)
    norm = np.linalg.norm(avg_embedding)
    if norm > 0:
        avg_embedding /= norm
    
    return avg_embedding


def _split_into_chunks(text: str) -> list[str]:
    """
    Split text into semantic chunks, trying to break at sentence boundaries.
    Returns at most MAX_CHUNKS chunks.
    """
    # Try to split at sentence boundaries first
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= CHUNK_SIZE:
            current_chunk += " " + sentence if current_chunk else sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            # If a single sentence is too long, split it further
            if len(sentence) > CHUNK_SIZE:
                words = sentence.split()
                current_chunk = ""
                for word in words:
                    if len(current_chunk) + len(word) + 1 <= CHUNK_SIZE:
                        current_chunk += " " + word if current_chunk else word
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = word
            else:
                current_chunk = sentence
        
        if len(chunks) >= MAX_CHUNKS:
            break
    
    # Don't forget the last chunk
    if current_chunk and len(chunks) < MAX_CHUNKS:
        chunks.append(current_chunk.strip())
    
    # Filter out tiny chunks
    chunks = [c for c in chunks if len(c) > 20]
    
    return chunks[:MAX_CHUNKS]
