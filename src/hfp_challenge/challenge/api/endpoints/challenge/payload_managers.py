from api.logger import logger
from api.config import config
from enum import Enum
from collections import defaultdict


class PayloadManager:
    def __init__(self):
        self.fingerprints: list[dict] = []

    def restart_manager(self) -> None:
        self.fingerprints = []

    def store_fingerprint(
        self, social_id: str, fingerprint: str, payload: dict
    ) -> None:
        # Parse social_id: testcase_sendername_device_browser
        parts = social_id.lower().split("_")
        if len(parts) != 4:
            logger.warning(f"Invalid social_id format: {social_id}")
            return

        testcase, sendername, device, browser = parts

        self.fingerprints.append(
            {
                "social_id": social_id,
                "testcase": testcase,
                "sendername": sendername,
                "device": device,
                "browser": browser,
                "fingerprint": fingerprint,
                "payload": payload,
            }
        )
        logger.info(f"Stored fingerprint for {social_id}")

    def get_fingerprints(self) -> list[dict]:
        return self.fingerprints

    def fingerprint_count(self) -> int:
        return len(self.fingerprints)

    def calculate_score(self) -> float:
        if not self.fingerprints:
            logger.warning("No fingerprints to score")
            return 0.0

        scoring_cfg = config.challenge.scoring

        # Group fingerprints by device-browser combination
        device_browser_fps = defaultdict(list)
        for fp in self.fingerprints:
            key = f"{fp['sendername']}_{fp['device']}_{fp['browser']}"
            device_browser_fps[key].append(fp)

        # Track fingerprints across device-browser combinations for collision detection
        # Key: (fingerprint, browser) -> set of device keys
        fp_to_devices = defaultdict(set)
        for key, fps in device_browser_fps.items():
            device_key = "_".join(key.split("_")[:-1])  # Remove browser from key
            browser = key.split("_")[-1]
            for fp in fps:
                fp_to_devices[(fp["fingerprint"], browser)].add(device_key)

        total_score = 0.0
        total_weight = 0.0

        # Calculate score for each fingerprint
        for fp in self.fingerprints:
            # Get weights
            testcase_weight = scoring_cfg.testcase_weights.get(fp["testcase"], 0.5)
            browser_weight = scoring_cfg.browser_weights.get(fp["browser"], 0.5)
            base_score = testcase_weight * browser_weight

            # Calculate fragmentation for this device-browser combination
            key = f"{fp['sendername']}_{fp['device']}_{fp['browser']}"
            unique_fps = {f["fingerprint"] for f in device_browser_fps[key]}
            fragmentation_count = len(unique_fps)

            # Calculate collision for this fingerprint within the same browser
            collision_count = len(fp_to_devices[(fp["fingerprint"], fp["browser"])])

            # Apply penalties
            score = base_score

            # Fragmentation penalty
            if fragmentation_count >= scoring_cfg.max_fragmentation_threshold:
                score = 0.0
            elif fragmentation_count > 1:
                score *= 1 - scoring_cfg.fragmentation_penalty * (
                    fragmentation_count - 1
                )

            # Collision penalty
            if collision_count >= scoring_cfg.max_collision_threshold:
                score = 0.0
            elif collision_count > 1:
                score *= 1 - scoring_cfg.collision_penalty * (collision_count - 1)

            total_score += max(0.0, score)
            total_weight += base_score

        # Normalize to 0-1
        if total_weight > 0:
            final_score = total_score / total_weight
        else:
            final_score = 0.0

        final_score = max(0.0, min(1.0, final_score))
        logger.info(f"Final score: {final_score:.3f}")
        return round(final_score, 3)


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
