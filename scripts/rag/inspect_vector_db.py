import os
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="../app/.env")

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in ../app/.env")
    exit(1)

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004", google_api_key=api_key
)

db_path = "vector_db/python_textbook_gemini_db"

try:
    vector_store = FAISS.load_local(
        db_path, embeddings, allow_dangerous_deserialization=True
    )
    
    # Get all document IDs
    doc_ids = list(vector_store.index_to_docstore_id.values())
    total_docs = len(doc_ids)

    # Write output to file with utf-8 encoding
    with open("inspection_result.txt", "w", encoding="utf-8") as f:
        f.write(f"Successfully loaded vector store from {db_path}\n")
        f.write(f"Total number of chunks: {total_docs}\n")
        f.write("\n--- Sample Chunks Inspection ---\n")
        
        # Inspect first few chunks
        for i in range(min(3, total_docs)):
            doc_id = doc_ids[i]
            doc = vector_store.docstore.search(doc_id)
            
            f.write(f"\n[Chunk {i+1}]\n")
            f.write(f"Source: {doc.metadata.get('source', 'Unknown')}\n")
            f.write(f"Page: {doc.metadata.get('page', 'Unknown')}\n")
            f.write(f"Content Length: {len(doc.page_content)} characters\n")
            f.write(f"Content Preview:\n{doc.page_content[:200]}...\n")
            f.write("-" * 50 + "\n")

        # Calculate average chunk size
        total_chars = 0
        for doc_id in doc_ids[:100]: # Sample first 100 for average
            doc = vector_store.docstore.search(doc_id)
            total_chars += len(doc.page_content)
        
        avg_size = total_chars / min(100, total_docs)
        f.write(f"\nAverage chunk size (first 100 samples): {avg_size:.2f} characters\n")
        print("Inspection completed. Results written to inspection_result.txt")

except Exception as e:
    print(f"Error loading vector store: {e}")
