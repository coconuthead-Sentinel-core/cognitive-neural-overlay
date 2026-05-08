"""CSTM §4 metadata frontmatter tests."""
from fastapi.testclient import TestClient

from cno.app import app
from cno.metadata import (
    ArtifactMetadata, make_metadata, render_artifact,
    to_dict, to_yaml_frontmatter, METADATA_VERSION, SPEC_REF,
)


client = TestClient(app)


def test_metadata_carries_10_fields_plus_spec_gaps():
    m = make_metadata(run_id="r1", ts="2026-05-08T00:00:00+00:00",
                      session_id="s1", zone="zone-A")
    d = to_dict(m)
    expected_fields = {
        "artifact_id", "canon_ref", "artifact_type", "metadata_version",
        "spec_ref", "created_at", "created_by", "run_id", "session_id", "zone",
    }
    assert expected_fields <= set(d)
    assert d["metadata_version"] == METADATA_VERSION
    assert d["spec_ref"] == SPEC_REF
    assert isinstance(d["spec_gaps"], list) and d["spec_gaps"]


def test_artifact_id_is_stable_for_same_inputs():
    a = make_metadata(run_id="r1", ts="t1")
    b = make_metadata(run_id="r1", ts="t1")
    assert a.artifact_id == b.artifact_id


def test_artifact_id_changes_when_inputs_change():
    a = make_metadata(run_id="r1", ts="t1")
    b = make_metadata(run_id="r2", ts="t1")
    assert a.artifact_id != b.artifact_id


def test_yaml_frontmatter_brackets_are_correct():
    m = make_metadata(run_id="r1", ts="2026-05-08T00:00:00+00:00")
    fm = to_yaml_frontmatter(m)
    lines = fm.splitlines()
    assert lines[0] == "---"
    assert lines[-1] == "---"
    assert any(line.startswith("artifact_id: ") for line in lines)
    assert any(line.startswith("metadata_version: ") for line in lines)


def test_yaml_handles_null_and_lists():
    m = make_metadata(run_id="r1", ts="t", session_id=None, zone=None)
    fm = to_yaml_frontmatter(m)
    assert "session_id: null" in fm
    assert "zone: null" in fm
    assert "spec_gaps:" in fm
    assert "  - " in fm  # list items are indented


def test_yaml_quotes_values_with_colons():
    m = ArtifactMetadata(
        artifact_id="x", canon_ref="#18 CNO", artifact_type="t",
        metadata_version="1.0", spec_ref="CSTM_Lattice v1.0 §4",
        created_at="t", created_by="cno/0.3.0", run_id="r", session_id=None, zone=None,
    )
    fm = to_yaml_frontmatter(m)
    # spec_ref contains §, no colon. created_by contains '/' but no colon.
    # Make sure the canon_ref starting with '#' is quoted.
    assert 'canon_ref: "#18 CNO"' in fm


def test_render_artifact_combines_frontmatter_and_body():
    m = make_metadata(run_id="r1", ts="t1")
    art = render_artifact(m, "# Title\n\nbody text")
    assert art.startswith("---\n")
    assert "\n---\n\n# Title" in art
    assert art.endswith("body text\n")


# --- API integration ---

def test_envelope_payload_carries_metadata():
    r = client.post("/cno/process", json={"request": "hello there"})
    assert r.status_code == 200
    md = r.json()["payload"]["metadata"]
    assert md["spec_ref"] == SPEC_REF
    assert md["run_id"] == r.json()["run_id"]
    assert md["artifact_type"] == "pipeline-run"


def test_artifact_endpoint_returns_markdown_with_frontmatter():
    r = client.post("/cno/process", json={"request": "make me an artifact"})
    run_id = r.json()["run_id"]

    art = client.get(f"/cno/artifact/{run_id}")
    assert art.status_code == 200
    assert art.headers["content-type"].startswith("text/plain")
    text = art.text
    assert text.startswith("---\n")
    assert "\n---\n\n" in text
    assert "# CNO pipeline run" in text
    assert run_id in text


def test_artifact_endpoint_404_for_unknown_run():
    r = client.get("/cno/artifact/does-not-exist")
    assert r.status_code == 404
