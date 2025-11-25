
# PopPins II

- **AI 모델**: Gemini 2.5 Flash / Gemini 2.0 Flash Exp
- **벡터 DB**: FAISS with Semantic Chunking (LangChain)

## ✨ 최신 개선 사항 (v1.5.1)

- 🔧 **마크다운 코드 블록 보존**: 생성된 콘텐츠의 코드 블록이 올바르게 렌더링됩니다
- 📥 **다운로드 기능 개선**: 파일명 정규화 및 크로스 브라우저 호환성 향상
- 🛠️ **JSON 파싱 강화**: 불완전한 응답에 대한 안정적인 처리
- 📝 **응답 모델 확장**: 더 명확한 타입 검증 및 오류 처리

## 🚀 Quick Start

### 사전 요구사항

- Python 3.8+
- Node.js 18+
- Gemini API 키 ([Google AI Studio](https://makersuite.google.com/app/apikey)에서 발급)

### 1. 환경 변수 설정

`app/.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
GEMINI_API_KEY=your-gemini-api-key-here
USE_RAG=true
VECTOR_DB_PATH=../python_textbook_gemini_db_semantic
VECTOR_DB_EMBEDDING_MODEL=gemini
```

### 1-1. RAG 벡터 DB 생성 (선택사항)

RAG 기능을 사용하려면 먼저 벡터 DB를 생성해야 합니다:

```bash
cd "RAG vector generator"
pip install -r requirements.txt langchain-google-genai

# .env 파일 생성 (RAG vector generator 폴더에)
# GEMINI_API_KEY=your-gemini-api-key-here

# 벡터 DB 생성 (Gemini 임베딩 사용)
python python_textbook_rag_generator.py --db-name python_textbook_gemini_db_semantic --embedding-model gemini
```

생성된 벡터 DB는 프로젝트 루트에 저장됩니다.

자세한 사용법은 [`RAG vector generator/README.md`](./RAG%20vector%20generator/README.md)를 참고하세요.

### 2. Backend 실행

```bash
cd app
pip install -r requirements.txt
uvicorn main_with_RAG:app --port 8001 --reload
```

서버가 실행되면 `http://localhost:8001/docs`에서 API 문서를 확인할 수 있습니다.

### 3. Frontend 실행

```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:5173`을 열면 애플리케이션을 사용할 수 있습니다.

### 4. 사용하기

1. 학습 주제, 난이도, 챕터 수를 입력
2. "학습 자료 생성하기" 버튼 클릭
3. 생성된 커리큘럼에서 원하는 챕터 클릭
4. 개념 학습 → 실습 과제 → 퀴즈 순서로 학습

## 📁 프로젝트 구조

```
Pop-pins2/
├── app/                    # Backend (FastAPI)
│   ├── services/          # [NEW] 비즈니스 로직 모듈
│   │   └── generator.py   # 콘텐츠 생성 로직 (Gemini + RAG)
│   ├── main_with_RAG.py   # 메인 앱 (서비스 호출)
│   ├── requirements.txt
│   └── README.md
├── frontend/              # Frontend (React)
│   ├── src/
│   │   ├── pages/         # 페이지 컴포넌트
│   │   ├── components/    # 재사용 컴포넌트
│   │   └── services/       # API 서비스
│   └── package.json
├── RAG vector generator/  # RAG 벡터 DB 생성 도구
│   ├── python_textbook_rag_generator.py
│   ├── pdfs/              # PDF 파일 저장소
│   └── README.md
├── python_textbook_gemini_db_semantic/  # RAG 벡터 DB (생성된 파일 저장)
├── manual.md              # 사용설명서 (비전공자용)
├── dev_summary.md         # 개발 요약
└── README.md              # 이 파일
```

## 📚 문서

- 📖 **사용설명서**: [`manual.md`](./manual.md) - 비전공자도 이해할 수 있는 상세 가이드
- 📝 **개발 요약**: [`dev_summary.md`](./dev_summary.md) - 개발 진행 상황 및 변경 이력
- 🔄 **변경 이력**: [`app/CHANGELOG.md`](./app/CHANGELOG.md) - 버전별 변경 사항
- 🔌 **API 문서**: [`app/API_REFERENCE.md`](./app/API_REFERENCE.md) - API 엔드포인트 상세
- 🔍 **RAG 가이드**: [`app/RAG_INTEGRATION_GUIDE.md`](./app/RAG_INTEGRATION_GUIDE.md) - RAG 설정 및 사용법

## 🎯 주요 API 엔드포인트

- `POST /generate-course` - 커리큘럼만 생성 (Lazy-Loading)
- `POST /generate-chapter-content` - 챕터 상세 내용 생성
- `POST /download-chapter` - 챕터를 Markdown으로 다운로드
- `POST /grade-quiz` - 퀴즈 답안 채점
- `GET /health` - 서버 상태 확인

자세한 내용은 API 문서를 참고하세요.

## 🔧 문제 해결

### 서버 연결 오류
- 백엔드 서버가 실행 중인지 확인 (`http://localhost:8001/health`)
- 포트가 8001인지 확인

### API 키 오류
- `.env` 파일에 올바른 `GEMINI_API_KEY`가 설정되어 있는지 확인

### RAG 관련 오류
- 벡터 DB 경로가 올바른지 확인
- `USE_RAG=false`로 설정하여 RAG 없이 사용 가능

자세한 문제 해결 방법은 [`manual.md`](./manual.md)의 "문제 해결" 섹션을 참고하세요.

## 📝 라이선스

이 프로젝트는 교육 목적으로 자유롭게 사용할 수 있습니다.

## 🤝 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요.

---

**버전**: v1.6.0 | **최종 업데이트**: 2025-11-25
