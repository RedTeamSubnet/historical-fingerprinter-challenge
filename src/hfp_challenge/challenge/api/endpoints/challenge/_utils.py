import os
import time
from enum import Enum
from threading import Thread

import docker
import requests

from api.logger import logger

NETWORK_NAME = "internal_net"
FINGERPRINTER_IMAGE = "redteamsubnet61/hfp_fingerprinter:latest"
FINGERPRINTER_BUILD_PATH = f"{os.getenv('HFP_CHALLENGE_API_DIR')}/fingerprinter"
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


def wait_for_health(
    ip_address: str, timeout: int = 100, fingerprinter_port: int = 8000
) -> None:
    url = f"http://{ip_address}:{fingerprinter_port}/health"
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
        f"Fingerprinter container health check timed out after {timeout}s in this url: {url}"
    )


def _ensure_image(client: docker.DockerClient) -> None:
    try:
        client.images.get(FINGERPRINTER_IMAGE)
    except docker.errors.NotFound:
        try:
            client.images.pull(FINGERPRINTER_IMAGE)
        except docker.errors.NotFound:
            client.images.build(
                path=FINGERPRINTER_BUILD_PATH,
                tag=FINGERPRINTER_IMAGE,
                rm=True,
            )


def run_fingerprinter_container(
    request_id: str, files_dir: str, fingerprinter_port: int = 8000
) -> tuple[docker.models.containers.Container, str]:
    client = docker.from_env()
    ensure_network_exists()
    _ensure_image(client)

    container_name = f"fingerprinter_{request_id}"

    volumes = {}
    for file_name in os.listdir(files_dir):
        file_path = os.path.join(files_dir, file_name)
        target_path = f"/app/submissions/{file_name}"
        volumes[file_path] = {"bind": target_path, "mode": "ro"}
    container = client.containers.run(
        FINGERPRINTER_IMAGE,
        detach=True,
        network=NETWORK_NAME,
        environment={"PORT": str(fingerprinter_port)},
        volumes=volumes,
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


def stream_container_logs(
    container: docker.models.containers.Container, prefix: str = "[FINGERPRINTER]"
) -> None:
    for log_line in container.logs(stream=True, follow=True):
        logger.debug(f"{prefix} {log_line.decode('utf-8').strip()}")


def start_log_streaming_thread(
    container: docker.models.containers.Container, prefix: str = "[FINGERPRINTER]"
) -> Thread:
    thread = Thread(target=stream_container_logs, args=(container, prefix), daemon=True)
    thread.start()
    return thread
