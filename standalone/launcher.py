"""
PopPins II - Standalone Desktop Application Launcher
FastAPI + PyWebview 기반 데스크탑 앱

실행 방법:
    python launcher.py
"""

import webview
import uvicorn
import threading
import time
import sys
import os
from pathlib import Path

# 프로젝트 루트 경로를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def start_backend():
    """FastAPI 백엔드 서버를 백그라운드에서 시작"""
    try:
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8001,
            log_level="error",  # 로그 출력 최소화
            access_log=False    # 액세스 로그 비활성화
        )
    except Exception as e:
        print(f"❌ 백엔드 서버 시작 실패: {e}")
        sys.exit(1)

def check_server_ready(url="http://127.0.0.1:8001/health", timeout=10):
    """서버가 준비될 때까지 대기"""
    import requests
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                print("✅ 백엔드 서버 준비 완료")
                return True
        except:
            time.sleep(0.5)
    
    print("⚠️ 서버 응답 대기 시간 초과")
    return False

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🚀 PopPins II - AI 학습 자료 생성기")
    print("=" * 60)
    
    # 1. 백엔드 서버 시작 (백그라운드 스레드)
    print("⏳ 백엔드 서버 시작 중...")
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # 2. 서버 준비 대기
    if not check_server_ready():
        print("❌ 서버를 시작할 수 없습니다.")
        return
    
    # 3. WebView 창 열기
    print("📱 애플리케이션 창 열기...")
    try:
        webview.create_window(
            title="PopPins II - AI 학습 자료 생성기",
            url="http://127.0.0.1:8001",
            width=1400,
            height=900,
            resizable=True,
            min_size=(1024, 768)
        )
        webview.start()
    except Exception as e:
        print(f"❌ WebView 실행 실패: {e}")
        print("💡 pywebview가 설치되어 있는지 확인하세요: pip install pywebview")
        return
    
    print("👋 애플리케이션이 종료되었습니다.")

if __name__ == "__main__":
    main()
