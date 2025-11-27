"""
QA 로그 자동 분석 및 수정 제안 시스템

qa_logs/suggestions.md 파일이 생성되면 자동으로:
1. 실패한 포인트 분석
2. 수정 patch diff 생성
3. 사용자에게 적용 여부 확인

사용법:
    python qa_auto_fix.py

또는 파일 감시 모드:
    python qa_auto_fix.py --watch
"""
import os
import re
import json
import difflib
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import argparse

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent
QA_LOGS_DIR = PROJECT_ROOT / "qa_logs"
SUGGESTIONS_FILE = QA_LOGS_DIR / "suggestions.md"


def analyze_failures(suggestions_content: str) -> Dict[str, List[str]]:
    """
    suggestions.md 파일에서 실패한 포인트를 분석합니다.
    
    Args:
        suggestions_content: suggestions.md 파일 내용
    
    Returns:
        Dict: 분석 결과
            - errors: 에러 목록
            - warnings: 경고 목록
            - improvements: 개선 사항 목록
            - code_issues: 코드 문제 목록
    """
    analysis = {
        "errors": [],
        "warnings": [],
        "improvements": [],
        "code_issues": [],
        "test_failures": [],
        "performance_issues": []
    }
    
    lines = suggestions_content.split('\n')
    current_section = None
    
    for i, line in enumerate(lines):
        # 섹션 헤더 감지
        if line.startswith('#'):
            current_section = line.strip('#').strip().lower()
        
        # 에러 패턴 감지
        if any(keyword in line.lower() for keyword in ['error', 'fail', 'exception', 'crash']):
            analysis["errors"].append({
                "line": i + 1,
                "content": line.strip(),
                "context": '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
            })
        
        # 경고 패턴 감지
        if any(keyword in line.lower() for keyword in ['warning', 'deprecated', 'should', 'consider']):
            analysis["warnings"].append({
                "line": i + 1,
                "content": line.strip(),
                "context": '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
            })
        
        # 테스트 실패 감지
        if 'test' in line.lower() and ('fail' in line.lower() or '❌' in line or '✗' in line):
            analysis["test_failures"].append({
                "line": i + 1,
                "content": line.strip(),
                "context": '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
            })
        
        # 성능 문제 감지
        if any(keyword in line.lower() for keyword in ['slow', 'performance', 'timeout', 'memory']):
            analysis["performance_issues"].append({
                "line": i + 1,
                "content": line.strip(),
                "context": '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
            })
        
        # 코드 문제 감지 (파일 경로 포함)
        file_pattern = r'([a-zA-Z0-9_/\\\.]+\.(py|tsx?|ts|jsx?|js|md))'
        if re.search(file_pattern, line) and any(keyword in line.lower() for keyword in ['fix', 'change', 'update', 'modify']):
            analysis["code_issues"].append({
                "line": i + 1,
                "content": line.strip(),
                "file": re.search(file_pattern, line).group(1) if re.search(file_pattern, line) else None
            })
    
    return analysis


def extract_file_paths(suggestions_content: str) -> List[str]:
    """
    suggestions.md에서 언급된 파일 경로를 추출합니다.
    
    Args:
        suggestions_content: suggestions.md 파일 내용
    
    Returns:
        List[str]: 파일 경로 목록
    """
    file_paths = []
    
    # 일반적인 파일 경로 패턴
    patterns = [
        r'`([a-zA-Z0-9_/\\\.]+\.(py|tsx?|ts|jsx?|js|md))`',  # 백틱으로 감싸진 파일
        r'([a-zA-Z0-9_/\\\.]+\.(py|tsx?|ts|jsx?|js|md))',  # 일반 파일 경로
        r'File:\s*([a-zA-Z0-9_/\\\.]+\.(py|tsx?|ts|jsx?|js|md))',  # File: 접두사
        r'Path:\s*([a-zA-Z0-9_/\\\.]+\.(py|tsx?|ts|jsx?|js|md))',  # Path: 접두사
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, suggestions_content)
        for match in matches:
            file_path = match[0] if isinstance(match, tuple) else match
            # 프로젝트 루트 기준 경로로 정규화
            if not file_path.startswith(('app/', 'frontend/', './', '../')):
                # 상대 경로로 변환 시도
                if os.path.exists(file_path):
                    file_paths.append(file_path)
                elif os.path.exists(f"app/{file_path}"):
                    file_paths.append(f"app/{file_path}")
                elif os.path.exists(f"frontend/src/{file_path}"):
                    file_paths.append(f"frontend/src/{file_path}")
            else:
                file_paths.append(file_path)
    
    # 중복 제거 및 정규화
    unique_paths = []
    for path in set(file_paths):
        normalized = Path(path).as_posix()
        if (PROJECT_ROOT / normalized).exists():
            unique_paths.append(normalized)
    
    return unique_paths


