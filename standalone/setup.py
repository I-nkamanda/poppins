"""
Standalone 폴더를 완전히 독립적으로 구성하는 스크립트
상위 폴더에서 필요한 모든 파일을 복사
"""
import shutil
from pathlib import Path
import sys

# 프로젝트 루트
ROOT = Path(__file__).parent.parent
STANDALONE = Path(__file__).parent

def setup_standalone():
    print("=" * 70)
    print("🔧 Standalone 폴더 독립형 구성 시작")
    print("=" * 70)
    
    # 1. app/ 복사
    print("\n📁 app/ 복사 중...")
    app_dst = STANDALONE / "app"
    if app_dst.exists():
        print("   기존 app/ 폴더 삭제...")
        shutil.rmtree(app_dst)
    
    # 불필요한 파일 제외하고 복사
    def ignore_patterns(directory, files):
        ignored = []
        for f in files:
            if f in ['__pycache__', '.env', 'test_rag.py', 'main(no RAG).py']:
                ignored.append(f)
            elif f.endswith(('.pyc', '.pyo', '.db')):
                ignored.append(f)
        return ignored
    
    shutil.copytree(ROOT / "app", app_dst, ignore=ignore_patterns)
    print("   ✅ app/ 복사 완료")
    
    # 2. frontend/dist/ 복사
    print("\n📁 frontend/dist/ 복사 중...")
    dist_src = ROOT / "frontend" / "dist"
    dist_dst = STANDALONE / "frontend" / "dist"
    
    if not dist_src.exists():
        print("   ❌ frontend/dist/ 가 없습니다!")
        print("   먼저 frontend를 빌드하세요:")
        print("   cd frontend && npm run build")
        return False
    
    dist_dst.parent.mkdir(parents=True, exist_ok=True)
    if dist_dst.exists():
        print("   기존 dist/ 폴더 삭제...")
        shutil.rmtree(dist_dst)
    shutil.copytree(dist_src, dist_dst)
    print(f"   ✅ frontend/dist/ 복사 완료 ({len(list(dist_dst.rglob('*')))} 파일)")
    
    # 3. vector_db/ 찾기 및 복사
    print("\n📁 vector_db/ 검색 중...")
    
    # 여러 가능한 위치 확인
    vector_candidates = [
        ROOT / "vector_db",  # 표준 위치
        ROOT / "python_textbook_gemini_db_semantic",  # 직접 위치
    ]
    
    # .faiss 파일이 있는 폴더 찾기
    vector_src = None
    for candidate in vector_candidates:
        if candidate.exists():
            faiss_files = list(candidate.rglob("*.faiss"))
            if faiss_files:
                vector_src = candidate
                print(f"   ✓ Vector DB 발견: {candidate.name}")
                break
    
    if vector_src:
        vector_dst = STANDALONE / "vector_db"
        if vector_dst.exists():
            print("   기존 vector_db/ 폴더 삭제...")
            shutil.rmtree(vector_dst)
        
        vector_dst.mkdir(parents=True, exist_ok=True)
        
        # vector_db/python_textbook_gemini_db_semantic/ 구조로 복사
        if vector_src.name == "python_textbook_gemini_db_semantic":
            # 직접 위치에서 발견 → vector_db/ 안에 넣기
            shutil.copytree(vector_src, vector_dst / "python_textbook_gemini_db_semantic")
        else:
            # 이미 vector_db/ 아래 → 전체 복사
            shutil.copytree(vector_src, vector_dst, dirs_exist_ok=True)
        
        # .faiss 파일 개수 확인
        faiss_files = list(vector_dst.rglob("*.faiss"))
        print(f"   ✅ vector_db/ 복사 완료 ({len(faiss_files)}개 .faiss 파일)")
        print(f"   ⚠️  Git LFS 자동 트래킹: {len(faiss_files)}개 .faiss 파일")
    else:
        print("   ⚠️  vector_db/ 또는 .faiss 파일을 찾을 수 없습니다")
        print("   RAG 기능이 비활성화됩니다")
    
    # 4. .env 복사 및 경로 수정
    env_src = ROOT / "app" / ".env"
    if env_src.exists():
        print("\n📄 .env 복사 및 경로 수정 중...")
        env_dst = STANDALONE / ".env"
        shutil.copy(env_src, env_dst)
        
        # VECTOR_DB_PATH 경로 수정 및 API 키 제거
        with open(env_dst, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            if line.strip().startswith("GEMINI_API_KEY="):
                # 키 값 제거 (빈 값으로 설정)
                new_lines.append("GEMINI_API_KEY=\n")
            elif line.strip().startswith("VECTOR_DB_PATH="):
                # 경로 수정
                new_lines.append("VECTOR_DB_PATH=vector_db/python_textbook_gemini_db_semantic\n")
            else:
                new_lines.append(line)
        
        with open(env_dst, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print("   ✅ .env 복사 및 설정 완료 (API 키 초기화됨)")
    else:
        print("\n⚠️  .env 파일이 없습니다")
        print("   app/.env 파일을 생성하고 GEMINI_API_KEY를 설정하세요")
    
    # 5. requirements.txt 확인
    req_src = ROOT / "requirements.txt"
    if req_src.exists():
        print("\n📄 requirements.txt 복사 중...")
        shutil.copy(req_src, STANDALONE / "requirements.txt")
        print("   ✅ requirements.txt 복사 완료")
    
    print("\n" + "=" * 70)
    print("✅ Standalone 폴더 구성 완료!")
    print("=" * 70)
    print("\n📋 다음 단계:")
    print("   1. Git LFS 설정:")
    print("      cd standalone")
    print("      git lfs track '*.faiss'")
    print("      git add .gitattributes")
    print("")
    print("   2. Tauri 초기화:")
    print("      cd frontend")
    print("      npm install")
    print("      npm install --save-dev @tauri-apps/cli @tauri-apps/api")
    print("      npm run tauri init")
    print("")
    return True

if __name__ == "__main__":
    try:
        success = setup_standalone()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
