# PopPins II - Standalone Desktop App

**데스크탑 애플리케이션 버전 (PyWebview + FastAPI)**

## 🎯 개요

이 폴더는 PopPins II를 독립 실행 가능한 데스크탑 애플리케이션으로 만들기 위한 프로토타입입니다.

- **Frontend**: React (빌드된 정적 파일)
- **Backend**: FastAPI (백그라운드 서버)
- **UI Container**: PyWebview (네이티브 앱처럼 보임)

## 🚀 실행 방법

### 1. 의존성 설치

```bash
# 루트 폴더에서 실행
pip install -r requirements.txt
pip install -r standalone/requirements.txt
```

### 2. Frontend 빌드 (최초 1회)

```bash
cd frontend
npm install
npm run build
```

빌드 결과물은 `frontend/dist/` 폴더에 생성됩니다.

### 3. Standalone 앱 실행

```bash
# 프로젝트 루트에서 실행
cd standalone
python launcher.py
```

또는 루트에서 직접:

```bash
python standalone/launcher.py
```

## 📦 구조

```
standalone/
├── launcher.py          # 메인 실행 파일
├── requirements.txt     # 추가 의존성
└── README.md           # 이 파일
```

## ✅ 동작 방식

1. `launcher.py` 실행
2. FastAPI 서버가 백그라운드에서 시작 (`http://127.0.0.1:8001`)
3. 서버 준비 완료 대기
4. PyWebview 창 열기 (네이티브 앱처럼 보임)
5. 사용자가 웹 UI 사용 (브라우저 주소창 없음)

## 🔧 다음 단계 (배포용 exe 만들기)

### PyInstaller 사용

```bash
pip install pyinstaller

pyinstaller --onefile --windowed \
  --add-data "frontend/dist:frontend/dist" \
  --add-data "vector_db:vector_db" \
  --add-data "app/.env:app" \
  --hidden-import=uvicorn.logging \
  --hidden-import=uvicorn.loops.auto \
  --hidden-import=uvicorn.protocols.http.auto \
  standalone/launcher.py
```

결과: `dist/launcher.exe` (단일 실행 파일)

## ⚠️ 주의사항

- `.env` 파일에 `GEMINI_API_KEY`가 설정되어 있어야 합니다
- `vector_db/` 폴더가 필요합니다 (RAG 기능 사용 시)
- `history.db` 파일이 실행 위치에 생성됩니다

## 🐛 문제 해결

### "pywebview를 찾을 수 없습니다"
```bash
pip install pywebview
```

### "서버를 시작할 수 없습니다"
- 8001 포트가 이미 사용 중인지 확인
- `.env` 파일이 `app/` 폴더에 있는지 확인

### 창이 열리지 않음
- Windows: Edge WebView2 런타임 필요
- macOS: 기본 제공
- Linux: `python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.0` 설치

## 📝 버전 정보

- **버전**: 1.10.0
- **최종 업데이트**: 2025-11-27
