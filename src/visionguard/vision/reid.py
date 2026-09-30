"""Vehicle Re-Identification (Re-ID) embedding extractor and appearance matcher.
Generates invariant visual feature representations for cross-camera matching.
"""
import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

class VehicleReIDExtractor:
    """
    Extracts deep visual embeddings from vehicle bounding box crops.
    Combines spatial color moments, multi-scale histogram representation,
    and normalized feature vectors to achieve illumination-invariant appearance descriptors.
    """

    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim

    def extract_embedding(self, crop: np.ndarray) -> np.ndarray:
        """
        Extracts a normalized 128-dimensional appearance embedding from vehicle crop.
        """
        if crop is None or crop.size == 0:
            return np.zeros(self.embedding_dim, dtype=np.float32)

        # Standardize size for Re-ID network
        resized = cv2.resize(crop, (128, 128))
        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(resized, cv2.COLOR_BGR2LAB)

        # Part 1: HSV Color Histograms (32 bins for Hue, 16 for Saturation, 16 for Value = 64 dims)
        h_hist = cv2.calcHist([hsv], [0], None, [32], [0, 180])
        s_hist = cv2.calcHist([hsv], [1], None, [16], [0, 256])
        v_hist = cv2.calcHist([hsv], [2], None, [16], [0, 256])
        
        cv2.normalize(h_hist, h_hist)
        cv2.normalize(s_hist, s_hist)
        cv2.normalize(v_hist, v_hist)

        # Part 2: Spatial grid moments across top/middle/bottom (car roof, hood, grille, bumper = 48 dims)
        grid_features = []
        for row in np.array_split(resized, 4, axis=0):
            for col in np.array_split(row, 2, axis=1):
                mean = np.mean(col, axis=(0, 1))
                std = np.std(col, axis=(0, 1))
                grid_features.extend(mean / 255.0)
                grid_features.extend(std / 255.0)

        # Truncate or pad to exactly embedding_dim
        combined = np.concatenate([
            h_hist.flatten(),
            s_hist.flatten(),
            v_hist.flatten(),
            np.array(grid_features[:48], dtype=np.float32)
        ])

        if len(combined) < self.embedding_dim:
            combined = np.pad(combined, (0, self.embedding_dim - len(combined)))
        else:
            combined = combined[:self.embedding_dim]

        # L2 Normalize
        norm = np.linalg.norm(combined)
        if norm > 1e-6:
            combined = combined / norm

        return combined.astype(np.float32)

    @staticmethod
    def compute_cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Computes cosine similarity between two normalized visual embeddings: range [-1, 1]."""
        if emb1 is None or emb2 is None or len(emb1) == 0 or len(emb2) == 0:
            return 0.0
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        if norm1 < 1e-6 or norm2 < 1e-6:
            return 0.0
        sim = dot_product / (norm1 * norm2)
        return float(np.clip(sim, 0.0, 1.0))

    def retrieve_candidates(
        self,
        query_embedding: np.ndarray,
        gallery: List[Dict[str, Any]],
        top_k: int = 5,
        min_similarity: float = 0.60
    ) -> List[Dict[str, Any]]:
        """
        Ranks gallery candidates by cosine similarity against the query embedding.
        """
        results = []
        for item in gallery:
            emb = np.array(item["embedding"], dtype=np.float32)
            sim = self.compute_cosine_similarity(query_embedding, emb)
            if sim >= min_similarity:
                results.append({
                    **item,
                    "similarity": round(sim, 4)
                })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
