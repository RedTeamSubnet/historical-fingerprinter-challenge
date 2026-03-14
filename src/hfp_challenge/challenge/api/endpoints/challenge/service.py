import json
import os
import tempfile

import pandas as pd
import requests
from pydantic import validate_call

from api.config import config
from api.logger import logger

from api.endpoints.challenge import _utils
from .schemas import MinerInput, MinerOutput

FINGERPRINT_STORAGE: dict[str, str] = {}


def get_task() -> MinerInput:
    return MinerInput()


@validate_call
def score(request_id: str, miner_output: MinerOutput) -> None:
    global FINGERPRINT_STORAGE

    if _utils.get_scoring_status() == _utils.ScoringStatus.SCORING:
        raise RuntimeError("Scoring is already in progress")

    FINGERPRINT_STORAGE = {}
    _request_miss_counter = 0
    container = None

    _utils.set_scoring_status(_utils.ScoringStatus.SCORING)

    with tempfile.TemporaryDirectory() as tmp_dir:
        for file in miner_output.commit_files:
            file_path = os.path.join(tmp_dir, f"{file.file_name}.py")
            with open(file_path, "w") as f:
                f.write(file.content)

        try:
            container, ip_address = _utils.run_fingerprinter_container(
                request_id=request_id,
                files_dir=tmp_dir,
            )

            config.challenge.fingerprinter_ip = ip_address
            logger.info(
                f"[{request_id}] - Fingerprinter container started at {ip_address}"
            )

            _utils.wait_for_health(
                ip_address, fingerprinter_port=config.challenge.fingerprinter_port
            )
            logger.info(f"[{request_id}] - Fingerprinter container is healthy")

            base_url = f"http://{ip_address}:{config.challenge.fingerprinter_port}"
            df = pd.read_csv(config.challenge.metrics_csv_path)
            for index, row in df[["social_id", "user_metrics"]].iterrows():
                logger.info(f"{index} is started")
                social_id = str(row["social_id"])
                user_metrics = json.loads(str(row["user_metrics"]))
                try:
                    resp = requests.post(
                        f"{base_url}/fingerprint",
                        json={"products": user_metrics},
                        timeout=config.challenge.single_request_timeout,
                    )
                    resp.raise_for_status()
                    fingerprint = resp.json().get("fingerprint")
                    if fingerprint:
                        FINGERPRINT_STORAGE[social_id] = fingerprint
                        logger.info(
                            f"[{request_id}] - Stored fingerprint for {social_id}"
                        )
                    else:
                        logger.warning(
                            f"[{request_id}] - No fingerprint returned for {social_id}"
                        )
                except requests.RequestException as e:
                    _request_miss_counter += 1
                    logger.error(
                        f"[{request_id}] - Error during fingerprint request for {social_id}: {str(e)}"
                    )
                if _request_miss_counter > config.challenge.max_request_misses:
                    logger.error(
                        f"[{request_id}] - Exceeded max request misses. Stopping fingerprinting."
                    )
                    break
                logger.info(f"{index} is finished")

            logger.info(
                f"[{request_id}] - Fingerprinting completed. Stored {len(FINGERPRINT_STORAGE)} fingerprints"
            )

        finally:
            if container:
                _utils.cleanup_container(container)
                logger.info(f"[{request_id}] - Fingerprinter container cleaned up")
            _utils.set_scoring_status(_utils.ScoringStatus.AVAILABLE)

    return None


__all__ = [
    "get_task",
    "score",
]
