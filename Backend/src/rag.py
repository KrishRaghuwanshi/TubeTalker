import os
import lancedb
import google.generativeai as genai
from PIL import Image # <-- NEW: Needed to load images
from llama_index.core import StorageContext
from llama_index.core.indices import MultiModalVectorStoreIndex
from llama_index.vector_stores.lancedb import LanceDBVectorStore
from llama_index.embeddings.clip import ClipEmbedding

def retrieve_and_answer(session_id: str, query: str, api_key: str) -> dict:
    """
    Connects to a session's LanceDB, retrieves context using a multi-modal
    retriever, loads images, and generates an answer using Gemini Pro Vision.
    """
    # 1. Connect to the session-specific LanceDB table
    db_path = f"/tmp/lancedb_sessions/{session_id}"
    db = lancedb.connect(db_path)
    table_name = f"session_{session_id}"
    table = db.open_table(table_name)

    # 2. Re-hydrate the LlamaIndex Vector Stores
    vector_store = LanceDBVectorStore(table=table, embedding_field_name="vector")
    image_store = LanceDBVectorStore(table=table, embedding_field_name="vector")
    storage_context = StorageContext.from_defaults(vector_store=vector_store, image_store=image_store)

    # 3. Reconstruct the MultiModalVectorStoreIndex
    index = MultiModalVectorStoreIndex.from_vector_store(
        vector_store=storage_context.vector_store,
        image_store=storage_context.image_store,
        embed_model=ClipEmbedding()
    )

    # 4. Create the MultiModal Retriever
    retriever = index.as_retriever(similarity_top_k=3, image_similarity_top_k=2)

    # 5. Retrieve nodes
    retrieved_nodes = retriever.retrieve(query)

    # 6. Build the text context and identify image paths
    context = "\n\n".join(
        [node.get_content() for node in retrieved_nodes if node.metadata.get("type") == "text"]
    )
    # --- MODIFIED: Get full paths to the image files ---
    frames_base_path = f"/tmp/video_rag/{session_id}/frames" # Base path where frames were saved
    image_paths = [
        os.path.join(frames_base_path, node.get_content())
        for node in retrieved_nodes if node.metadata.get("type") == "image"
        and os.path.exists(os.path.join(frames_base_path, node.get_content())) # Check if file exists
    ]

    if not context:
        context = "No relevant text context found in the video for this query."

    # 7. --- MODIFIED: Prepare input for Gemini Pro Vision ---
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro-vision') # <-- Use the vision model

    # Create the prompt parts (text first, then images)
    prompt_parts = [
        "Based on the following context (text and images) from a video, answer the user's query.\n\n"
        f"Text Context: \"{context}\"\n\n"
        f"Query: \"{query}\"\n\n"
        "Answer:"
    ]

    # Load and add images to the prompt parts
    loaded_images = []
    for img_path in image_paths:
        try:
            img = Image.open(img_path)
            loaded_images.append(img)
        except Exception as e:
            print(f"Warning: Could not load image {img_path}: {e}")
            
    # Combine text and loaded images
    prompt_parts.extend(loaded_images)

    # 8. --- MODIFIED: Call the Vision model ---
    try:
        response = model.generate_content(prompt_parts)
        answer = response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        # Fallback to text-only if vision fails or has content issues
        try:
            text_model = genai.GenerativeModel('gemini-pro')
            text_prompt = prompt_parts[0] # Use only the text part
            response = text_model.generate_content(text_prompt)
            answer = f"(Vision model failed, using text only): {response.text}"
        except Exception as fallback_e:
            print(f"Fallback Gemini API call failed: {fallback_e}")
            answer = "Error generating answer from Gemini."

    # Return the answer and the filenames (for frontend display)
    image_filenames = [os.path.basename(p) for p in image_paths]
    return {"answer": answer}