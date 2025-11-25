import os
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

def verify_new_db():
    print("Loading New Vector DB...")
    try:
        db = FAISS.load_local(
            db_path, embeddings, allow_dangerous_deserialization=True
        )
        print(f"✅ New DB loaded successfully from {db_path}")
    except Exception as e:
        print(f"❌ Error loading New DB: {e}")
        return

    # Test queries focusing on areas where filtering/cleaning should help
    test_queries = [
        "파이썬 리스트 슬라이싱하는 방법",
        "딕셔너리 키와 값 순회하기",
        "try except 예외 처리",
        "파일 열고 닫기 (open, close)",
        "for 루프 사용법"
    ]

    with open("new_db_verification.txt", "w", encoding="utf-8") as f:
        f.write("="*60 + "\n")
        f.write("New Vector DB Verification Results\n")
        f.write(f"DB Path: {db_path}\n")
        f.write("="*60 + "\n\n")
        
        for query in test_queries:
            f.write(f"🔎 Query: '{query}'\n")
            f.write("-" * 60 + "\n")
            
            # Retrieve from New DB
            docs = db.similarity_search(query, k=3)
            f.write(f"[Results]\n")
            for i, doc in enumerate(docs, 1):
                source = os.path.basename(doc.metadata.get('source', 'Unknown'))
                file_name = doc.metadata.get('file_name', source)
                page = doc.metadata.get('page', 'N/A')
                content_preview = doc.page_content[:200].replace('\n', ' ')
                f.write(f"  {i}. {file_name} (p.{page})\n")
                f.write(f"     Preview: {content_preview}...\n\n")
            
            f.write("-" * 60 + "\n\n")

    print("✅ Verification completed. Results written to new_db_verification.txt")

if __name__ == "__main__":
    verify_new_db()
