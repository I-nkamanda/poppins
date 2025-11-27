# QA 로그 디렉토리

이 디렉토리는 QA(품질 보증) 관련 로그와 제안 사항을 저장합니다.

## 파일 구조

- `suggestions.md`: 코드 품질 개선 제안 사항

## 자동 처리 시스템

`qa_logs/suggestions.md` 파일이 생성되거나 수정되면:

1. **자동 분석**: 실패한 포인트, 에러, 경고 등을 분석
2. **패치 생성**: 수정 사항을 diff 형식으로 생성
3. **확인 요청**: 사용자에게 패치 적용 여부 확인

## 사용법

### 파일 감시 모드 (권장)

```bash
python watch_qa_suggestions.py
```

이 명령을 실행하면 `suggestions.md` 파일을 감시하며, 파일이 생성되거나 수정되면 자동으로 분석합니다.

### 일회성 실행

```bash
python qa_auto_fix.py
```

현재 `suggestions.md` 파일을 분석하고 패치를 생성합니다.

## suggestions.md 형식

파일은 다음과 같은 형식으로 작성할 수 있습니다:

```markdown
# 코드 품질 개선 제안

## 에러
- `app/main.py:123`: 함수에서 예외 처리가 누락됨

## 경고
- `frontend/src/App.tsx:45`: 사용하지 않는 변수 `navigate`

## 개선 사항
- `app/services/generator.py`: 중복 코드 제거 필요
- 테스트 커버리지 향상 필요
```

## 주의사항

- 패치 적용 전에 항상 내용을 검토하세요
- 자동 생성된 패치는 수동 검증이 필요할 수 있습니다
- 백업 파일은 `.backup` 확장자로 저장됩니다

