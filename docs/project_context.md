# 프로젝트 맥락 정리

## 1. 원 과제 요약

원 과제는 사내 리소스 관리 웹서비스의 운영 데이터를 대상으로, 관리자가 자연어로 질문하면 LLM이 SQL을 생성해 결과를 반환하는 시스템을 개선하는 문제다.

기존 파일럿 시스템은 다음 구조를 가진다.

- 사용자 질문 입력
- 상용 LLM API 호출
- SQL 생성
- 내부 DB 실행
- 결과 반환

입력 프롬프트는 매우 큰 단일 프롬프트였고, 대략 다음이 포함되어 있다.

- SQL 전문가 페르소나
- 약 80개 테이블 스키마
- 각 테이블 일부 레코드

파일럿 결과는 아래와 같다.

- 실행 가능한 SQL 생성 확률: 매우 높음
- 질의 의도에 맞는 정확한 결과 반환 확률: 75%

최종 목표는 3개월 안에 SQL 생성 정확도를 99%까지 개선하는 것이다.

## 2. 원 과제의 핵심 문제 정의

이 과제의 핵심은 `SQL 문법 생성` 문제가 아니라 `의미 해석 정확도` 문제다.

실패 사례를 보면 대부분 아래 부류다.

1. 스키마 grounding 실패
   - 존재하지 않는 컬럼을 사용한다.
2. 시간 해석 실패
   - 상반기 요청에 다른 연도/다른 기간을 반환한다.
3. metric 정의 실패
   - "금액"을 계약금액이 아니라 인건비로 해석한다.
4. scope/state 필터 실패
   - 전직원 조회에 퇴사자를 포함한다.
5. entity resolution 실패
   - 띄어쓰기나 표기 차이 때문에 같은 엔티티를 찾지 못한다.
6. business rule 실패
   - "미입력"의 실제 업무 정의를 몰라 null만 찾는다.

즉, 문제를 이렇게 다시 써야 한다.

> 실행 가능한 SQL을 만드는 시스템이 아니라,
> 의미적으로 안전하고 검증 가능한 질의 시스템을 만든다.

## 3. 왜 공공 데이터로 바꾸는가

이번 프로젝트에서는 데이터 설계와 데이터 채우기 자체를 별도 작업으로 만들지 않기 위해, 공개 데이터베이스를 기준으로 과제를 다시 정의한다.

핵심 원칙은 다음과 같다.

- 데이터는 공개 원천을 그대로 사용한다.
- 별도 DB 서버를 설치하지 않는다.
- 앱 시작 시 공개 CSV/Parquet를 DuckDB in-memory로 읽어 쿼리한다.
- 평가 기준은 원 과제의 오류 유형을 공공 데이터의 유사 오류 유형으로 치환해 만든다.

## 4. 왜 USAspending contracts slice를 추천하는가

공공 데이터 후보는 많지만, 이번 과제와 가장 비슷한 오류 구조를 만들기 쉬운 것은 USAspending 계약/지출 데이터다.

이 데이터를 추천하는 이유는 다음과 같다.

- 공식 공개 데이터/API가 있다.
- agency, subagency, recipient, award, transaction, fiscal year 등 질의 축이 풍부하다.
- amount 관련 정의가 여러 개여서 metric ambiguity를 테스트하기 좋다.
- fiscal year와 calendar year 혼동 같은 시간 해석 오류를 만들기 쉽다.
- recipient/agency 표기 변형 문제로 entity resolution 테스트가 가능하다.
- DuckDB in-memory로 얇게 시작하기 좋다.

## 5. 공공 데이터 버전에서의 핵심 질문

이 프로젝트를 Claude Code 에이전트가 이해하도록 만들려면, 아래 질문에 답하는 구조로 문서를 써야 한다.

1. 사용자는 어떤 공개 데이터에 대해 질문하는가?
2. 질문의 metric은 무엇인가?
3. 질문의 시간 축은 무엇인가?
4. 질문의 scope는 무엇인가?
5. entity 이름은 어떻게 정규화하는가?
6. 애매하면 답할 것인가, 되물을 것인가?
7. 정답 여부는 SQL 문자열이 아니라 결과 의미로 어떻게 판단하는가?

## 6. phase 1 / phase 2 전략

### phase 1: 75 -> 95

이 단계의 핵심은 `구조화와 가드레일`이다.

먼저 넣어야 할 것:

- schema retrieval
- glossary / metric dictionary
- time interpreter
- entity resolver
- SQL static validator
- ambiguity detector
- retry / repair loop

여기서는 모델 교체보다 구조화가 더 큰 효과를 낸다.

### phase 2: 95 -> 99

이 단계의 핵심은 `고정밀 운영`이다.

추가해야 할 것:

- multi-candidate plan / SQL generation
- semantic reranking
- uncertainty scoring
- abstain / clarify 정책 강화
- hard-case 회귀 잠금
- benchmark 및 릴리즈 게이트 강화

95 이후는 더 똑똑한 한 번 생성보다, 틀릴 가능성이 있을 때 멈추는 능력이 중요하다.

## 7. 이 프로젝트의 성공 조건

최종 성공 조건은 단순히 SQL이 실행되는 것이 아니다.

- 결과 의미가 맞아야 한다.
- 정의가 애매하면 보수적으로 질문을 되물어야 한다.
- public data slice 기준으로 반복 가능한 평가가 있어야 한다.
- Claude Code 에이전트가 문서만 읽고도 다음 작업을 이어갈 수 있어야 한다.
