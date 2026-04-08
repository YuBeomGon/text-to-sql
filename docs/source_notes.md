# Source Notes

아래 링크는 공공 데이터 버전 과제를 설계할 때 참고한 공식 문서다.

## USAspending

- API overview: https://api.usaspending.gov/
- API endpoints: https://api.usaspending.gov/docs/endpoints
- Federal Spending Guide PDF: https://www.usaspending.gov/data/Federal-Spending-Guide.pdf
- Data Sources Download PDF: https://www.usaspending.gov/data/data-sources-download.pdf

핵심 참고 포인트:
- API 엔드포인트가 인증 없이 공개되어 있다.
- recipient / awarding agency / glossary autocomplete 엔드포인트가 있다.
- obligation / outlay / award spending 등 의미가 다른 금액 축이 공존한다.
- linked / unlinked 데이터와 파일 계층이 달라 세부정보 누락/범위 착오 문제가 생길 수 있다.

## DuckDB

- Overview: https://duckdb.org/
- Parquet reading docs: https://duckdb.org/docs/stable/data/parquet/overview
- Multiple files docs: https://duckdb.org/docs/current/data/multiple_files/overview.html

핵심 참고 포인트:
- in-process DB로 사용하기 좋다.
- CSV / Parquet를 직접 읽을 수 있다.
- 작은 범위의 공개 데이터 slice를 빠르게 로드해 실험하기 좋다.
