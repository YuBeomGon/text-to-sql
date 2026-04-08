from src.data_download import build_download_request, parse_download_response


def test_build_download_request_structure():
    req = build_download_request(
        agencies=["NASA", "Department of Defense"],
        start_date="2023-10-01",
        end_date="2025-09-30",
    )
    assert req["filters"]["prime_award_types"] == ["A", "B", "C", "D"]
    assert len(req["filters"]["agencies"]) == 2
    assert req["filters"]["date_range"]["start_date"] == "2023-10-01"


def test_build_download_request_agency_format():
    req = build_download_request(
        agencies=["NASA"],
        start_date="2023-10-01",
        end_date="2025-09-30",
    )
    agency = req["filters"]["agencies"][0]
    assert agency["type"] == "awarding"
    assert agency["tier"] == "toptier"
    assert agency["name"] == "NASA"


def test_parse_download_response_extracts_url():
    response_data = {
        "status_url": "https://api.usaspending.gov/api/v2/bulk_download/status/?file_name=test.zip",
        "file_url": "https://files.usaspending.gov/generated_downloads/test.zip",
        "file_name": "test.zip",
    }
    url = parse_download_response(response_data)
    assert url == "https://files.usaspending.gov/generated_downloads/test.zip"


def test_parse_download_response_handles_missing_url():
    response_data = {"status_url": "https://example.com/status"}
    url = parse_download_response(response_data)
    assert url is None
