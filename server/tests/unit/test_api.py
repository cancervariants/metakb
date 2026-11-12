"""Check basic functions of general endpoint(s)"""

from pathlib import Path

import jsonschema
import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient

from metakb.main import app, mount_client


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.mark.ci_ok
def test_frontend(tmp_path: Path):
    """Serve a minimal frontend build without application startup dependencies."""
    html = "<!doctype html><html><body>MetaKB</body></html>"
    (tmp_path / "index.html").write_text(html)
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log('MetaKB');")

    frontend = FastAPI()
    mount_client(frontend, tmp_path)
    with TestClient(frontend) as client:
        for path in ("/", "/search"):
            response = client.get(path)
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/html")
            assert response.text == html

        response = client.get("/assets/app.js")
        assert response.status_code == 200
        assert response.text == "console.log('MetaKB');"


@pytest.mark.filterwarnings(
    "ignore:jsonschema\\.RefResolver is deprecated:DeprecationWarning"
)
def test_service_info(client: TestClient, test_data_dir: Path):
    response = client.get("/api/service-info")
    response.raise_for_status()

    with (test_data_dir / "general" / "service_info_openapi.yaml").open() as f:
        spec = yaml.safe_load(f)

    resp_schema = spec["paths"]["/service-info"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]

    resolver = jsonschema.RefResolver.from_schema(spec)
    data = response.json()
    jsonschema.validate(instance=data, schema=resp_schema, resolver=resolver)
