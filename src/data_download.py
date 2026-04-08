from __future__ import annotations

import io
import time
import zipfile
from pathlib import Path

import httpx

_API_BASE = "https://api.usaspending.gov/api/v2"
_DOWNLOAD_TIMEOUT = 600


def build_download_request(
    agencies: list[str],
    start_date: str,
    end_date: str,
) -> dict:
    """Build the request body for the USAspending bulk download API."""
    return {
        "filters": {
            "agencies": [
                {"type": "awarding", "tier": "toptier", "name": name}
                for name in agencies
            ],
            "prime_award_types": ["A", "B", "C", "D"],
            "date_type": "action_date",
            "date_range": {
                "start_date": start_date,
                "end_date": end_date,
            },
        },
        "columns": [],
        "file_format": "csv",
    }


def parse_download_response(data: dict) -> str | None:
    """Extract the file URL from the bulk download API response."""
    return data.get("file_url")


def request_download(
    agencies: list[str],
    start_date: str,
    end_date: str,
) -> str:
    """Request a bulk download and return the status URL."""
    body = build_download_request(agencies, start_date, end_date)
    resp = httpx.post(
        f"{_API_BASE}/bulk_download/awards/",
        json=body,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["status_url"]


def poll_until_ready(status_url: str, poll_interval: int = 15) -> str:
    """Poll the status URL until the file is ready. Return the file URL."""
    elapsed = 0
    retries = 0
    max_retries = 3
    while elapsed < _DOWNLOAD_TIMEOUT:
        try:
            resp = httpx.get(status_url, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            retries = 0  # reset on success
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as e:
            retries += 1
            print(f"  Connection error ({retries}/{max_retries}): {e}")
            if retries >= max_retries:
                raise
            time.sleep(poll_interval)
            elapsed += poll_interval
            continue

        if data.get("status") == "finished":
            file_url = data.get("file_url")
            if file_url:
                return file_url
            raise RuntimeError("Download finished but no file_url in response")

        if data.get("status") == "failed":
            raise RuntimeError(f"Download failed: {data.get('message', 'unknown')}")

        print(f"  Status: {data.get('status', 'unknown')}... ({elapsed}s)")
        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"Download not ready after {_DOWNLOAD_TIMEOUT}s")


def download_and_extract(file_url: str, dest_dir: Path) -> list[Path]:
    """Download the zip file and extract CSVs to dest_dir."""
    dest_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {file_url} ...")
    resp = httpx.get(file_url, timeout=300, follow_redirects=True)
    resp.raise_for_status()

    csv_paths = []
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        for name in zf.namelist():
            if name.endswith(".csv"):
                zf.extract(name, dest_dir)
                csv_paths.append(dest_dir / name)
                print(f"  Extracted: {name}")

    return csv_paths


def fetch_data(
    agencies: list[str],
    start_date: str,
    end_date: str,
    dest_dir: Path,
) -> list[Path]:
    """Full pipeline: request download -> poll -> download -> extract CSVs."""
    print(f"Requesting bulk download for {len(agencies)} agencies...")
    status_url = request_download(agencies, start_date, end_date)
    print(f"Status URL: {status_url}")

    print("Waiting for file generation...")
    file_url = poll_until_ready(status_url)
    print(f"File ready: {file_url}")

    return download_and_extract(file_url, dest_dir)
