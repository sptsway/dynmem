"""Local text embeddings with mxbai-embed-large-v1 (MPS, CPU fallback)."""
from __future__ import annotations

import numpy as np

MODEL_ID = "mixedbread-ai/mxbai-embed-large-v1"
QUERY_PROMPT = "Represent this sentence for searching relevant passages: "


class Embedder:
    def __init__(self, model_id: str = MODEL_ID, device: str | None = None):
        import torch
        from sentence_transformers import SentenceTransformer

        torch.manual_seed(0)
        if device is None:
            device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.model = SentenceTransformer(model_id, device=device)
        self.model_id, self.device = model_id, device
        self.dim = self.model.get_embedding_dimension()

    def embed_docs(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        return self.model.encode(texts, batch_size=batch_size, normalize_embeddings=True,
                                 convert_to_numpy=True, show_progress_bar=False)

    def embed_query(self, text: str) -> np.ndarray:
        return self.model.encode(QUERY_PROMPT + text, normalize_embeddings=True,
                                 convert_to_numpy=True, show_progress_bar=False)
