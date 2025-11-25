import os
import time
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="app/.env")

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in app/.env")
    exit(1)

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004", google_api_key=api_key
)

db_path = "vector_db/python_textbook_gemini_db"

def evaluate_retrieval():
    print(f"Loading vector store from {db_path}...")
    try:
        vector_store = FAISS.load_local(
            db_path, embeddings, allow_dangerous_deserialization=True
        )
        print("✅ Vector store loaded successfully.")
    except Exception as e:
        print(f"❌ Error loading vector store: {e}")
        return

    # Test queries covering different topics
    test_queries = [
        "파이썬 리스트 슬라이싱하는 방법",
        "함수에서 가변 인자(*args) 사용법",
        "파일 열고 닫기 (open, close)",
        "try except 예외 처리",
        "딕셔너리 키와 값 순회하기"
    ]

    # Write output to file with utf-8 encoding
    with open("evaluation_results.txt", "w", encoding="utf-8") as f:
        f.write("="*50 + "\n")
        f.write("RAG Retrieval Performance Evaluation\n")
        f.write("="*50 + "\n")

        for query in test_queries:
            f.write(f"\n🔎 Query: '{query}'\n")
            start_time = time.time()
            
            # Retrieve top 3 chunks
            docs = vector_store.similarity_search(query, k=3)
            
            elapsed_time = time.time() - start_time
            f.write(f"⏱️ Retrieval Time: {elapsed_time:.4f}s\n")
            
            if not docs:
                f.write("❌ No documents found.\n")
                continue

            for i, doc in enumerate(docs, 1):
                source = os.path.basename(doc.metadata.get('source', 'Unknown'))
                page = doc.metadata.get('page', 'N/A')
                content_preview = doc.page_content[:150].replace('\n', ' ')
                
                f.write(f"  [Chunk {i}] Source: {source} (p.{page})\n")
                f.write(f"    Content: {content_preview}...\n")
                f.write("-" * 30 + "\n")
                
    print("Evaluation completed. Results written to evaluation_results.txt")

if __name__ == "__main__":
    evaluate_retrieval()
