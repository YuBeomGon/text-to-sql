# 평가 체계 제안

## 1. 평가 철학

이 프로젝트에서 가장 중요한 것은 `SQL이 실행되는가`가 아니라 `결과 의미가 맞는가`다.

따라서 평가도 다음 원칙을 따른다.

- SQL string exact match를 메인 지표로 쓰지 않는다.
- result-set correctness를 메인 지표로 쓴다.
- negative case의 정답은 "거절" 또는 "질문 보강"일 수 있다.
- metric/time/scope/entity 오류를 분해해서 본다.
- quick score와 full score를 분리한다.

## 2. 핵심 지표

### 2.1 Positive result accuracy

positive 케이스에서 결과 집합이 정답과 일치하는 비율.

이 프로젝트의 메인 KPI다.

### 2.2 Negative abstain / clarify F1

negative 또는 ambiguous 케이스에서,

- 억지 SQL을 생성하지 않고
- 적절히 질문을 보강하거나
- 안전하게 거절하는지

를 측정한다.

### 2.3 Metric-definition accuracy

질문이 요구한 metric을 맞게 해석했는지 본다.

예:

- award amount
- obligation
- outlay
- transaction count
- award count

### 2.4 Time-axis accuracy

시간 해석 정확도.

예:

- fiscal year vs calendar year
- half / quarter 해석
- action date vs award date
- relative period anchoring

### 2.5 Scope/state accuracy

질문의 범위를 맞게 해석했는지 본다.

예:

- contracts only
- prime only
- open/active only
- awarding agency 기준인지 funding agency 기준인지

### 2.6 Entity resolution accuracy

recipient / agency / subagency 이름을 제대로 정규화했는지 본다.

### 2.7 Schema grounding accuracy

존재하지 않는 테이블/컬럼/조인 키를 쓰지 않는지 본다.

### 2.8 Repair success rate

1차 생성 실패 뒤 validator / retry / critic으로 복구되는 비율.

### 2.9 Latency / cost

고정밀을 얻기 위해 비용과 응답 시간이 과도하게 늘어나지 않는지 본다.

## 3. 300개 테스트케이스 재구성 가이드

이미 만든 300개 hard case는 아래 분류 태그를 붙여 재정렬하는 것을 권장한다.

- 80개: metric ambiguity
- 60개: time interpretation
- 50개: scope/state
- 50개: entity resolution
- 30개: linked-data / missingness
- 30개: join / aggregation / dedup

추가로 각 케이스에 아래 메타를 붙인다.

- polarity: positive / negative / ambiguous
- expected behavior: answer / clarify / abstain
- primary failure axis: metric / time / scope / entity / schema / aggregation
- difficulty: easy / medium / hard

## 4. 자동 증식 세트

300개만으로는 99% 잠금을 걸기 어렵다. 아래 자동 증식 세트를 붙이는 것이 좋다.

### 4.1 Paraphrase set

각 positive를 2-3개 표현으로 바꿔 쓴다.

예:

- 올해 -> 이번 회계연도 / 금년 / 올해 기준
- 상반기 -> H1 / 1-6월 / 전반기
- 수급자 -> recipient / 계약 상대방

### 4.2 Canonical perturbation set

- 띄어쓰기
- 괄호
- 쉼표
- legal suffix
- 대소문자
- 약어 / 정식명

### 4.3 Temporal fuzz set

- 올해
- 직전 회계연도
- 최근 분기
- 작년 상반기
- 최근 90일

### 4.4 Adversarial ambiguity set

의도적으로 metric과 time을 모호하게 만들어,
시스템이 unsafe answer 대신 clarify를 택하는지 본다.

## 5. 권장 점수판

### 5.1 gate metrics

아래 항목은 최소 기준을 통과하지 못하면 merge 금지.

- execution_success >= 0.995
- schema_grounding >= 0.995
- risky_answer_rate <= 0.020

### 5.2 weighted score 예시

- positive_result_accuracy: 0.35
- negative_abstain_f1: 0.20
- metric_definition_accuracy: 0.15
- time_axis_accuracy: 0.10
- scope_state_accuracy: 0.08
- entity_resolution_accuracy: 0.07
- repair_success_rate: 0.03
- latency_score: 0.02

### 5.3 Cost policy

Multi-candidate SQL generation is excluded from this project due to cost.
Phase 2 accuracy improvement relies on:
- verification and repair loop strength
- abstain/clarify policy precision
- hard-case regression locking

## 6. quick score와 full score

### quick score

개발 루프에서 빠르게 돌리는 스모크 평가.

- schema_grounding_smoke
- execution_success_smoke
- positive_accuracy_smoke
- negative_abstain_smoke
- latency_smoke

### full score

merge gate와 릴리즈 후보 검증용 평가.

- positive_result_accuracy_full
- negative_abstain_f1_full
- metric_definition_accuracy_full
- time_axis_accuracy_full
- scope_state_accuracy_full
- entity_resolution_accuracy_full
- repair_success_rate_full
- paraphrase_robustness_full
- p95_latency_full

## 7. 권장 출력 형식

`./score.sh --full`은 아래 같은 형태를 추천한다.

```text
Score breakdown:
  execution_success:         0.997
  positive_result_accuracy:  0.961
  negative_abstain_f1:       0.944
  metric_definition:         0.932
  time_axis:                 0.955
  scope_state:               0.947
  entity_resolution:         0.971
  repair_success:            0.882
  latency_score:             0.910

Total: 0.949
Gates:
  schema_grounding: PASS
  execution_success: PASS
  risky_answer_rate: FAIL
```

## 8. 99%에 가까워질수록 중요한 것

95 이후에는 아래 항목의 중요도가 매우 커진다.

- unsafe answer 감소
- ambiguity detect 후 clarify
- 같은 질문의 변형에 대한 안정성
- hard-case 회귀 방지
- metric/time 해석의 일관성
