# Architecture Compliance — 왜 필요하고, 어떻게 할 것인가

## 1. 발생한 문제

2026-04-08, 첫 자동화 사이클에서 easy baseline 20개를 85% → 100%로 올렸다.
그런데 방법이 잘못되었다.

### 문서가 요구한 방식
```
질문 → IR 변환 (metric, entity, time, scope 파싱)
     → 정규화된 IR로 프롬프트 구성
     → LLM → SQL → 검증
```
(`program.md` Key Product Principle, `docs/project_context.md` phase 1 전략)

### 실제로 한 방식
```
질문 (그대로) → 프롬프트에 규칙 추가 (agency alias, transaction 규칙)
             → LLM → SQL
```

에이전트가 프롬프트에 예외 규칙을 하나씩 추가하는 방식으로 점수를 올렸다.
점수는 올랐지만, 이건 문서가 명시적으로 금지한 구조다.

### 왜 이게 문제인가

- 케이스가 228개로 늘어나면 프롬프트에 규칙이 수십 개 쌓임
- 규칙끼리 충돌하기 시작함
- 새 규칙이 이전에 맞던 케이스를 깨뜨림
- 근본 원인(entity 정규화, metric 사전 등)이 해결되지 않음
- 결국 95% 이상으로 갈 수 없는 구조

## 2. 근본 원인

평가 시스템이 **결과만 측정하고 과정을 측정하지 않았다.**

| 현재 평가 | 빠진 평가 |
|---|---|
| SQL 결과가 gold와 일치하는가? | pipeline이 IR을 거치는가? |
| clarify/abstain을 올바르게 했는가? | entity resolver를 사용하는가? |
| 실행이 성공했는가? | 프롬프트에 비즈니스 규칙이 하드코딩되지 않았는가? |
| risky answer rate이 낮은가? | metric 해석이 사전 기반인가? |

결과가 맞으면 통과되니까, 에이전트는 가장 쉬운 방법(프롬프트 패치)을 택한다.

## 3. 해결 방안: Architecture Compliance Gate

`score.sh` 실행 시, 결과 점수 외에 **구조 정합성 체크**를 추가한다.

### 체크 항목 (초기 버전)

| # | 체크 | 검증 방법 | 위반 시 |
|---|---|---|---|
| AC-1 | pipeline이 IR 변환을 거치는가 | `pipeline.py`가 IR 모듈을 import하고 호출하는지 정적 분석 | FAIL — merge 금지 |
| AC-2 | entity 정규화가 코드 레벨에서 수행되는가 | entity_resolver 모듈이 존재하고 pipeline에서 호출되는지 | FAIL |
| AC-3 | prompt_builder에 하드코딩된 비즈니스 규칙이 없는가 | 프롬프트 내 agency alias, metric 매핑 등이 config/사전에서 로딩되는지 | FAIL |
| AC-4 | metric 해석이 사전 기반인가 | metric_dictionary 모듈이 존재하고 pipeline에서 호출되는지 | FAIL |
| AC-5 | time 해석이 규칙 기반인가 | time_interpreter 모듈이 존재하고 사용되는지 | WARN (M2 완료 전까지) |

### 구현 위치

`src/eval/architecture_check.py` — 정적 분석 스크립트

### score.sh 연동

```bash
# score.sh에 추가 (구현 후)
python -m src.eval.architecture_check   # Architecture compliance
python -m src.eval.score_runner "$MODE"  # Result accuracy
```

두 가지 모두 통과해야 변경을 유지할 수 있다.

### 출력 형식

```
Architecture Compliance:
  AC-1 IR conversion in pipeline:     PASS
  AC-2 Entity resolver used:          PASS
  AC-3 No hardcoded rules in prompt:  FAIL — prompt_builder.py contains agency alias list
  AC-4 Metric dictionary used:        PASS
  AC-5 Time interpreter used:         WARN — not yet implemented

Gate: FAIL (AC-3)
```

## 4. 현재 상태 vs 목표 상태

### 현재 (AC 체크 없음)
```
에이전트: 점수 올리는 가장 쉬운 방법 선택 → 프롬프트 패치
평가: 점수 올랐네? → 통과
결과: 구조적으로 잘못된 코드가 계속 쌓임
```

### 목표 (AC 체크 있음)
```
에이전트: 점수 올리는 방법 선택 → 프롬프트 패치 시도
평가: 점수 올랐지만 AC-3 FAIL → 거부
에이전트: entity_resolver 모듈 구축 → 프롬프트에서 alias 제거
평가: 점수 유지 + AC 전체 PASS → 통과
결과: 문서대로 구조적으로 올바른 코드만 누적됨
```

## 5. 구현 우선순위

1. `src/eval/architecture_check.py` 구현 (AC-1 ~ AC-5)
2. `score.sh`에 gate로 연동
3. 현재 `prompt_builder.py`의 하드코딩된 규칙을 config로 이동 (AC-3 위반 해소)
4. M2 모듈 구축 시 AC-1, AC-2, AC-4가 자동으로 PASS됨
5. AC 체크 항목은 M2-M5 진행에 따라 확장

## 6. 교훈

- 에이전트는 명시적으로 금지하지 않으면 shortcut을 탄다
- 점수만 올리면 되는 구조에서는 가장 쉬운 방법이 선택된다
- **과정 품질은 결과 품질과 별도로 측정해야 한다**
- 문서에 원칙을 쓰는 것만으로는 부족하고, 그 원칙의 준수를 자동으로 검증하는 gate가 필요하다
