import hashlib
import hmac

from app.services.github_ingestion import incident_from_github_issue_event, verify_github_signature


def test_verify_github_signature_valid() -> None:
    secret = "abc123"
    payload = b'{"action":"opened"}'
    signature = "sha256=" + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    verify_github_signature(secret=secret, signature_header=signature, payload=payload)


def test_parse_github_issue_event_to_incident() -> None:
    body = {
        "action": "opened",
        "issue": {
            "title": "High error rate in prod",
            "body": "Spike after deploy",
            "number": 42,
            "html_url": "https://github.com/org/repo/issues/42",
            "labels": [{"name": "incident"}, {"name": "sev1"}],
        },
        "repository": {"full_name": "org/repo"},
    }
    incident = incident_from_github_issue_event(event_type="issues", body=body)
    assert incident is not None
    assert incident.source == "github"
    assert incident.title == "High error rate in prod"
    assert incident.metadata["repository"] == "org/repo"
