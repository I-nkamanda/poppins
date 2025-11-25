📘 PRD – Python PDF 기반 RAG Tutor (PBL Generator Lite)

with 멘토링 피드백 반영 버전 (2025-11-17)

1. Product Overview
1.1 제품 목적

이번 Term Project의 거대한 목표(“AI 기반 PBL 생성 플랫폼” 

텀 프로젝트 제안_이진걸

) 중, 멘토링 세션에서 방향성을 다시 잡으며 아래로 스코프를 축소했다:

“파이썬 PDF 문서를 기반으로 문서 신뢰성을 확보한 RAG 시스템을 만들고,
초급 학습자를 위한 자습형 PBL 학습지를 자동 생성하는 최소 기능(MVP) 데모 구현”

즉, LMS 전체가 아니라
LMS에 ‘부착 가능한 PBL 모듈’을 만드는 프로젝트로 확정되었다.
(멘토링 회의: “프로젝트 범위를 LMS 내 PBL 모듈 개발로 한정”)

2. Mentoring Feedback Integration
2.1 스코프 정렬 (멘토 → 우리 팀)

멘토가 조언한 내용:

범위 좁히기 → LMS 전체 아키텍처 X / PBL 모듈만 개발

컨텐츠 신뢰도 확보 → 전문/PDF 컨텐츠를 벡터DB에 저장해 AI hallucination 방지

피드백 사이클 고려 → 활동기록·문제풀이·설문 기반의 학습 분석 구조 기획

GCP 기반 기술 환경 → Gen AI SDK, Vertex AI, 무료티어 적극 활용

이번 스프린트 목표는 데모 UI 포함한 MVP

위 내용을 모두 본 PRD에 반영함.

3. Target Users
🎯 Primary: 파이썬 초~중급 학습자

함수/반복문은 됨

클래스/Node/LinkedList를 배우고 싶어함
(워크플로우 자료 기반: “class는 어렴풋, Node/LinkedList 구현이 목표” 

[POP.PINS] 챗봇과의 유저 워크플로우 구상

)

🎯 Secondary

대학생/직장인/교사 등 PBL 실습지를 빠르게 얻고 싶은 사용자
(텀 프로젝트 제안서의 페르소나 3명과 일치함.) 

텀 프로젝트 제안_이진걸

4. User Scenario (최종 정제)

Term 프로젝트 제안서의 1~4단계 시나리오를 RAG 문서 기반 자습용으로 재해석했다.
(“학습자 입력 → 구체화 → 출력 → 학습” 흐름 반영) 

텀 프로젝트 제안_이진걸

시나리오 A — “LinkedList를 2시간 안에 이해하고 싶어요”

학습자 입력:

단순 연결 리스트를 자습으로 배우고 싶어요.


시스템 처리:

PDF에서 LinkedList 관련 단락 Top-K 검색

학습자 레벨 반영 (초급)

PBL 미션(Day1~Day5 기반 미니 버전) 생성

워크플로우 PDF에서 사용한 구조 반영: “개념 → 실습 → 순회 → 삽입/삭제 → 원형리스트” 

[POP.PINS] 챗봇과의 유저 워크플로우 구상

출력:

개념 요약

PDF 기반 인용

예제 코드

미니 PBL 세트 (3~5개 미션)

시나리오 B — “람다 함수 핵심 요약 + 작은 실습 문제 줘”

질문

RAG 검색

LLM이 PDF 근거 기반으로 정확한 설명 + 1~2개 실습(PBL) 출력

5. Key Features (멘토링 피드백 반영)
5.1 문서 기반 컨텐츠 저장소 (전문 컨텐츠 우선)

멘토 요청사항:

“AI에만 의존하는 게 아니라, 전문 컨텐츠를 별도 저장해야 한다.”

구현 내용:

PDF 텍스트 → Chunking → Embedding → Qdrant 저장

문서 기반 정확성 확보

AI는 문서 제공 + PBL 변환 역할만 함

외부 컨텐츠도 확장 가능 (MD, HTML, YouTube Transcript 등)

5.2 RAG (Retrieval-Augmented Generation)

구성:

PDF Loader

Recursive Splitter

SentenceTransformer Embedding

Qdrant VectorDB

Retriever

LLM(Gemini 또는 GPT-5.1)

➕ 멘토가 제공한 Databricks 무료 RAG 예제 코드와 흐름을 벤치마킹함.

5.3 자습형 PBL 생성기

PBL 생성 규칙:

개념 → 실습 → 평가 → 복습 문제

