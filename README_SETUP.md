# New Repository Setup Guide

이 가이드는 `Pop-pins2` 프로젝트를 새로운 Git 리포지토리에 올리고 설정하는 방법을 설명합니다.

## 1. 사전 준비 (Cleanup)

새 리포지토리에 올리기 전에 불필요한 파일들을 정리해야 합니다.

1.  **Cleanup 스크립트 실행**:
    ```powershell
    ./cleanup_for_new_repo.ps1
    ```
    이 스크립트는 `node_modules`, `__pycache__`, 로그 파일 등을 삭제하여 프로젝트 용량을 줄입니다.

2.  **Vector DB 확인 (Git LFS)**:
    *   `index.faiss` 파일은 용량이 커서 **Git LFS**로 관리됩니다.
    *   `.gitignore`에서 제외되지 않았으므로, LFS가 설치되어 있다면 자동으로 다운로드됩니다.

## 2. Git 초기화 및 푸시

```bash
# 1. Git 초기화
git init

# 2. Git LFS 설치 (필수)
git lfs install

# 3. 모든 파일 스테이징 (LFS 추적 설정 포함)
git add .

# 4. 커밋
git commit -m "Initial commit: Pop-pins2 v1.5.1 with Git LFS"

# 5. 리모트 추가 (새 리포지토리 주소)
git remote add origin <NEW_REPOSITORY_URL>

# 6. 푸시
git push -u origin main
```

## 3. 새 환경에서 실행하기 (Clone 후)

새로운 컴퓨터나 서버에서 프로젝트를 받아서 실행할 때의 절차입니다.

### 3-1. 환경 변수 설정

`app/.env` 파일을 생성하고 다음 내용을 채워넣으세요 (보안상 Git에 없으므로 직접 생성 필요):

```env
GEMINI_API_KEY=your_api_key_here
USE_RAG=true
VECTOR_DB_PATH=../python_textbook_gemini_db_semantic
VECTOR_DB_EMBEDDING_MODEL=gemini
```

### 3-2. Vector DB 복원 (Git LFS)

이 프로젝트는 RAG 기능을 위해 Vector DB가 필요하며, Git LFS로 관리됩니다.

*   **Clone 시 자동 다운로드**: `git clone` 시 LFS 파일도 자동으로 받아집니다.
*   **수동 다운로드 (파일이 작게 보일 경우)**:
    ```bash
    git lfs pull
    ```

### 3-3. 실행

**Backend:**
```bash
cd app
pip install -r requirements.txt
uvicorn main_with_RAG:app --port 8001 --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```