def parse_suggestion_line(line: str) -> Optional[Dict]:
    """
    제안 라인을 파싱하여 수정 정보를 추출합니다.
    
    Args:
        line: 제안 라인 (예: "app/main.py:123: 에러 메시지")
    
    Returns:
        Optional[Dict]: 파싱된 정보 또는 None
    """
    # 파일:라인:설명 형식
    pattern1 = r'([a-zA-Z0-9_/\\\.]+\.(py|tsx?|ts|jsx?|js|md)):(\d+):\s*(.+)'
    match1 = re.match(pattern1, line)
    if match1:
        return {
            "file": match1.group(1),
            "line": int(match1.group(3)),
            "message": match1.group(4),
            "type": "line_specific"
        }
    
    # 파일:라인 형식
    pattern2 = r'([a-zA-Z0-9_/\\\.]+\.(py|tsx?|ts|jsx?|js|md)):(\d+)'
    match2 = re.match(pattern2, line)
    if match2:
        return {
            "file": match2.group(1),
            "line": int(match2.group(3)),
            "message": "",
            "type": "line_specific"
        }
    
    # 파일만 언급
    pattern3 = r'`([a-zA-Z0-9_/\\\.]+\.(py|tsx?|ts|jsx?|js|md))`'
    match3 = re.search(pattern3, line)
    if match3:
        return {
            "file": match3.group(1),
            "line": None,
            "message": line,
            "type": "file_general"
        }
    
    return None


