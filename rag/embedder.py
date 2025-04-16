# rag/embedder.py
from sentence_transformers import SentenceTransformer
import numpy as np

class Embedder:
    def __init__(self, model_name="all-MiniLM-L6-v2"):   # "all-mpnet-base-v2"
        self.model = SentenceTransformer(model_name)

    def embed(self, texts):
        """
        Embed a list of texts into vectors.
        Args:
            texts (list of str): Texts to embed.
        Returns:
            numpy.ndarray: Embeddings.
        """
        if isinstance(texts, str):
            texts = [texts]
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings