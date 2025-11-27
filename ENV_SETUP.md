# 환경 변수 설정 가이드

PopPins II를 실행하기 위해 필요한 환경 변수를 설정하는 방법입니다.

## 필수 설정

### GEMINI_API_KEY

Google Gemini API 키를 설정해야 합니다.

1. [Google AI Studio](https://aistudio.google.com/)에 접속
2. API 키 생성
3. `.env` 파일에 다음 형식으로 추가:

```env
GEMINI_API_KEY=your_actual_api_key_here
```

**주의**: `your_api_key_here` 같은 기본값은 사용할 수 없습니다.

## 선택 설정

### RAG (Retrieval-Augmented Generation)

RAG 기능을 사용하려면 다음 환경 변수를 설정하세요:

```env
# RAG 사용 여부 (true/false)
USE_RAG=true

# 벡터 DB 경로
VECTOR_DB_PATH=../python_textbook_gemini_db_semantic

# 임베딩 모델 (gemini 또는 openai)
VECTOR_DB_EMBEDDING_MODEL=gemini
```

RAG를 사용하지 않으려면:
```env
USE_RAG=false
```

### 로깅

로그 레벨을 조정하려면:

```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### 서버 포트 설정 (백엔드)

백엔드 서버 포트를 변경하려면:

```env
PORT=8001  # 기본값: 8001
HOST=0.0.0.0  # 기본값: 0.0.0.0 (모든 인터페이스에서 접근 가능)
```

### 프론트엔드 API URL 설정

프론트엔드에서 백엔드 API URL을 설정하려면 `frontend/.env` 파일을 생성하고:

```env
VITE_API_BASE_URL=http://localhost:8001
```

**주의**: Vite는 환경 변수 앞에 `VITE_` 접두사가 필요합니다.

프로덕션 환경에서는:
```env
VITE_API_BASE_URL=https://api.yourdomain.com
```

## .env 파일 생성 방법

1. 프로젝트 루트 디렉토리에 `.env` 파일 생성
2. 위의 환경 변수들을 복사하여 실제 값으로 채우기
3. `.env` 파일은 Git에 커밋하지 마세요 (`.gitignore`에 포함되어 있음)

## 문제 해결

### ContentGenerator 초기화 실패

다음 사항을 확인하세요:

1. **GEMINI_API_KEY가 설정되었는지 확인**
   ```bash
   # Windows PowerShell
   $env:GEMINI_API_KEY
   
   # Linux/Mac
   echo $GEMINI_API_KEY
   ```

2. **.env 파일이 올바른 위치에 있는지 확인**
   - 프로젝트 루트 디렉토리 (app/ 디렉토리와 같은 레벨)

3. **API 키 형식 확인**
   - 최소 20자 이상이어야 함
   - 공백이나 특수문자가 포함되지 않았는지 확인

4. **서버 로그 확인**
   - `logs/app.log` 파일에서 초기화 에러 메시지 확인

### 학습 목표 생성 실패

다음 사항을 확인하세요:

1. **API 키 유효성**
   - Google AI Studio에서 API 키가 활성화되어 있는지 확인
   - API 할당량이 남아있는지 확인

2. **네트워크 연결**
   - 인터넷 연결 확인
   - 방화벽 설정 확인

3. **서버 로그 확인**
   - 에러 메시지와 스택 트레이스 확인

