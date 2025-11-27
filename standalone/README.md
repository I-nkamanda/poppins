# PopPins II - Tauri Standalone Desktop App

**완전 독립형 데스크탑 애플리케이션** (5-10MB)

# PopPins II - Tauri Standalone Desktop App

**완전 독립형 데스크탑 애플리케이션** (5-10MB)

## 🎯 개요

이 폴더는 PopPins II의 **완전히 독립적인** Tauri 기반 데스크탑 앱입니다.
- ✅ 이 폴더만 있으면 빌드 가능
- ✅ 상위 폴더 참조 없음
- ✅ 모든 의존성 포함
- ✅ v2.1.0 최신 기능 모두 지원 (객관식 퀴즈, 고급 학습)

## 📁 구조

```
standalone/
├── app/                    # 백엔드 (복사됨)
├── frontend/               # Tauri + React
│   ├── dist/              # 빌드된 프론트엔드
│   ├── src-tauri/         # Tauri Rust 코드
│   └── package.json
├── vector_db/             # 벡터 DB (복사됨)
├── .env                   # 환경 변수
├── .gitattributes         # Git LFS 설정 (*.faiss)
├── requirements.txt       # Python 의존성
├── setup.py              # 자동 구성 스크립트
├── launcher.py           # Python 간편 실행기
├── README.md             # 이 파일
├── QUICKSTART.md         # 빠른 시작 가이드
├── ARCHITECTURE.md       # 아키텍처 상세
├── DEPLOYMENT.md         # 배포 가이드
└── DIFFERENCES.md        # Web vs Standalone 비교
```

## 🚀 빌드 방법

### 준비사항

1. **Rust 설치** (최초 1회)
```bash
winget install -e --id Rustlang.Rustup
# 또는 https://rustup.rs/
```

2. **Node.js 설치** (v18+)

### 빌드 순서

#### 1. 독립형 구성 (최초 1회)
```bash
# 프로젝트 루트에서
cd frontend
npm run build

# standalone 구성
cd ../standalone
python setup.py
```

#### 2. Tauri 개발 모드
```bash
cd standalone/frontend
npm run tauri dev
```

#### 3. 프로덕션 빌드
```bash
cd standalone/frontend
npm run tauri build
```

**결과물**: `src-tauri/target/release/bundle/`
- Windows: `PopPins II.exe` (~5-10MB)
- Installer: `PopPins II_0.1.0_x64_en-US.msi`

## 📦 Git LFS

`.faiss` 파일은 Git LFS로 관리됩니다:

```bash
# 이미 설정됨
git lfs track "*.faiss"
git add .gitattributes
```

## ⚙️ 작동 방식

1. Tauri 앱 실행 (.exe)
2. Python FastAPI 서버 자동 시작 (port 8001)
3. WebView 창에 React UI 로드
4. 완료!

## ✨ v2.1.0 최신 기능

- 객관식 퀴즈 (5문제, 즉각 피드백)
- 고급 학습 섹션 (주관식 3문제, AI 채점)
- 개선된 UI/UX
- 안정성 향상

## 🔧 문제 해결

### "Rust가 설치되지 않음"
```bash
rustc --version
# 없으면 Rust 설치 필요
```

### "Python 백엔드 시작 실패"
- Python이 설치되어 있는지 확인
- `standalone/.env`에 GEMINI_API_KEY 설정 확인
- `pip install -r requirements.txt` 실행

### 빌드 시 에러
```bash
# Cargo 캐시 정리
cd frontend/src-tauri
cargo clean
```

## 📚 추가 문서

- [**QUICKSTART.md**](./QUICKSTART.md) - 3분 만에 시작하기
- [**ARCHITECTURE.md**](./ARCHITECTURE.md) - 아키텍처 상세 설명
- [**DEPLOYMENT.md**](./DEPLOYMENT.md) - 배포 및 패키징 가이드
- [**DIFFERENCES.md**](./DIFFERENCES.md) - Web 버전과의 차이점

## 📝 버전 정보

- **버전**: v2.1.0
- **Tauri**: 2.x
- **최종 업데이트**: 2025-11-28
