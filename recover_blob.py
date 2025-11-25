import subprocess
import sys

def recover_blob(blob_hash, output_path):
    print(f"Recovering {blob_hash} to {output_path}...")
    try:
        # git cat-file -p 명령어를 실행하고 바이너리 출력을 캡처
        # -p 대신 blob 타입을 명시하지 않고 내용만 가져오기 위해 git cat-file blob <hash> 사용 가능
        # 하지만 git cat-file -p가 더 안전할 수 있음 (타입 확인 등)
        # 여기서는 git cat-file -p 사용 (바이너리 출력)
        
        # 주의: git cat-file -p는 내용을 pretty-print하므로 바이너리에는 적합하지 않을 수 있음
        # git cat-file blob <hash> 가 정확함
        
        process = subprocess.Popen(
            ['git', 'cat-file', 'blob', blob_hash],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            print(f"Error: {stderr.decode('utf-8')}")
            return False
            
        with open(output_path, 'wb') as f:
            f.write(stdout)
            
        print(f"Success! Wrote {len(stdout)} bytes.")
        return True
        
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    # index.faiss
    recover_blob('4ab8782eaee1ffeff8519de36c84a8753e5e1250', 'RAG vector generator/vector_db/python_textbook_gemini_db_semantic/index.faiss')
    
    # index.pkl
    recover_blob('c965380b482863d300de2a0eb761e63db45b8540', 'RAG vector generator/vector_db/python_textbook_gemini_db_semantic/index.pkl')