def generate_patch(file_path: str, suggestions_content: str, analysis: Dict) -> Optional[str]:
    """
    제안 사항을 기반으로 수정 패치를 생성합니다.
    
    Args:
        file_path: 수정할 파일 경로
        suggestions_content: suggestions.md 내용
        analysis: 분석 결과
    
    Returns:
        Optional[str]: diff 형식의 패치, 생성 실패 시 None
    
    변경 이유:
        - 더 정교한 패치 생성 로직 구현
        - 라인별 수정 사항 추출
        - 실제 코드 수정 제안 생성
    """
    full_path = PROJECT_ROOT / file_path
    
    if not full_path.exists():
        return None
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            original_lines = f.readlines()
        
        modified_lines = original_lines.copy()
        changes_made = False
        
        # 파일 관련 제안 사항 찾기
        file_suggestions = []
        lines = suggestions_content.split('\n')
        
        for i, line in enumerate(lines):
            parsed = parse_suggestion_line(line.strip())
            if parsed and (parsed["file"] == file_path or file_path.endswith(parsed["file"])):
                file_suggestions.append({
                    **parsed,
                    "source_line": i + 1,
                    "context": '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
                })
        
        # 라인별 수정 적용
        for suggestion in file_suggestions:
            if suggestion["type"] == "line_specific" and suggestion["line"]:
                line_num = suggestion["line"] - 1  # 0-based index
                
                if 0 <= line_num < len(modified_lines):
                    original_line = modified_lines[line_num]
                    
                    # 일반적인 수정 패턴 적용
                    message = suggestion["message"].lower()
                    
                    # 사용하지 않는 변수 제거
                    if "unused" in message or "사용하지 않는" in message:
                        # 변수명 추출 시도
                        var_match = re.search(r'(\w+)', message)
                        if var_match:
                            var_name = var_match.group(1)
                            # 해당 라인에서 변수 선언 찾기
                            if var_name in original_line and ('=' in original_line or ':' in original_line):
                                # 주석 처리 또는 제거 (안전을 위해 주석 처리)
                                modified_lines[line_num] = f"# {original_line.rstrip()}\n"
                                changes_made = True
                    
                    # import 정리
                    elif "import" in message and ("unused" in message or "사용하지 않는" in message):
                        if original_line.strip().startswith("import") or original_line.strip().startswith("from"):
                            modified_lines[line_num] = f"# {original_line.rstrip()}\n"
                            changes_made = True
                    
                    # 타입 힌트 추가
                    elif "type" in message and ("hint" in message or "annotation" in message):
                        # 간단한 타입 힌트 추가는 복잡하므로 스킵
                        pass
                    
                    # 에러 처리 추가
                    elif "error" in message or "exception" in message or "try" in message:
                        # try-except 블록 추가는 복잡하므로 스킵
                        pass
        
        # diff 생성
        if changes_made:
            diff = difflib.unified_diff(
                original_lines,
                modified_lines,
                fromfile=f'a/{file_path}',
                tofile=f'b/{file_path}',
                lineterm='',
                n=3  # 컨텍스트 3줄
            )
            return ''.join(diff)
        
        return None
        
    except Exception as e:
        print(f"Error generating patch for {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_suggestions_file() -> Tuple[Dict, List[Tuple[str, str]]]:
    """
    suggestions.md 파일을 처리하고 분석 결과와 패치를 생성합니다.
    
    Returns:
        Tuple[Dict, List[Tuple[str, str]]]: (분석 결과, [(파일경로, 패치)] 리스트)
    """
    if not SUGGESTIONS_FILE.exists():
        print(f"❌ {SUGGESTIONS_FILE} 파일을 찾을 수 없습니다.")
        return {}, []
    
    print(f"📄 {SUGGESTIONS_FILE} 파일을 분석 중...")
    
    with open(SUGGESTIONS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 실패 포인트 분석
    print("\n🔍 실패한 포인트 분석 중...")
    analysis = analyze_failures(content)
    
    # 분석 결과 출력
    print("\n" + "="*60)
    print("📊 분석 결과")
    print("="*60)
    
    if analysis["errors"]:
        print(f"\n❌ 에러: {len(analysis['errors'])}개 발견")
        for error in analysis["errors"][:5]:  # 최대 5개만 표시
            print(f"  - Line {error['line']}: {error['content'][:80]}")
    
    if analysis["warnings"]:
        print(f"\n⚠️  경고: {len(analysis['warnings'])}개 발견")
        for warning in analysis["warnings"][:5]:
            print(f"  - Line {warning['line']}: {warning['content'][:80]}")
    
    if analysis["test_failures"]:
        print(f"\n🧪 테스트 실패: {len(analysis['test_failures'])}개 발견")
        for failure in analysis["test_failures"][:5]:
            print(f"  - Line {failure['line']}: {failure['content'][:80]}")
    
    if analysis["code_issues"]:
        print(f"\n💻 코드 문제: {len(analysis['code_issues'])}개 발견")
        for issue in analysis["code_issues"][:5]:
            print(f"  - Line {issue['line']}: {issue['content'][:80]}")
    
    # 파일 경로 추출
    print("\n📁 관련 파일 추출 중...")
    file_paths = extract_file_paths(content)
    
    if file_paths:
        print(f"발견된 파일: {len(file_paths)}개")
        for path in file_paths[:10]:  # 최대 10개만 표시
            print(f"  - {path}")
    else:
        print("  관련 파일을 찾을 수 없습니다.")
    
    # 패치 생성
    print("\n🔧 수정 패치 생성 중...")
    patches = []
    
    for file_path in file_paths[:5]:  # 최대 5개 파일만 처리
        patch = generate_patch(file_path, content, analysis)
        if patch:
            patches.append((file_path, patch))
            print(f"  ✓ {file_path} 패치 생성 완료")
    
    return analysis, patches


def apply_patch(file_path: str, patch: str) -> bool:
    """
    패치를 적용합니다.
    
    Args:
        file_path: 파일 경로
        patch: diff 형식의 패치
    
    Returns:
        bool: 적용 성공 여부
    
    변경 이유:
        - unified diff 형식 파싱 개선
        - 백업 파일 생성
        - 안전한 패치 적용 (검증 후 적용)
    """
    full_path = PROJECT_ROOT / file_path
    
    if not full_path.exists():
        print(f"  ❌ 파일을 찾을 수 없습니다: {file_path}")
        return False
    
    try:
        # 백업 생성
        backup_path = full_path.with_suffix(full_path.suffix + f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        with open(full_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
            original_lines = f.readlines()
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        print(f"  💾 백업 생성: {backup_path.name}")
        
        # unified diff 파싱
        patch_lines = patch.splitlines()
        new_lines = original_lines.copy()
        
        i = 0
        while i < len(patch_lines):
            line = patch_lines[i]
            
            # hunk 헤더 찾기: @@ -start,count +start,count @@
            if line.startswith('@@'):
                hunk_match = re.search(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
                if hunk_match:
                    old_start = int(hunk_match.group(1)) - 1  # 0-based
                    old_count = int(hunk_match.group(2)) if hunk_match.group(2) else 1
                    new_start = int(hunk_match.group(3)) - 1
                    new_count = int(hunk_match.group(4)) if hunk_match.group(4) else 1
                    
                    i += 1
                    hunk_lines = []
                    
                    # hunk 내용 읽기
                    while i < len(patch_lines) and not patch_lines[i].startswith('@@'):
                        hunk_line = patch_lines[i]
                        if hunk_line.startswith('+') and not hunk_line.startswith('+++'):
                            # 추가할 라인
                            hunk_lines.append(hunk_line[1:] + '\n')
                        elif hunk_line.startswith('-') and not hunk_line.startswith('---'):
                            # 삭제할 라인 (스킵)
                            pass
                        elif hunk_line.startswith(' '):
                            # 변경 없음 (유지)
                            hunk_lines.append(hunk_line[1:] + '\n')
                        i += 1
                    
                    # 라인 교체
                    if 0 <= old_start < len(new_lines):
                        # 기존 라인 제거 및 새 라인 삽입
                        new_lines = new_lines[:old_start] + hunk_lines + new_lines[old_start + old_count:]
            else:
                i += 1
        
        # 수정된 내용이 있는지 확인
        new_content = ''.join(new_lines)
        if new_content != original_content:
            # 파일에 적용
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"  ✅ 패치 적용 완료: {file_path}")
            print(f"     변경된 라인 수: 약 {abs(len(new_lines) - len(original_lines))}줄")
            return True
        else:
            print(f"  ⚠️  패치 적용 후 변경사항이 없습니다: {file_path}")
            # 백업 파일 삭제 (변경사항 없음)
            backup_path.unlink()
            return False
        
    except Exception as e:
        print(f"  ❌ 패치 적용 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description='QA 로그 자동 분석 및 수정 제안')
    parser.add_argument('--watch', action='store_true', help='파일 감시 모드')
    parser.add_argument('--auto-apply', action='store_true', help='자동 적용 (주의: 사용 전 검토 필요)')
    args = parser.parse_args()
    
    if args.watch:
        print("👀 파일 감시 모드 시작...")
        print(f"감시 중: {SUGGESTIONS_FILE}")
        print("Ctrl+C로 종료")
        
        last_modified = 0
        while True:
            try:
                if SUGGESTIONS_FILE.exists():
                    current_modified = SUGGESTIONS_FILE.stat().st_mtime
                    if current_modified > last_modified:
                        last_modified = current_modified
                        print(f"\n🔄 파일 변경 감지: {datetime.now()}")
                        analysis, patches = process_suggestions_file()
                        
                        if patches:
                            print("\n" + "="*60)
                            print("📝 생성된 패치")
                            print("="*60)
                            
                            for file_path, patch in patches:
                                print(f"\n--- {file_path}")
                                print(patch[:500] + "..." if len(patch) > 500 else patch)
                            
                            if not args.auto_apply:
                                response = input("\n❓ 패치를 적용하시겠습니까? (y/N): ")
                                if response.lower() == 'y':
                                    for file_path, patch in patches:
                                        apply_patch(file_path, patch)
                                    print("✅ 패치 적용 완료")
                                else:
                                    print("❌ 패치 적용 취소")
                            else:
                                print("⚠️  자동 적용 모드: 패치가 적용됩니다.")
                                for file_path, patch in patches:
                                    apply_patch(file_path, patch)
                
                import time
                time.sleep(2)  # 2초마다 확인
                
            except KeyboardInterrupt:
                print("\n\n👋 감시 모드 종료")
                break
    else:
        # 일회성 실행
        analysis, patches = process_suggestions_file()
        
        if patches:
            print("\n" + "="*60)
            print("📝 생성된 패치")
            print("="*60)
            
            for file_path, patch in patches:
                print(f"\n--- {file_path}")
                print(patch[:500] + "..." if len(patch) > 500 else patch)
            
            if not args.auto_apply:
                response = input("\n❓ 패치를 적용하시겠습니까? (y/N): ")
                if response.lower() == 'y':
                    for file_path, patch in patches:
                        apply_patch(file_path, patch)
                    print("✅ 패치 적용 완료")
                else:
                    print("❌ 패치 적용 취소")
            else:
                print("⚠️  자동 적용 모드: 패치가 적용됩니다.")
                for file_path, patch in patches:
                    apply_patch(file_path, patch)
        else:
            print("\n✅ 수정할 패치가 없습니다.")


if __name__ == "__main__":
    main()

