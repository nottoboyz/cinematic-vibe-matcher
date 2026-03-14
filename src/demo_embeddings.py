# src/test_embeddings.py
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('all-mpnet-base-v2')

sentences = [
    "A mind-bending thriller about dreams within dreams",
    "A space journey that bends time and explores black holes",
    "A friendly bear from Peru adapts to life in London"
]

embeddings = model.encode(sentences)

print(f"Shape: {embeddings.shape}")
print(f"ตัวอย่าง 5 ค่าแรกของประโยคแรก: {embeddings[0][:5]}")

from sklearn.metrics.pairwise import cosine_similarity

sim_matrix = cosine_similarity(embeddings)

print("\nSimilarity Matrix:")
print(f"Inception vs Interstellar:  {sim_matrix[0][1]:.4f}")
print(f"Inception vs Paddington:    {sim_matrix[0][2]:.4f}")
print(f"Interstellar vs Paddington: {sim_matrix[1][2]:.4f}")