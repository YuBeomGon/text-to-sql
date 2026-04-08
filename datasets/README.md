# Datasets

This directory holds the local USAspending data files used by the project.

## How to acquire data

1. Run `python -m src.loader --download` (after Task 4 is implemented)
2. Or manually download from https://api.usaspending.gov/api/v2/bulk_download/

## What should be here after download

- `contracts_FY2024.csv` or `.parquet`
- `contracts_FY2025.csv` or `.parquet`

Do not commit large data files. Add them to `.gitignore`.
