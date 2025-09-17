import io, os
from hr_parser.service import HRResumeParserService

def test_mock_parse(monkeypatch):
    os.environ["HRP_USE_MOCK"] = "true"
    svc = HRResumeParserService()
    fake = io.BytesIO(b"John Doe\nEmail: john@example.com\nSkills: Python, FastAPI")
    res = svc.parse_fileobj(fake, "john_doe.pdf")
    assert res["ok"] is True
    assert "candidate_id" in res