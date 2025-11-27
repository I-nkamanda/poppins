import os
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

# Load environment variables
load_dotenv("app/.env")

def verify_db():
    print("Verifying recovered Semantic Vector DB...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in app/.env")
        return

    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=api_key
        )
        
        db_path = "RAG vector generator/vector_db/python_textbook_gemini_db_semantic"
        print(f"Loading DB from: {db_path}")
        
        vector_store = FAISS.load_local(
            db_path,
            embeddings,
            allow_dangerous_deserialization=True
        )
        
        query = "파이썬의 리스트와 튜플의 차이점은 무엇인가요?"
        print(f"Testing query: {query}")
        
        results = vector_store.similarity_search(query, k=1)
        
        if results:
            print("\n✅ Search successful!")
            print(f"Found document from: {results[0].metadata.get('file_name')}")
            print(f"Content preview: {results[0].page_content[:100]}...")
            return True
        else:
            print("❌ Search returned no results.")
            return False
            
    except Exception as e:
        print(f"❌ Error loading or searching DB: {e}")
        return False

if __name__ == "__main__":
    verify_db()
