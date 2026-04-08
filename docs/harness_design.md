# Harness 설계

## 1. 목표

이 harness의 목표는 에이전트를 병렬로 많이 돌리는 것이 아니다.
핵심 목표는 다음 세 가지다.

1. 작업 범위를 명확히 나눈다.
2. 각 변경을 score gate로 검증한다.
3. 작은 개선을 누적해 최종 정확도까지 끌고 간다.

## 2. 기본 원칙

- foundation 단계는 single-agent 우선
- retrieval / generation / verifier / policy는 ownership 분리
- merge는 항상 quick score 후 결정
- fan-out보다 fan-in discipline을 더 중요하게 본다

## 3. 권장 역할 분리

### foundation

책임:
- 디렉토리 구조
- DuckDB bootstrap
- loader
- config
- executor

### data-eval

책임:
- 300 hard case 관리
- paraphrase / fuzz 세트
- score 계산
- 리포트 출력

### semantics

책임:
- schema retrieval
- glossary retrieval
- metric dictionary
- time / scope / entity 해석
- IR 생성

### generator

책임:
- prompt pack
- IR -> SQL 생성
- answer rendering

### verifier

책임:
- schema validation
- join checks
- metric/time/scope checks
- repair loop

### policy

책임:
- ambiguity detection
- clarify / abstain routing
- uncertainty policy

### bench

책임:
- locked set evaluation
- latency measurement
- regression reporting

## 4. 병렬화 순서

권장 순서는 아래와 같다.

1. foundation
2. data-eval
3. semantics + generator
4. verifier + policy
5. bench

즉, 기초와 점수판이 없을 때는 멀티에이전트가 오히려 독이 된다.

## 5. merge gate

변경은 아래 순서로 다룬다.

1. 작은 변경 수행
2. `./score.sh --quick` 실행
3. 점수 유지/상승이면 keep
4. 점수 하락이면 revert
5. WBS 업데이트

## 6. 금지 패턴

- 한 번에 여러 책임 영역을 동시에 크게 수정
- 테스트를 약화해 점수만 올리기
- ambiguous question에도 무조건 답변하기
- SQL 문자열 exact match를 목표로 삼기

## 7. task prompt 예시

### semantics worker

```text
Build schema, glossary, metric, time, and entity interpretation.
Only modify src/semantics/** and related tests.
Do not change generator or verifier behavior in this task.
Run ./score.sh --quick after each small change.
```

### verifier worker

```text
Build semantic validation and repair checks.
Only modify src/verifier/** and related tests.
Focus on invalid schema references, metric mistakes, time-axis mistakes, and scope mistakes.
Run ./score.sh --quick after each small change.
```

### policy worker

```text
Improve clarify / abstain routing for ambiguous questions.
Only modify src/policy/** and related tests.
Optimize for lower risky-answer rate, not for answer volume.
Run ./score.sh --quick after each small change.
```

## 8. 좋은 harness의 기준

좋은 harness는 에이전트가 똑똑해서가 아니라,

- 다음 일이 무엇인지 분명하고
- 바꾸면 안 되는 것이 분명하고
- 좋아졌는지 나빠졌는지 점수로 확인되고
- 실패 시 작게 되돌릴 수 있는 구조

를 가질 때 작동한다.
