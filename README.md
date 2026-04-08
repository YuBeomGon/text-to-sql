# Public NL2SQL Harness Starter

이 폴더는 원 과제 PDF를 `공공 데이터 + in-memory DB + harness 기반 개발` 형태로 다시 해석한 시작용 문서 묶음입니다.

핵심 목적은 다음 두 가지입니다.

1. Claude Code 에이전트가 과제 맥락을 빠르게 이해하도록 한다.
2. `program.md -> docs/wbs_v0.1.md -> score.sh -> harness/run.sh` 흐름으로, 에이전트가 스스로 검증하면서 최종 제품까지 가는 틀을 만든다.

## 이 폴더를 어떻게 쓰면 되나

Claude Code에서 작업할 때 아래 순서로 읽히게 하면 됩니다.

1. `README.md`
2. `docs/project_context.md`
3. 업로드한 원 과제 PDF
4. `docs/public_db_adaptation.md`
5. `docs/evaluation_framework.md`
6. `program.md`
7. `docs/wbs_v0.1.md`
8. `docs/harness_design.md`

그 다음부터 에이전트는 `program.md` 규칙대로 다음 미완료 WBS 항목을 찾아 구현하고, `score.sh --quick` 또는 `score.sh --full`로 검증하는 방식으로 작업하게 하면 됩니다.

## 포함 파일

- `docs/project_context.md`
  - 원 과제 요약
  - 핵심 실패 원인
  - phase 1 / phase 2 전략
- `docs/public_db_adaptation.md`
  - 원 과제를 공공 데이터 과제로 바꾸는 과정
  - 왜 USAspending contracts slice를 추천하는지
  - 원 오류 유형이 공공 데이터에선 무엇으로 바뀌는지
- `docs/evaluation_framework.md`
  - 평가 지표
  - 300개 테스트케이스 재구성 방법
  - quick/full score 기준
- `program.md`
  - 에이전트 운영 규약
- `docs/wbs_v0.1.md`
  - milestone 단위 작업 분해
- `docs/harness_design.md`
  - harness 역할 분리, merge gate, 작업 방식
- `score.sh`
  - 실행 가능한 스텁
- `harness/run.sh`
  - 단계별 실행 스텁
- `harness/team.toml`
  - 역할 정의 예시

## 추천 시작 범위

처음부터 전체 공개 지출 데이터를 다루지 말고 아래 범위만 다루는 것을 권장합니다.

- 데이터 원천: USAspending 공개 데이터
- 도메인: federal contracts only
- 기간: 최근 2개 fiscal year
- 범위: 3-5개 awarding agency
- DB 엔진: DuckDB in-memory

## 왜 이런 구조가 필요한가

원 과제의 핵심 문제는 SQL 실행 실패가 아니라 의미 해석 실패입니다. 따라서 이번 프로젝트도

- 더 긴 프롬프트를 만드는 것
- 더 큰 모델 하나로 해결하는 것

보다,

- metric 정의 계층
- 시간 해석 계층
- entity 정규화 계층
- ambiguity 감지와 보수적 답변 정책
- result-set 기준 평가

를 먼저 구조화해야 합니다.

## Claude Code에 넣을 추가 지시 예시

아래와 같은 한 줄 지시를 프로젝트 시작 메시지에 붙이면 좋습니다.

`원 과제 PDF와 docs/ 이하 문서를 먼저 읽고, public NL2SQL 시스템을 docs/wbs_v0.1.md 순서대로 구현하라. 다음 미완료 항목 하나만 진행하고, 각 변경 뒤에 ./score.sh --quick 을 실행하라.`

## 외부 참고 소스

상세 링크는 `docs/source_notes.md`에 정리했습니다.

## Additional governance files

- `CLAUDE.md`
  - Claude Code operating instructions
  - coding rules
  - subagent guidance
  - SSOT handling summary
- `docs/ssot_guide.md`
  - single source of truth policy
  - where each kind of rule should live
- `CONTRIBUTING.md`
  - branch strategy
  - commit strategy
  - PR strategy
  - review expectations

## Where to put which rules

Use this default:

- agent operating behavior -> `CLAUDE.md`
- product workflow and hard constraints -> `program.md`
- task decomposition -> `docs/wbs_v0.1.md`
- evaluation logic and score gates -> `docs/evaluation_framework.md`
- public-data scope and reinterpretation of the original PDF -> `docs/public_db_adaptation.md`
- SSOT ownership and drift prevention -> `docs/ssot_guide.md`
- commit, branch, and PR workflow -> `CONTRIBUTING.md`

This separation helps Claude Code avoid mixing product rules, coding rules, and collaboration rules into one file.


## Claude Code project files

This starter now includes project-level Claude Code helpers:

- `.claude/agents/`
  - `data-eval.md`
  - `semantics.md`
  - `verifier.md`
  - `policy.md`
  - `bench.md`
- `.claude/commands/`
  - `quick-score.md`
  - `full-eval.md`
  - `delegate-next.md`

Recommended use:
- keep foundation work in the main agent
- after interfaces stabilize, delegate narrow tasks to the matching subagent
- merge only one small change at a time
- require `./score.sh --quick` before keeping a change


## Evaluation assets

This starter now includes a concrete evaluation pack under `eval/`:

- `eval/cases/*.jsonl`
  - 300 semantic hard cases split by failure category
- `eval/cases/combined_hard_cases.jsonl`
  - merged manifest for scoring pipelines
- `eval/cases/gold_result_snapshot_template.jsonl`
  - template for freezing gold results after the dataset slice is locked
- `eval/expansions/*.yaml`
  - paraphrase, temporal fuzz, and adversarial expansion templates
- `eval/README.md`
  - case schema, intended usage, and how to backfill result snapshots

Use the semantic cases immediately for policy, semantics, verifier, and regression work.
Once the USAspending slice is fixed, backfill positive-case gold outputs into the snapshot template and promote selected cases into locked full-score evaluation.
