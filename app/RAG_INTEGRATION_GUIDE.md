# RAG 벡터 DB 통합 가이드

이 문서는 `main_with_RAG.py`를 사용하여 RAG 벡터 DB를 활용하는 방법을 설명합니다.

## 📋 개요

RAG (Retrieval-Augmented Generation) 벡터 DB를 통합하여, Gemini 2.5가 파이썬 교재 PDF의 내용을 참고하여 더 정확하고 관련성 높은 학습 자료를 생성할 수 있도록 했습니다.

## 🔧 설정 방법

### 1. 필요한 패키지 설치

```bash
pip install -r requirements.txt
```

또는 RAG 기능만 사용하려면:

```bash
pip install langchain langchain-community langchain-google-genai faiss-cpu
```

### 2. 환경 변수 설정

`.env` 파일에 다음 환경 변수를 설정하세요:

```env
# Gemini API 키 (필수)
GEMINI_API_KEY=your-gemini-api-key

# RAG 벡터 DB 경로 (선택사항)
# 기본값: ../vector_db/python_textbook_gemini_db
VECTOR_DB_PATH=../vector_db/python_textbook_gemini_db

# 벡터 DB 생성 시 사용한 임베딩 모델 (선택사항, 기본값: gemini)
# Gemini text-embedding-004 모델 사용
VECTOR_DB_EMBEDDING_MODEL=gemini

# RAG 사용 여부 (선택사항, 기본값: true)
USE_RAG=true
```

### 3. 벡터 DB 생성

먼저 RAG 벡터 생성기를 사용하여 벡터 DB를 생성해야 합니다:

```bash
cd "cursor 만들어보기 버전/RAG vector generator"
python python_textbook_rag_generator.py
```

자세한 내용은 `cursor 만들어보기 버전/RAG vector generator/README.md`를 참고하세요.

## 🚀 사용 방법

### 기본 사용

벡터 DB가 올바른 경로에 있고 환경 변수가 설정되어 있으면, 자동으로 RAG 기능이 활성화됩니다.

```bash
# RAG 통합 버전 실행
python app/main_with_RAG.py
```

또는:

```bash
uvicorn app.main_with_RAG:app --reload
```

**참고**: 원본 버전(RAG 없음)을 사용하려면 `main.py`를 사용하세요.

### RAG 기능 비활성화

RAG 기능을 사용하지 않으려면 `.env` 파일에 다음을 추가:

```env
USE_RAG=false
```

## 🔍 작동 방식

### 1. 애플리케이션 시작 시

- `main_with_RAG.py` 실행 시 `startup_event()` 함수가 실행되어 벡터 DB를 로드합니다.
- 벡터 DB가 없거나 로드에 실패하면 경고 메시지를 출력하고 RAG 없이 동작합니다.
- 벡터 DB가 성공적으로 로드되면 콘솔에 "✅ RAG 벡터 DB 로드 완료" 메시지가 표시됩니다.

### 2. 각 생성 함수에서

다음 함수들이 RAG를 사용합니다:

- **`generate_course()`**: 커리큘럼 생성 시 참고 자료 검색
- **`generate_concept()`**: 개념 정리 생성 시 관련 교재 내용 검색
- **`generate_exercise()`**: 실습 과제 생성 시 관련 예제 검색
- **`generate_quiz()`**: 퀴즈 생성 시 관련 내용 검색

각 함수는 다음과 같이 동작합니다:

1. 챕터/주제에 대한 검색 쿼리 생성
2. 벡터 DB에서 관련 문서 검색 (상위 3개)
3. 검색된 내용을 프롬프트에 컨텍스트로 추가
4. Gemini 2.5가 컨텍스트를 참고하여 더 정확한 내용 생성

### 3. 검색 예제

```python
# 예: "파이썬 리스트" 챕터에 대해 개념 정리 생성 시
search_query = "파이썬 리스트 리스트와 튜플의 차이점"
# → 벡터 DB에서 관련 교재 내용 3개 검색
# → 검색된 내용을 프롬프트에 추가
# → Gemini가 참고하여 더 정확한 개념 설명 생성
```

## 📊 성능 및 제한사항

### 성능

- 벡터 DB 로드: 애플리케이션 시작 시 1회만 수행 (약 1-2초)
- 검색 속도: 쿼리당 약 0.1-0.5초
- 메모리 사용: 벡터 DB 크기에 비례 (일반적으로 100-500MB)

### 제한사항

- 벡터 DB는 생성 시 사용한 임베딩 모델과 동일한 모델로 로드해야 합니다.
- 현재 Gemini `text-embedding-004` 모델을 사용합니다.
- OpenAI 임베딩도 지원합니다 (`VECTOR_DB_EMBEDDING_MODEL=openai` 설정).
- 검색 결과는 각 쿼리당 최대 3개 문서로 제한됩니다.

## 🐛 문제 해결

### 벡터 DB를 찾을 수 없습니다

```
⚠️ 벡터 DB를 찾을 수 없습니다: C:/path/to/vector_db
```

**해결 방법:**
1. 벡터 DB가 올바른 경로에 있는지 확인
2. `.env` 파일에 `VECTOR_DB_PATH` 설정
3. 또는 `USE_RAG=false`로 설정하여 RAG 없이 사용

### 임베딩 모델 불일치

벡터 DB 생성 시 사용한 임베딩 모델과 로드 시 사용한 모델이 다르면 오류가 발생할 수 있습니다.

**해결 방법:**
- `.env` 파일에 `VECTOR_DB_EMBEDDING_MODEL=gemini` 설정 (생성 시 사용한 모델과 동일하게)

### 패키지 누락

```
ImportError: No module named 'langchain_community'
```

**해결 방법:**
```bash
pip install langchain langchain-community langchain-google-genai faiss-cpu
```

### API 키 누락

```
⚠️ GEMINI_API_KEY 또는 GOOGLE_API_KEY가 설정되지 않았습니다.
```

**해결 방법:**
- `.env` 파일에 `GEMINI_API_KEY` 설정

## 📝 예제

### RAG 사용 예제

```python
# 자동으로 RAG가 활성화되어 있으면
# POST /generate-study-material
{
    "topic": "파이썬 리스트와 튜플",
    "difficulty": "초급",
    "max_chapters": 2
}

# → 벡터 DB에서 "파이썬 리스트와 튜플" 관련 교재 내용 검색
# → 검색된 내용을 참고하여 더 정확한 학습 자료 생성
```

### RAG 비활성화 예제

```env
USE_RAG=false
```

```python
# RAG 없이 기존 방식으로 동작
# 벡터 DB 검색 없이 Gemini만 사용하여 생성
```

## 🔄 업데이트

벡터 DB를 업데이트하려면:

1. 새로운 PDF 파일을 `pdfs` 폴더에 추가
2. RAG 벡터 생성기 실행:
   ```bash
   cd "cursor 만들어보기 버전/RAG vector generator"
   python python_textbook_rag_generator.py
   ```
3. FastAPI 서버 재시작:
   ```bash
   python app/main_with_RAG.py
   ```

## 📚 참고 자료

- RAG 벡터 생성기: `cursor 만들어보기 버전/RAG vector generator/README.md`
- LangChain 문서: https://python.langchain.com/
- FAISS 문서: https://github.com/facebookresearch/faiss

