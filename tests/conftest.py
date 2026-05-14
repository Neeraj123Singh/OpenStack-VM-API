import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.deps import get_vm_service
from app.main import create_app
from app.services.mock_vm import MockVMService


@pytest.fixture(autouse=True)
def _mock_mode_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENSTACK_MODE", "mock")
    get_settings.cache_clear()


@pytest.fixture()
def client() -> TestClient:
    app = create_app()
    mock_svc = MockVMService()

    def _override() -> MockVMService:
        return mock_svc

    app.dependency_overrides[get_vm_service] = _override
    with TestClient(app) as tc:
        yield tc
    app.dependency_overrides.clear()
