# PopPins II Standalone - Deployment Guide

## 개요

이 문서는 PopPins II Standalone 데스크탑 애플리케이션의 빌드 및 배포 과정을 상세하게 설명합니다.

---

## 배포 전 체크리스트

### ✅ 필수 준비사항

- [ ] Rust Toolchain 설치 확인
- [ ] Node.js v18+ 설치 확인
- [ ] Python 3.8+ 설치 확인
- [ ] Frontend 빌드 완료 (`frontend/dist/` 폴더 존재)
- [ ] Backend 의존성 설치 완료
- [ ] 벡터 DB 준비 완료 (`vector_db/` 폴더)
- [ ] 환경 변수 설정 (`.env` 파일)
- [ ] 아이콘 파일 준비 (`.ico`, `.png`)

---

## Windows 빌드

### 1. 개발 환경 준비

#### Rust 설치
```powershell
# Windows Package Manager 사용
winget install -e --id Rustlang.Rustup

# 또는 수동 설치
# https://rustup.rs/ 에서 다운로드
```

#### Node.js 설치
```powershell
winget install -e --id OpenJS.NodeJS
```

#### Python 설치
```powershell
winget install -e --id Python.Python.3.11
```

### 2. Frontend 빌드

```bash
# 프로젝트 루트에서
cd frontend
npm install
npm run build
```

**결과**: `frontend/dist/` 폴더에 빌드 파일 생성

### 3. Standalone 구성

```bash
cd ../standalone
python setup.py
```

**setup.py가 수행하는 작업**:
- `app/` 폴더 복사
- `vector_db/` 폴더 복사 또는 심볼릭 링크 생성
- `frontend/dist/` 복사
- `.env` 파일 생성 (템플릿)

### 4. Tauri 빌드

```bash
cd frontend
npm install
npm run tauri build
```

### 5. 빌드 결과 확인

빌드 완료 후 다음 위치에 파일이 생성됩니다:

```
standalone/frontend/src-tauri/target/release/bundle/
├── msi/
│   └── PopPins II_0.1.0_x64_en-US.msi  # Windows 설치 파일 (~10-15MB)
├── nsis/
│   └── PopPins II_0.1.0_x64-setup.exe  # NSIS 설치 파일
└── PopPins II.exe                      # 실행 파일 (~5-10MB)
```

---

## macOS 빌드

### 1. 개발 환경 준비

```bash
# Homebrew 설치 (없는 경우)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Rust 설치
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Node.js 설치
brew install node

# Python 설치
brew install python@3.11
```

### 2. Frontend 빌드 (Windows와 동일)

```bash
cd frontend
npm install
npm run build
```

### 3. Tauri 빌드

```bash
cd ../standalone/frontend
npm install
npm run tauri build
```

### 4. 빌드 결과

```
standalone/frontend/src-tauri/target/release/bundle/
├── dmg/
│   └── PopPins II_0.1.0_x64.dmg        # macOS 디스크 이미지
└── macos/
    └── PopPins II.app                  # macOS 앱 번들
```

### 5. 코드 서명 (선택사항)

```bash
# Apple Developer 계정 필요
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" "PopPins II.app"

# 공증(Notarization)
xcrun notarytool submit "PopPins II_0.1.0_x64.dmg" --apple-id "your@email.com" --password "app-specific-password" --team-id "TEAM_ID"
```

---

## Linux 빌드

### 1. 개발 환경 준비

```bash
# Debian/Ubuntu
sudo apt update
sudo apt install -y curl git build-essential libssl-dev pkg-config libgtk-3-dev libwebkit2gtk-4.0-dev libappindicator3-dev

# Rust 설치
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Node.js 설치 (nvm 사용)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18

# Python 설치
sudo apt install python3 python3-pip
```

### 2. Tauri 빌드

```bash
cd standalone/frontend
npm install
npm run tauri build
```

### 3. 빌드 결과

```
standalone/frontend/src-tauri/target/release/bundle/
├── deb/
│   └── pop-pins-ii_0.1.0_amd64.deb     # Debian 패키지
└── appimage/
    └── pop-pins-ii_0.1.0_amd64.AppImage # AppImage
```

---

## 환경 변수 설정

### 개발 환경

`standalone/.env` 파일:
```env
GEMINI_API_KEY=your-api-key-here
USE_RAG=true
VECTOR_DB_PATH=./vector_db/python_textbook_gemini_db_semantic
VECTOR_DB_EMBEDDING_MODEL=gemini
```

### 프로덕션 환경

두 가지 방식:

#### 1. 빌드 시 포함 (권장하지 않음)
- API 키가 실행 파일에 포함됨
- 보안 위험

#### 2. 첫 실행 시 입력 (권장)
- 사용자가 앱 첫 실행 시 API 키 입력
- `AppData` 또는 `~/.config`에 암호화하여 저장
- **현재 구현 필요**

#### 3. 환경 변수 사용
```bash
# Windows
set GEMINI_API_KEY=your-key
PopPins II.exe

# macOS/Linux
export GEMINI_API_KEY=your-key
./PopPins\ II.app/Contents/MacOS/PopPins\ II
```

---

