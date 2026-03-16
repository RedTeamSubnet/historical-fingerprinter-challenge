from api.logger import logger
from enum import Enum


class PayloadManager:
    def __init__(self):
        self.fingerprints: dict[str, str] = {}

    def restart_manager(self) -> None:
        self.fingerprints = {}

    def store_fingerprint(self, social_id: str, fingerprint: str) -> None:
        self.fingerprints[social_id] = fingerprint
        logger.info(f"Stored fingerprint for {social_id}")

    def get_fingerprints(self) -> dict[str, str]:
        return self.fingerprints

    def fingerprint_count(self) -> int:
        return len(self.fingerprints)


class ScoringStatus(str, Enum):
    STARTED = "started"
    SCORING = "scoring"
    AVAILABLE = "available"


class ScoringStatusManager:
    def __init__(self):
        self._scoring_status = ScoringStatus.STARTED

    def get_scoring_status(self) -> ScoringStatus:
        return self._scoring_status

    def set_scoring_status(self, status: ScoringStatus) -> None:
        self._scoring_status = status


payload_manager = PayloadManager()
scoring_status_manager = ScoringStatusManager()

__all__ = [
    "PayloadManager",
    "payload_manager",
    "ScoringStatusManager",
    "scoring_status_manager",
]
