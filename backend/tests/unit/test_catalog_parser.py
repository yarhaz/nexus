import pytest
from app.modules.ingestion.catalog_parser import parse_catalog_info, make_deterministic_id


VALID_YAML = """
apiVersion: nexus.io/v1
kind: Component
metadata:
  name: my-api
  description: My API service
  tags: [python, fastapi]
spec:
  owner: platform-team
  lifecycle: production
  status: active
  runbookUrl: https://wiki.example.com/my-api
"""

MINIMAL_YAML = """
metadata:
  name: minimal-service
spec:
  owner: team-a
"""


def test_parse_valid_yaml():
    result = parse_catalog_info(VALID_YAML, "https://github.com/org/my-api")
    assert result is not None
    assert result.name == "my-api"
    assert result.description == "My API service"
    assert result.team == "platform-team"
    assert result.lifecycle == "production"
    assert result.status == "active"
    assert "python" in result.tags


def test_parse_minimal_yaml():
    result = parse_catalog_info(MINIMAL_YAML)
    assert result is not None
    assert result.name == "minimal-service"
    assert result.lifecycle == "development"  # default


def test_parse_missing_name():
    result = parse_catalog_info("metadata:\n  description: no name here\n")
    assert result is None


def test_parse_invalid_yaml():
    result = parse_catalog_info("{ invalid: yaml: content ::::")
    assert result is None


def test_parse_invalid_status_defaults():
    yaml = "metadata:\n  name: svc\nspec:\n  status: unknown-status\n"
    result = parse_catalog_info(yaml)
    assert result is not None
    assert result.status == "active"


def test_deterministic_id():
    id1 = make_deterministic_id("https://github.com/org/repo")
    id2 = make_deterministic_id("https://github.com/org/repo")
    id3 = make_deterministic_id("https://github.com/org/other-repo")
    assert id1 == id2
    assert id1 != id3


def test_deterministic_id_is_valid_uuid():
    import uuid
    id1 = make_deterministic_id("https://github.com/org/repo")
    uuid.UUID(id1)  # Should not raise