## 크기 최적화

### 1. Frontend 최적화

#### Vite 설정 (`frontend/vite.config.ts`)
```typescript
export default defineConfig({
  build: {
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // 콘솔 로그 제거
      },
    },
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
        },
      },
    },
  },
})
```

### 2. Backend 최적화

#### 불필요한 패키지 제거
```bash
# requirements.txt에서 개발 전용 패키지 제거
# 예: pytest, black, mypy 등
```

#### Python 바이트코드 사전 컴파일
```bash
python -m compileall standalone/app
```

### 3. Tauri 설정

#### `tauri.conf.json` 최적화
```json
{
  "bundle": {
    "active": true,
    "targets": ["msi"],
    "resources": {
      "python": false,  // Python 런타임 포함 여부
      "vectordb": true  // 벡터 DB 포함
    }
  },
  "tauri": {
    "bundle": {
      "externalBin": []  // 외부 바이너리 최소화
    }
  }
}
```

### 4. 벡터 DB 압축

```bash
# FAISS 인덱스 압축
# 주의: 성능 저하 가능
```

---

## 자동 업데이트

### Tauri Updater 설정

#### 1. `tauri.conf.json` 설정
```json
{
  "updater": {
    "active": true,
    "endpoints": [
      "https://releases.your-domain.com/{{target}}/{{current_version}}"
    ],
    "dialog": true,
    "pubkey": "YOUR_PUBLIC_KEY"
  }
}
```

#### 2. 릴리스 서버 구성
- GitHub Releases 사용 권장
- 릴리스 생성 시 서명된 업데이트 파일 업로드

#### 3. 서명 키 생성
```bash
tauri signer generate
```

---

## CI/CD 자동화

### GitHub Actions 예시

`.github/workflows/release.yml`:
```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    permissions:
      contents: write
    strategy:
      fail-fast: false
      matrix:
        platform: [windows-latest, macos-latest, ubuntu-latest]

    runs-on: ${{ matrix.platform }}

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 18

      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies (Ubuntu)
        if: matrix.platform == 'ubuntu-latest'
        run: |
          sudo apt-get update
          sudo apt-get install -y libgtk-3-dev libwebkit2gtk-4.0-dev libappindicator3-dev

      - name: Build Frontend
        run: |
          cd frontend
          npm install
          npm run build

      - name: Setup Standalone
        run: |
          cd standalone
          python setup.py

      - name: Build Tauri
        uses: tauri-apps/tauri-action@v0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          projectPath: standalone/frontend
          tagName: ${{ github.ref_name }}
          releaseName: 'PopPins II ${{ github.ref_name }}'
          releaseBody: 'See CHANGELOG.md for details.'
          releaseDraft: true
          prerelease: false
```

---

## 배포 후 확인사항

### ✅ 테스트 항목

- [ ] 앱 설치 정상 작동
- [ ] 첫 실행 시 API 키 입력 (향후 구현)
- [ ] 백엔드 서버 자동 시작
- [ ] Frontend UI 정상 로드
- [ ] 코스 생성 기능
- [ ] 챕터 콘텐츠 생성
- [ ] 객관식 퀴즈 작동
- [ ] 주관식 AI 채점
- [ ] 데이터베이스 저장
- [ ] 앱 종료 시 백엔드도 함께 종료

### 📊 성능 확인

- [ ] 앱 시작 시간 < 5초
- [ ] 메모리 사용량 < 200MB
- [ ] 코스 생성 시간 < 30초
- [ ] UI 반응 속도 정상

---

## 트러블슈팅

### Windows Defender 경고
- 코드 서명이 없는 경우 발생
- 해결: Microsoft Developer 계정으로 코드 서명

### macOS Gatekeeper 차단
- 공증(Notarization)이 없는 경우 발생
- 해결: Apple Developer 계정으로 공증

### Linux 의존성 오류
- GTK, WebKit 라이브러리 누락
- 해결: 빌드 환경 준비 단계 참조

---

## 버전 관리

### 버전 번호 업데이트

1. `standalone/frontend/src-tauri/Cargo.toml`
```toml
[package]
version = "0.2.0"  # 업데이트
```

2. `standalone/frontend/src-tauri/tauri.conf.json`
```json
{
  "version": "0.2.0"  // 업데이트
}
```

3. Git 태그 생성
```bash
git tag v0.2.0
git push origin v0.2.0
```

---

## 배포 체크리스트

### 릴리스 전

- [ ] 모든 테스트 통과
- [ ] 버전 번호 업데이트
- [ ] CHANGELOG.md 작성
- [ ] 문서 최신화
- [ ] 빌드 성공 (3개 플랫폼)
- [ ] 설치 파일 동작 확인

### 릴리스 시

- [ ] GitHub Release 생성
- [ ] 릴리스 노트 작성
- [ ] 설치 파일 업로드
- [ ] 체크섬 파일 생성 및 업로드

### 릴리스 후

- [ ] 다운로드 링크 확인
- [ ] 사용자 피드백 모니터링
- [ ] 문제 발생 시 핫픽스 준비

---

**버전**: v2.1.0  
**최종 업데이트**: 2025-11-28
