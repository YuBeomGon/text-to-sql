# 원 과제를 공공 데이터 과제로 바꾸는 과정

## 1. 왜 변환이 필요한가

원 과제는 사내 리소스 관리 DB를 전제로 하지만, 이번 프로젝트에서는

- 사내 DB 설계
- 초기 데이터 생성/적재
- 운영용 DB 설치 및 관리

를 별도 업무로 만들고 싶지 않다.

따라서 원 과제의 본질만 남기고, 데이터 계층은 공개 데이터로 교체한다.

남겨야 하는 본질은 다음과 같다.

- 자연어 질문을 SQL로 바꾼다.
- 실행 가능한 SQL보다 의미 정확도가 중요하다.
- 업무 용어 정의를 잘못 이해하면 크게 틀린다.
- 평가 하네스가 개발을 끌고 가야 한다.
- phase 1 / phase 2로 나눠 정밀도를 끌어올린다.

## 2. 공개 데이터 선택 기준

공공 데이터는 아래 기준으로 골라야 한다.

1. 질문 축이 여러 개여야 한다.
   - 금액
   - 기간
   - 기관
   - 수급자
   - 상태
2. 스키마가 너무 빈약하지 않아야 한다.
3. 정의가 비슷해 보이지만 실제로 다른 필드가 있어야 한다.
4. entity 정규화 문제를 만들 수 있어야 한다.
5. DuckDB in-memory에서 쉽게 다룰 수 있어야 한다.

이 기준에 가장 잘 맞는 초기 선택이 `USAspending contracts slice`다.

## 3. 추천 공개 데이터 범위

초기 범위는 작게 잡는다.

- 원천: USAspending 공식 공개 데이터/API
- 도메인: contracts only
- 기간: 최근 2개 fiscal year
- 범위: 3-5개 awarding agency
- 저장: DuckDB in-memory

이 범위면 데이터 구축 부담은 작고, 오류 유형은 충분히 풍부하다.

## 4. 원 과제 오류를 공공 데이터 오류로 바꾸기

아래 표가 가장 중요하다. Claude Code 에이전트가 원 과제를 공공 데이터 버전으로 이해하려면, 이 대응표를 먼저 이해해야 한다.

| 원 과제 오류 유형 | 공공 데이터 버전의 유사 오류 |
|---|---|
| 존재하지 않는 컬럼 사용 | 존재하지 않는 award/transaction/account 필드 사용 |
| 상반기 해석 오류 | fiscal year vs calendar year, action date vs award date 혼동 |
| 금액 정의 혼동 | award amount vs obligation vs outlay vs transaction amount 혼동 |
| 퇴사자 포함 같은 범위 오류 | active/open award만 봐야 하는데 closed/deobligated 포함 |
| 프로젝트명 표기 차이 미해결 | recipient / agency 명칭 alias, suffix, punctuation 차이 미해결 |
| 미입력 정의 오해 | null vs zero vs 미보고 vs negative obligation 의미 혼동 |

즉, 바뀌는 것은 데이터 도메인이지, 핵심 연구 문제는 그대로다.

## 5. 이 변환으로 생기는 대표 질문들

원 과제의 질문을 public 버전으로 바꾸면 아래 같은 질문이 된다.

- 가장 많은 obligation이 발생한 awarding agency Top 5는?
- 최근 2개 fiscal year 동안 outlay가 감소한 subagency는?
- recipient별 평균 award amount가 가장 큰 기관은?
- prime awards만 기준으로 가장 많은 계약을 맺은 recipient는?
- 올해 상반기와 작년 상반기를 비교했을 때 집행 패턴이 달라진 agency는?

이 질문들은 모두 metric, time, scope, entity 해석이 필요하다.

## 6. public DB 버전의 주요 위험

### 6.1 metric ambiguity

"금액"이라고 했을 때 아래 중 무엇인지 다를 수 있다.

- total award amount
- obligation
- outlay
- transaction obligated amount

### 6.2 time ambiguity

"올해", "상반기", "최근 분기"가 아래 중 무엇인지 애매할 수 있다.

- calendar year
- fiscal year
- fiscal half / calendar half
- award start date 기준
- action date 기준

### 6.3 scope ambiguity

아래 범위를 잘못 잡기 쉽다.

- contracts only vs all awards
- prime awards vs subawards
- awarding agency vs funding agency
- active/open only vs closed 포함

### 6.4 entity ambiguity

같은 엔티티가 다르게 표기될 수 있다.

- recipient 공식명 vs 검색명
- agency 약어 vs 정식 명칭
- punctuation / legal suffix 차이

## 7. 공공 데이터 버전의 아키텍처 원칙

이 프로젝트의 아키텍처는 아래 원칙을 지켜야 한다.

1. DB를 설계하지 말고 공개 데이터 파일을 읽는다.
2. 모든 질문을 바로 SQL로 보내지 말고 중간 의미 표현으로 먼저 정리한다.
3. metric / time / scope / entity를 별도 모듈로 해석한다.
4. ambiguity가 있으면 clarify 또는 abstain으로 라우팅한다.
5. 평가는 SQL 문자열이 아니라 result-set 중심으로 한다.

## 8. Claude Code에 줄 핵심 한 줄 설명

> 원 과제의 사내 리소스 DB를 public USAspending contracts slice로 치환하고,
> metric/time/scope/entity 의미 해석 정확도를 개선하는 high-precision NL2SQL 시스템을 만든다.
