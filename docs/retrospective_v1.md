# Retrospective v1 — Main Branch (Workflow 기반 NL2SQL)

## 1. 프로젝트 개요

- **기간**: 2026-04-08 ~ 2026-04-09
- **목표**: 공적 DB(USAspending)에 대한 NL2SQL 시스템 구축 + 자동화 평가 루프
- **결과**: 50개 smoke test 기준 39/50 (78%)
- **아키텍처**: IR 기반 workflow 파이프라인 + OpenAI gpt-4o-mini

## 2. 완료된 작업

### M0 (Foundation) — 완료
- DuckDB in-memory bootstrap, CSV loader, schema inspector, query executor
- pyproject.toml, config/slice.yaml, .env 설정
- USAspending 데이터 3개 agency 다운로드 (HHS, NASA, DHS)

### M1 (Evaluation) — 부분 완료
- 228개 eval case (JSONL), 6개 카테고리, core/extended 티어
- result-set comparison (tolerance, behavior routing)
- scorer (positive accuracy, abstain F1, risky rate, weighted total)
- score_runner CLI + score.sh
- gold SQL: 20 easy + 20 hard = 40개

### M2 (Semantic Interpretation) — 부분 완료
- IR dataclass (QuestionIR)
- 5개 semantic 모듈: entity_resolver, metric_interpreter, time_interpreter, scope_interpreter, ambiguity_detector
- config 기반 metadata: agency_aliases.yaml, metric_dictionary.yaml, glossary.yaml
- pipeline.py: IR 기반으로 재구축

### AC Gate — 완료
- architecture_check.py (AC-1 ~ AC-5)
- score.sh에 연동

### 문서
- program.md, wbs_v0.2.md, CONTRIBUTING.md, evaluation_framework.md, ssot_guide.md
- troubleshooting.md (architecture compliance 교훈)
- improvement_log.md (시도 이력)

## 3. 미완료 작업

- M1: paraphrase expansion runner, temporal fuzz runner, hard regression set 잠금
- M3: validation & repair loop
- M4: policy layer (clarify/abstain 정교화)
- DoD, GSA 데이터 미다운로드 (너무 큼)
- 228개 full eval 미실행

## 4. 점수 이력

| 시점 | 점수 | 비고 |
|---|---|---|
| baseline (stub) | 0.100 | pipeline 없음 |
| 첫 pipeline (20개) | 17/20 (85%) | raw question → LLM |
| 프롬프트 패치 | 20/20 (100%) | agency alias + count rule |
| 패치 revert + IR 재구축 | 16/20 (80%) | 구조적으로 올바른 접근 |
| config 수정 (aggregation keywords) | 19/20 (95%) | AC 전부 PASS |
| 50개 확장 baseline | 36/50 (72%) | hard case 추가 |
| glossary + scope hints | 39/50 (78%) | 최종 |

## 5. 핵심 교훈

### 5.1 평가는 결과 + 과정 둘 다 필요
- 결과만 평가하면 agent가 프롬프트 패치(shortcut)를 선택함
- AC gate로 구조 정합성을 강제해야 올바른 접근을 유도

### 5.2 문제 규모에 비례한 솔루션
- 테이블 1개, 컬럼 14개에 5개 semantic 모듈은 오버엔지니어링
- "비례 원칙" — 문제 복잡도를 먼저 파악하고 솔루션 규모를 결정

### 5.3 사전 검증 필수
- USAspending API 제약 (1년 제한, timeout)을 구현 전에 확인했어야 함
- CSV 컬럼명을 코딩 전에 확인했어야 함
- Gold SQL을 실제 데이터에서 실행 검증했어야 함

### 5.4 Workflow vs Agent 아키텍처
- 고정 파이프라인(workflow)은 유연성이 부족
- 테이블 1개에서도 질문 유형마다 다른 처리가 필요 (list vs aggregate vs count)
- Agent가 도구를 선택적으로 사용하는 구조가 더 적합
- M3(검증), M4(정책)이 별도 모듈이 아니라 agent 행동으로 자연스럽게 해결

### 5.5 사람 개입 최소화 실패 원인
- agent가 매 단계마다 확인을 구함 → program.md에 자율 판단 기준이 불충분
- 잘못된 방향(프롬프트 패치)을 사람이 잡음 → 자동 검증(AC gate)이 늦게 도입됨
- 데이터/API 이슈를 사람이 해결 → 사전 조사 단계가 없었음

### 5.6 컨텍스트 관리
- 긴 세션에서 이전 결정이 흐려짐
- commit 메시지에 맥락을 기록하는 정책은 좋았음
- memory 시스템을 활용하지 않음 → 다음에는 핵심 결정을 memory에 저장

## 6. 다음 브랜치 (agent-bird)를 위한 권고사항

### 6.1 아키텍처
- **Agent 기반**: OpenAI function calling으로 도구 선택형 파이프라인
- **BIRD benchmark**: 20-50 테이블, gold SQL 포함, NL2SQL 표준
- **Retrieval 필수**: 다수 테이블 → schema retrieval이 핵심 도구

### 6.2 평가
- score.sh + AC gate 구조는 재활용
- BIRD의 gold SQL을 그대로 사용 (직접 작성 불필요)
- execution accuracy + exact match 두 메트릭 병행

### 6.3 개발 프로세스
- harness 기반: team.toml에 agent 역할 정의
- 사전 검증: DB 스키마, 데이터 크기, API 제약을 먼저 확인
- 비례 원칙: 문제 복잡도 분석 → 솔루션 규모 결정
- doc-code 동기화: 행동 변경 commit에 doc 업데이트 필수

### 6.4 사람 개입 경계
사람이 할 것:
- BIRD DB 선택 및 데이터 준비
- 비용 한도 설정
- 아키텍처 수준 의사결정 승인

Agent가 할 것:
- 도구 구현 및 테스트
- smoke test / score.sh 실행
- 성능 개선 루프 (시도 → 평가 → keep/revert)
- improvement_log 기록
- doc 업데이트

### 6.5 재활용 가능한 코드/구조
- `src/eval/` — scorer, result_compare, architecture_check
- `score.sh` — AC gate + score 구조
- `docs/improvement_log.md` — 시도 이력 구조
- `docs/troubleshooting.md` — 교훈 기록 구조
- `CONTRIBUTING.md` — commit 메시지 맥락 정책
- `config/` 기반 메타데이터 관리 패턴

### 6.6 버려야 할 것
- 고정 workflow 파이프라인 (pipeline.py의 _build_ir → prompt_builder → LLM 순서)
- 5개 semantic 모듈 (agent가 도구로 대체)
- 단일 테이블 가정 (loader, schema_inspector는 다중 테이블용으로 재설계)