난이도 조절 (학습자 입력 기반)

워크플로우 PDF에서 실제 Day1~5 PBL Breakdown 기반으로 정형화된 템플릿 사용 

[POP.PINS] 챗봇과의 유저 워크플로우 구상

Term 프로젝트 제안서의 “JSON 기반 Output Format” 아이디어도 병합함. 

텀 프로젝트 제안_이진걸

5.4 LMS 연동 가능한 모듈화된 구조

멘토가 제안한 방향성:

“LMS 전체가 아닌 PBL 모듈만 개발하자.”

따라서:

API-first 구조

FastAPI 기반 REST

/ask

/index

/history (optional)

LMS 프론트엔드에서 불러다 쓰기 쉬운 형태(JSON)

5.5 Feedback Cycle (설계 수준 포함)

멘토 요청:

“학습 기록 → 분석 → 개선 루프를 반드시 고려해라.”

MVP 범위에서는 기획까지만 하고:

활동 로그 저장

질문/응답 히스토리

PBL 수행 여부

간단한 Difficulty 조정 모델
→ 차후 LLM prompting에 반영되는 구조 설계.

5.6 GCP 기반 기술 환경

멘토 지원 항목:

Vertex AI

Gen AI SDK

Google Cloud 무료 옵션
→ 시스템 아키텍처에 반영

RAG 파이프라인:

GCS -> Vertex AI Embedding -> Qdrant (Compute Engine or Docker)
FastAPI -> Vertex AI / Gemini API -> UI

6. System Architecture

Term 프로젝트 제안서의 “Input Layer – AI Generator – Output Layer” 아키텍처를 그대로 가져오되,
멘토 피드백 기반으로 컨텐츠 저장소 / 학습 분석 / LMS 연동을 추가했다.


텀 프로젝트 제안_이진걸

┌───────────────────────────┐
│           UI               │
│ (MVP: 최소 페이지 1~2개)   │
└────────────┬──────────────┘
             │ Query
┌────────────▼──────────────┐
│         FastAPI            │
│  /ask /index /history      │
└───────┬───────┬───────────┘
        │       │
        │       ├─────────── Activity Logs (Feedback Cycle)
        │
        ▼
┌───────────────────────────┐
│ RAG Engine                │
│ PDF Loader → Chunker      │
│ Embedding → Qdrant Search │
└────────────┬──────────────┘
             │ context
             ▼
┌───────────────────────────┐
│  LLM (Gemini / GPT)       │
│  Concept + PBL Generator  │
└────────────┬──────────────┘
             │
             ▼
┌───────────────────────────┐
│ Output: 개념+실습(PBL)     │
└───────────────────────────┘

7. MVP Scope

멘토가 강조한 “이번 스프린트 내 완성해야 할 최소 범위”:

✔ 1) PDF → Qdrant 인덱싱
✔ 2) /ask → 자습서 + PBL 출력
✔ 3) 최소 UI (검색창 + 답변창)
✔ 4) 기획된 Feedback Cycle 구조 포함
8. Timeline (멘토링 일정 반영)
🔹 11/17 멘토링 → 방향성 정립
🔹 11/18~19: 기술 환경 설정 (GCP / VectorDB / FastAPI)
🔹 11/19(수) 온라인 멘토링 (19:30) — 1차 데모 공유
🔹 11/20~22: PBL Generator 품질 개선
🔹 11/23(일) 오프라인 멘토링 — PBL + UI 최종 점검
🔹 11/24~28: 발표 준비 및 시연용 WOW 포인트 적용

(제안서 참고: “발표 시 감성 → 작동 → 비전 3단 구조” 

텀 프로젝트 제안_이진걸

)

9. Success Metrics

RAG 기반 답변 정확도: 문서 근거 포함 응답률 90% 이상

PBL 미션 품질:

학습자 난이도 적합성

실습 가능성

시연 품질:

“입력 → 자동 자습서 생성” 흐름이 30초 내 재현

시스템 안정성:

잘못된 입력에도 FastAPI 오류 없는 응답

10. Risk & Mitigation
Risk	Mitigation
PDF 품질 저하	pdfminer fallback
LLM 환각	RAG 강제 + 문서 인용 포함
시간 부족	UI 최소화 + Backend 우선
GCP 비용	전부 무료 옵션(GCE-free-tier / Vertex Basic) 활용
11. Output Format (최종)
1) 개념 설명
[요약]
[예제 코드]
[문서 출처 기반 텍스트]

2) Mini PBL
1) 실습 1
2) 실습 2
3) 개념 확장 문제