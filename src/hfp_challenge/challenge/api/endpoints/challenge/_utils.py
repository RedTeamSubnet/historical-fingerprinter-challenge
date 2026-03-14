import time
from enum import Enum

import docker
import requests

NETWORK_NAME = "internal_net"
FINGERPRINTER_IMAGE = "redteamsubnet61/hfp_fingerprinter:latest"
FINGERPRINTER_PORT = 10002
FINGERPRINT_STORAGE: dict[str, str] = {}


class ScoringStatus(str, Enum):
    STARTED = "started"
    SCORING = "scoring"
    AVAILABLE = "available"


_scoring_status = ScoringStatus.STARTED


def get_scoring_status() -> ScoringStatus:
    return _scoring_status


def set_scoring_status(status: ScoringStatus) -> None:
    global _scoring_status
    _scoring_status = status


def get_fingerprint_storage() -> dict[str, str]:
    return FINGERPRINT_STORAGE


def clear_fingerprint_storage() -> None:
    global FINGERPRINT_STORAGE
    FINGERPRINT_STORAGE = {}


def ensure_network_exists() -> None:
    client = docker.from_env()
    try:
        client.networks.get(NETWORK_NAME)
    except docker.errors.NotFound:
        client.networks.create(NETWORK_NAME, driver="bridge", internal=True)


def wait_for_health(ip_address: str, timeout: int = 60) -> None:
    url = f"http://{ip_address}:{FINGERPRINTER_PORT}/health"
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200 and resp.json().get("status") == "ok":
                return
        except Exception:
            pass
        time.sleep(1)
    raise TimeoutError(
        f"Fingerprinter container health check timed out after {timeout}s"
    )


def run_fingerprinter_container(
    request_id: str,
    files_dir: str,
) -> tuple[docker.models.containers.Container, str]:
    client = docker.from_env()
    ensure_network_exists()

    container_name = f"fingerprinter_{request_id}"

    container = client.containers.run(
        FINGERPRINTER_IMAGE,
        detach=True,
        network=NETWORK_NAME,
        volumes={files_dir: {"bind": "/app/submissions/"}},
        name=container_name,
    )

    container.reload()
    ip_address = container.attrs["NetworkSettings"]["Networks"][NETWORK_NAME][
        "IPAddress"
    ]

    return container, ip_address


def cleanup_container(container: docker.models.containers.Container) -> None:
    try:
        container.stop()
        container.remove()
    except docker.errors.NotFound:
        pass
