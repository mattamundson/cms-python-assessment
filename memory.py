import chromadb
import os
from pathlib import Path

# Initialize ChromaDB client
PERSIST_PATH = Path(os.path.expanduser("~/.hermes/memory"))
PERSIST_PATH.mkdir(parents=True, exist_ok=True)

client = chromadb.PersistentClient(path=str(PERSIST_PATH))
collection = client.get_or_create_collection(name="jarvis_memory")

def index_task_experience(task_id, title, execution_output):
    """
    Summarizes and indexes a completed task experience into the vector store.
    """
    metadata = {"task_id": task_id, "title": title}
    # For now, we'll store the execution output as the document
    collection.add(
        documents=[execution_output],
        metadatas=[metadata],
        ids=[task_id]
    )
    print(f"[Memory] Indexed experience for task {task_id}")

def retrieve_related_experiences(query, n_results=3):
    """
    Retrieves the most relevant past experiences for a given query.
    """
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results['documents'][0] if results['documents'] else []

if __name__ == "__main__":
    # Test memory
    print("Testing Jarvis Memory...")
    index_task_experience("test-1", "Fix API key error", "The user had an insufficient quota error. I added a fallback to Google Gemini.")
    related = retrieve_related_experiences("How do I fix a quota error?")
    print(f"Retrieved: {related}")
