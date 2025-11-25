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

new_db_path = "vector_db/python_textbook_gemini_db"
old_db_path = "vector_db/.vector_db-oldver/python_textbook_gemini_db"

def load_db(path, name):
    print(f"Loading {name} from {path}...")
    try:
        db = FAISS.load_local(
            path, embeddings, allow_dangerous_deserialization=True
        )
        print(f"✅ {name} loaded successfully.")
        return db
    except Exception as e:
        print(f"❌ Error loading {name}: {e}")
        return None

def compare_performance():
    new_db = load_db(new_db_path, "New DB")
    old_db = load_db(old_db_path, "Old DB")
    
    if not new_db or not old_db:
        print("Failed to load one or both databases. Aborting comparison.")
        return

    # Test queries focusing on areas where filtering/cleaning should help
    test_queries = [
        "파이썬 리스트 슬라이싱하는 방법", # Previously retrieved TOC
        "딕셔너리 키와 값 순회하기", # Previously retrieved TOC
        "try except 예외 처리",
        "파일 열고 닫기 (open, close)"
    ]

    with open("comparison_results.txt", "w", encoding="utf-8") as f:
        f.write("="*60 + "\n")
        f.write("RAG Vector DB Performance Comparison (Old vs New)\n")
        f.write("="*60 + "\n")
        
        for query in test_queries:
            f.write(f"\n🔎 Query: '{query}'\n")
            f.write("-" * 60 + "\n")
            
            # Retrieve from Old DB
            old_docs = old_db.similarity_search(query, k=3)
            f.write(f"[Old DB Results]\n")
            for i, doc in enumerate(old_docs, 1):
                source = os.path.basename(doc.metadata.get('source', 'Unknown'))
                page = doc.metadata.get('page', 'N/A')
                content_preview = doc.page_content[:100].replace('\n', ' ')
                f.write(f"  {i}. {source} (p.{page}) | {content_preview}...\n")
            
            f.write("\n")
            
            # Retrieve from New DB
            new_docs = new_db.similarity_search(query, k=3)
            f.write(f"[New DB Results]\n")
            for i, doc in enumerate(new_docs, 1):
                source = os.path.basename(doc.metadata.get('source', 'Unknown'))
                page = doc.metadata.get('page', 'N/A')
                content_preview = doc.page_content[:100].replace('\n', ' ')
                f.write(f"  {i}. {source} (p.{page}) | {content_preview}...\n")
            
            f.write("-" * 60 + "\n")

    print("Comparison completed. Results written to comparison_results.txt")

if __name__ == "__main__":
    compare_performance()
