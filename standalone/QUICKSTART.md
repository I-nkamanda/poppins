# Standalone App Quick Start

## 📦 생성된 파일

```
standalone/
├── launcher.py          # 메인 실행 파일 ⭐
├── requirements.txt     # 추가 의존성 (pywebview)
└── README.md           # 상세 가이드
```

## 🚀 바로 실행하기 (3단계)

### 1️⃣ pywebview 설치 (최초 1회)

```bash
pip install pywebview requests
```

### 2️⃣ Standalone 앱 실행

standalone 폴더로 이동 후:

```bash
cd standalone
python launcher.py
```

또는 루트에서:

```bash
python standalone/launcher.py
```

### 3️⃣ 창이 열립니다! 🎉

```
🚀 PopPins II - AI 학습 자료 생성기
⏳ 백엔드 서버 시작 중...
✅ 백엔드 서버 준비 완료
📱 애플리케이션 창 열기...
```

**네이티브 앱처럼 보이는 창이 열립니다** (브라우저 주소창 없음)

---

## ✅ 작동 방식

1. FastAPI 서버가 백그라운드에서 실행 (`http://127.0.0.1:8001`)
2. PyWebview 네이티브 창이 자동으로 열림
3. React 빌드된 UI가 창 안에 표시됨
4. 데이터베이스(SQLite) 자동 생성

---

## 🎯 다음 단계 (선택사항)

### exe 파일로 패키징하기

```bash
pip install pyinstaller

pyinstaller --onefile --windowed standalone/launcher.py
```

결과: `dist/launcher.exe` 생성 (더블클릭으로 실행 가능)

---

## ⚠️ 주의사항

- `app/.env` 파일에 `GEMINI_API_KEY` 설정 필요
- Frontend가 빌드되어 있어야 함 (`frontend/dist/` 폴더)
- 8001 포트가 사용 가능해야 함

---

**Created**: 2025-11-27
