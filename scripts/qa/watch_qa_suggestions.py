"""
QA suggestions.md 파일 감시 및 자동 처리 스크립트

qa_logs/suggestions.md 파일이 생성되거나 수정되면:
1. 실패한 포인트 자동 분석
2. 수정 patch diff 생성
3. 사용자에게 적용 여부 확인 요청

사용법:
    python watch_qa_suggestions.py

백그라운드 실행:
    python watch_qa_suggestions.py &
"""
import os
import sys
import time
from pathlib import Path
from datetime import datetime
import qa_auto_fix

PROJECT_ROOT = Path(__file__).parent
QA_LOGS_DIR = PROJECT_ROOT / "qa_logs"
SUGGESTIONS_FILE = QA_LOGS_DIR / "suggestions.md"


def watch_file():
    """파일 감시 및 자동 처리"""
    # qa_logs 디렉토리 생성
    QA_LOGS_DIR.mkdir(exist_ok=True)
    
    print("="*60)
    print("🔍 QA Suggestions 파일 감시 시작")
    print("="*60)
    print(f"감시 파일: {SUGGESTIONS_FILE}")
    print(f"프로젝트 루트: {PROJECT_ROOT}")
    print("\n파일이 생성되거나 수정되면 자동으로 분석합니다...")
    print("Ctrl+C로 종료\n")
    
    last_modified = 0
    file_exists = False
    
    try:
        while True:
            if SUGGESTIONS_FILE.exists():
                current_modified = SUGGESTIONS_FILE.stat().st_mtime
                
                # 파일이 새로 생성되었거나 수정된 경우
                if current_modified > last_modified:
                    last_modified = current_modified
                    
                    if not file_exists:
                        print(f"\n{'='*60}")
                        print(f"✅ 파일 생성 감지: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"{'='*60}\n")
                        file_exists = True
                    else:
                        print(f"\n{'='*60}")
                        print(f"🔄 파일 수정 감지: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"{'='*60}\n")
                    
                    # 자동 분석 및 패치 생성
                    try:
                        analysis, patches = qa_auto_fix.process_suggestions_file()
                        
                        if patches:
                            print("\n" + "="*60)
                            print("📝 생성된 패치 요약")
                            print("="*60)
                            
                            for file_path, patch in patches:
                                print(f"\n📄 파일: {file_path}")
                                print(f"   패치 라인 수: {len(patch.splitlines())}줄")
                                print(f"   패치 크기: {len(patch)} bytes")
                            
                            # 사용자 확인 요청
                            print("\n" + "="*60)
                            print("❓ 패치 적용 확인")
                            print("="*60)
                            
                            for file_path, patch in patches:
                                print(f"\n--- 패치 미리보기: {file_path} ---")
                                # 처음 30줄만 미리보기
                                preview_lines = patch.splitlines()[:30]
                                print('\n'.join(preview_lines))
                                if len(patch.splitlines()) > 30:
                                    print(f"\n... (총 {len(patch.splitlines())}줄 중 30줄만 표시)")
                            
                            response = input("\n❓ 위 패치들을 적용하시겠습니까? (y/N): ")
                            
                            if response.lower() == 'y':
                                print("\n🔧 패치 적용 중...")
                                for file_path, patch in patches:
                                    success = qa_auto_fix.apply_patch(file_path, patch)
                                    if success:
                                        print(f"  ✅ {file_path} 적용 완료")
                                    else:
                                        print(f"  ⚠️  {file_path} 적용 실패 (수동 확인 필요)")
                                print("\n✅ 모든 패치 적용 완료")
                            else:
                                print("\n❌ 패치 적용 취소됨")
                                print("💡 패치를 나중에 적용하려면 qa_auto_fix.py를 직접 실행하세요.")
                        else:
                            print("\n✅ 수정할 패치가 없습니다.")
                            print("💡 suggestions.md의 내용을 확인하고 수동으로 수정이 필요할 수 있습니다.")
                    
                    except Exception as e:
                        print(f"\n❌ 분석 중 오류 발생: {e}")
                        import traceback
                        traceback.print_exc()
                
                file_exists = True
            else:
                file_exists = False
            
            time.sleep(1)  # 1초마다 확인
            
    except KeyboardInterrupt:
        print("\n\n👋 파일 감시 종료")
        sys.exit(0)


if __name__ == "__main__":
    watch_file()


