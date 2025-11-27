# 환경 변수 설정 체크 결과

**날짜**: 2025-11-27  
**참고**: `qa_logs/suggestions.md`의 제안사항 반영

---

## ✅ 완료된 개선 사항

### 1. 프론트엔드 API URL 환경 변수화

**Before**:
```typescript
const API_BASE_URL = 'http://localhost:8001'; // 하드코딩
```

**After**:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';
```

**변경 파일**: `frontend/src/services/api.ts`

**사용 방법**:
- `frontend/.env` 파일 생성
- `VITE_API_BASE_URL=http://localhost:8001` 설정
- 프로덕션: `VITE_API_BASE_URL=https://api.yourdomain.com`

### 2. 백엔드 포트 환경 변수화

**Before**:
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # 하드코딩
```

**After**:
```python
port = int(os.getenv("PORT", "8001"))
host = os.getenv("HOST", "0.0.0.0")
logger.info(f"Starting server on {host}:{port}")
uvicorn.run(app, host=host, port=port)
```

**변경 파일**: `app/main.py`

**사용 방법**:
- `.env` 파일에 `PORT=8001` 설정
- 프로덕션: `PORT=8080` 등으로 변경 가능

### 3. 문서 업데이트

**변경 파일**:
- ✅ `ENV_SETUP.md`: 환경 변수 설정 가이드에 포트 및 API URL 설정 추가
- ✅ `app/API_REFERENCE.md`: Base URL 포트 수정 (8000 → 8001)

### 4. 예시 파일 생성

**생성 파일**:
- `frontend/.env.example`: 프론트엔드 환경 변수 예시 (생성 시도했으나 .gitignore로 차단됨)

---

## 📋 환경 변수 목록

### 백엔드 (.env)

```env
# 필수
GEMINI_API_KEY=your_api_key_here

# 선택
USE_RAG=true
VECTOR_DB_PATH=../python_textbook_gemini_db_semantic
VECTOR_DB_EMBEDDING_MODEL=gemini
LOG_LEVEL=INFO
PORT=8001
HOST=0.0.0.0
```

### 프론트엔드 (frontend/.env)

```env
# 선택 (기본값: http://localhost:8001)
VITE_API_BASE_URL=http://localhost:8001
```

---

## ✅ 체크리스트

- [x] 프론트엔드 API URL을 환경 변수로 변경
- [x] 백엔드 포트를 환경 변수로 변경
- [x] 환경 변수 설정 가이드 업데이트
- [x] API 문서 포트 정보 수정
- [x] 기본값 설정 (환경 변수 없을 때도 동작)

---

## 🎯 제안사항 반영 완료

`suggestions.md`의 제안사항:
> "Ensure environment variables are used for API URLs in production to avoid hardcoded port mismatches."

**완료**: ✅
- 프론트엔드와 백엔드 모두 환경 변수 사용 가능
- 기본값 제공으로 하위 호환성 유지
- 프로덕션 환경에서 쉽게 설정 변경 가능

---

## 🧪 테스트 방법

### 1. 기본값 테스트 (환경 변수 없음)

```bash
# 백엔드
cd app
python -m uvicorn app.main:app  # 포트 8001로 실행

# 프론트엔드
cd frontend
npm run dev  # http://localhost:8001로 API 호출
```

### 2. 환경 변수 사용 테스트

```bash
# 백엔드
cd app
export PORT=8080
python -m uvicorn app.main:app  # 포트 8080으로 실행

# 프론트엔드
cd frontend
echo "VITE_API_BASE_URL=http://localhost:8080" > .env
npm run dev  # http://localhost:8080으로 API 호출
```

---

## 📝 다음 단계

1. **프로덕션 배포 시**:
   - 환경 변수로 포트 및 API URL 설정
   - `.env` 파일은 Git에 커밋하지 않음 (보안)

2. **CI/CD 파이프라인**:
   - 환경 변수를 CI/CD 시스템에서 주입
   - 각 환경(dev, staging, prod)별로 다른 값 사용

3. **Docker 배포**:
   - `docker-compose.yml`에서 환경 변수 설정
   - 또는 `docker run -e PORT=8001 ...` 형식으로 전달

---

**완료 시간**: 2025-11-27

