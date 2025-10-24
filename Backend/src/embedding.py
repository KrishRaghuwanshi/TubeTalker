# C:\Users\Krish Raghuwanshi\YTalk\Backend\src\embedding.py

# Note: For simplicity, we use a pre-trained CLIP model via LlamaIndex.
# This requires torch and torchvision.
from llama_index.embeddings.clip import ClipEmbedding
from PIL import Image
import clip
import torch

# Initialize the embedding model once
clip_embedder = ClipEmbedding()

def generate_text_embedding(text: str) -> list:
    return clip_embedder.get_text_embedding(text)


def generate_image_embedding(image_path):
    # Pass the saved frame path directly
    embedding = clip_embedder.get_image_embedding_batch([image_path])
    return embedding[0]  # single embedding

def clip_tokenizer(text: str):
    tokens = clip.tokenize(text, truncate=True)[0]
    token_count = (tokens != 0).sum().item()
    return list(range(token_count))
