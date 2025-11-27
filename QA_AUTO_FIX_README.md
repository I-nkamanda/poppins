# QA 자동 수정 시스템

`qa_logs/suggestions.md` 파일이 생성되거나 수정되면 자동으로 다음을 수행합니다:

1. ✅ **실패한 포인트 분석**
2. ✅ **수정 patch diff 생성**
3. ✅ **"적용할까?" 확인 요청**

---

## 🚀 빠른 시작

### 방법 1: 파일 감시 모드 (권장)

```bash
python watch_qa_suggestions.py
```

이 명령을 실행하면 `qa_logs/suggestions.md` 파일을 감시하며, 파일이 생성되거나 수정되면 자동으로 분석합니다.

### 방법 2: 일회성 실행

```bash
python qa_auto_fix.py
```

현재 `suggestions.md` 파일을 분석하고 패치를 생성합니다.

---

## 📋 작동 방식

### 1. 파일 감지
- `qa_logs/suggestions.md` 파일이 생성되거나 수정되면 자동 감지
- 1초마다 파일 변경 여부 확인

### 2. 실패 포인트 분석
다음 항목들을 자동으로 분석합니다:
- ❌ **에러**: error, fail, exception, crash 키워드
- ⚠️ **경고**: warning, deprecated, should, consider 키워드
- 🧪 **테스트 실패**: test + fail 조합
- ⚡ **성능 문제**: slow, performance, timeout, memory 키워드
- 💻 **코드 문제**: 파일 경로 + fix/change/update 키워드

### 3. 패치 생성
- suggestions.md에서 언급된 파일 경로 자동 추출
- 각 파일에 대한 수정 패치 생성 (unified diff 형식)
- 다음 패턴 자동 수정:
  - 사용하지 않는 변수/import 주석 처리
  - 라인별 수정 사항 적용

### 4. 사용자 확인
- 생성된 패치를 미리보기로 표시
- 사용자에게 적용 여부 확인 요청
- 적용 시 자동으로 백업 파일 생성

---

## 📝 suggestions.md 형식 예시

파일은 다음과 같은 형식으로 작성할 수 있습니다:

```markdown
# 코드 품질 개선 제안

## 에러
- `app/main.py:123`: 함수에서 예외 처리가 누락됨
- `frontend/src/App.tsx:45`: 사용하지 않는 변수 `navigate`

## 경고
- `app/services/generator.py:78`: deprecated 함수 사용

## 테스트 실패
- `tests/test_api.py:25`: test_generate_course 실패

## 개선 사항
- `app/utils/errors.py`: 중복 코드 제거 필요
- 타입 힌트 추가 필요
```

### 파일 경로 형식

다음 형식으로 파일을 언급하면 자동으로 인식됩니다:
- `` `app/main.py` ``
- `app/main.py:123`
- `app/main.py:123: 에러 메시지`
- `File: app/main.py`
- `Path: frontend/src/App.tsx`

---

## 🔧 생성된 파일

### qa_auto_fix.py
- 메인 분석 및 패치 생성 모듈
- `process_suggestions_file()`: 파일 분석 및 패치 생성
- `analyze_failures()`: 실패 포인트 분석
- `generate_patch()`: 패치 생성
- `apply_patch()`: 패치 적용

### watch_qa_suggestions.py
- 파일 감시 스크립트
- 파일 변경 감지 시 자동 처리
- 사용자 확인 요청

---

## 📊 출력 예시

```
============================================================
✅ 파일 생성 감지: 2025-11-27 14:00:00
============================================================

📄 qa_logs/suggestions.md 파일을 분석 중...
   파일 크기: 1234 bytes
   수정 시간: 2025-11-27 14:00:00

🔍 실패한 포인트 분석 중...

============================================================
📊 분석 결과 요약
============================================================

총 발견된 이슈: 5개

❌ 에러: 2개 발견
  - Line 10: error in app/main.py:123
  - Line 15: exception handling missing

⚠️  경고: 1개 발견
  - Line 20: unused variable 'navigate'

💻 코드 문제: 2개 발견
  - Line 25 (app/main.py): fix needed
  - Line 30 (frontend/src/App.tsx): update required

📁 관련 파일 추출 중...
발견된 파일: 2개
  ✓ app/main.py
  ✓ frontend/src/App.tsx

🔧 수정 패치 생성 중...
  ✅ app/main.py 패치 생성 완료 (15줄)
  ✅ frontend/src/App.tsx 패치 생성 완료 (8줄)

============================================================
📝 생성된 패치 요약
============================================================

📄 파일: app/main.py
   패치 라인 수: 15줄
   패치 크기: 456 bytes

--- 패치 미리보기: app/main.py ---
--- a/app/main.py
+++ b/app/main.py
@@ -120,7 +120,7 @@
     # 사용하지 않는 변수
-    navigate = useNavigate();
+    # navigate = useNavigate();
...

❓ 위 패치들을 적용하시겠습니까? (y/N):
```

---

## ⚙️ 고급 옵션

### 자동 적용 모드 (주의!)

```bash
python qa_auto_fix.py --auto-apply
```

⚠️ **주의**: 이 모드는 사용자 확인 없이 자동으로 패치를 적용합니다. 사용 전에 반드시 코드를 검토하세요.

### 파일 감시 + 자동 적용

```bash
python watch_qa_suggestions.py --auto-apply
```

---

## 🔒 안전 기능

1. **자동 백업**: 패치 적용 전 자동으로 `.backup` 파일 생성
2. **변경사항 검증**: 패치 적용 후 실제 변경사항 확인
3. **에러 복구**: 패치 적용 실패 시 원본 파일 유지
4. **사용자 확인**: 기본적으로 사용자 확인 후 적용

---

## 📌 주의사항

- 패치 적용 전에 항상 내용을 검토하세요
- 자동 생성된 패치는 수동 검증이 필요할 수 있습니다
- 복잡한 수정 사항은 수동으로 처리해야 할 수 있습니다
- 백업 파일은 `.backup.YYYYMMDD_HHMMSS` 형식으로 저장됩니다

---

## 🐛 문제 해결

### 문제: 파일이 감지되지 않아요

**해결**:
1. `qa_logs/` 디렉토리가 존재하는지 확인
2. 파일 경로가 정확한지 확인 (`qa_logs/suggestions.md`)
3. 파일 권한 확인

### 문제: 패치가 생성되지 않아요

**해결**:
1. suggestions.md에 파일 경로가 명시되어 있는지 확인
2. 파일 경로 형식이 올바른지 확인
3. 언급된 파일이 실제로 존재하는지 확인

### 문제: 패치 적용이 실패해요

**해결**:
1. 백업 파일 확인 (`.backup.*` 파일)
2. 수동으로 diff를 검토하여 적용
3. 파일 권한 확인

---

**작성일**: 2025-11-27  
**버전**: 1.0.0

