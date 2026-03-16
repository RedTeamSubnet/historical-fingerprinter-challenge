from api.logger import logger


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


payload_manager = PayloadManager()

__all__ = [
    "PayloadManager",
    "payload_manager",
]
