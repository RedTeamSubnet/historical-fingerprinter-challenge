from api.logger import logger
from api.config import config
from enum import Enum
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional


@dataclass
class ScoringTelemetry:
    request_id: Optional[str] = None
    total_file_size_bytes: int = 0
    runtime_seconds: float = 0.0
    network_rx_bytes: int = 0
    network_tx_bytes: int = 0
    score: Optional[float] = None


class ScoringTelemetryManager:
    def __init__(self):
        self._latest: ScoringTelemetry = ScoringTelemetry()

    def set_telemetry(
        self,
        request_id: Optional[str] = None,
        total_file_size_bytes: int = 0,
        runtime_seconds: float = 0.0,
        network_rx_bytes: int = 0,
        network_tx_bytes: int = 0,
        score: Optional[float] = None,
    ) -> None:
        self._latest = ScoringTelemetry(
            request_id=request_id,
            total_file_size_bytes=total_file_size_bytes,
            runtime_seconds=runtime_seconds,
            network_rx_bytes=network_rx_bytes,
            network_tx_bytes=network_tx_bytes,
            score=score,
        )
        logger.info(
            f"[Telemetry] Recorded: runtime={runtime_seconds:.2f}s, "
            f"net_rx={network_rx_bytes}, net_tx={network_tx_bytes}"
        )

    def get_telemetry(self) -> ScoringTelemetry:
        return self._latest

    def reset(self) -> None:
        self._latest = ScoringTelemetry()


class PayloadManager:
    def __init__(self):
        self.fingerprints: list[dict] = []

    def restart_manager(self) -> None:
        self.fingerprints = []

    def store_fingerprint(
        self, social_id: str, fingerprint: str, payload: dict, request_id: str = None
    ) -> None:
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
                "request_id": request_id,
            }
        )

    def get_fingerprints(self) -> list[dict]:
        return self.fingerprints

    def fingerprint_count(self) -> int:
        return len(self.fingerprints)

    def calculate_score(self) -> float:
        if not self.fingerprints:
            logger.warning("No fingerprints to score")
            return 0.0

        scoring_cfg = config.challenge.scoring

        device_browser_fps = defaultdict(list)
        for fp in self.fingerprints:
            key = f"{fp['sendername']}_{fp['device']}_{fp['browser']}"
            device_browser_fps[key].append(fp)

        fp_to_devices = defaultdict(set)
        for key, fps in device_browser_fps.items():
            device_key = "_".join(key.split("_")[:-1])
            browser = key.split("_")[-1]
            for fp in fps:
                fp_to_devices[(fp["fingerprint"], browser)].add(device_key)

        total_score = 0.0
        total_weight = 0.0

        for fp in self.fingerprints:
            testcase_weight = scoring_cfg.testcase_weights.get(fp["testcase"], 0.5)
            browser_weight = scoring_cfg.browser_weights.get(fp["browser"], 0.5)
            base_score = testcase_weight * browser_weight

            key = f"{fp['sendername']}_{fp['device']}_{fp['browser']}"
            unique_fps = {f["fingerprint"] for f in device_browser_fps[key]}
            fragmentation_count = len(unique_fps)

            collision_count = len(fp_to_devices[(fp["fingerprint"], fp["browser"])])

            score = base_score

            if fragmentation_count >= scoring_cfg.max_fragmentation_threshold:
                score = 0.0
            elif fragmentation_count > 1:
                score *= 1 - scoring_cfg.fragmentation_penalty * (
                    fragmentation_count - 1
                )

            if collision_count >= scoring_cfg.max_collision_threshold:
                score = 0.0
            elif collision_count > 1:
                score *= 1 - scoring_cfg.collision_penalty * (collision_count - 1)

            total_score += max(0.0, score)
            total_weight += base_score

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
scoring_telemetry_manager = ScoringTelemetryManager()

__all__ = [
    "PayloadManager",
    "payload_manager",
    "ScoringStatusManager",
    "scoring_status_manager",
    "ScoringTelemetry",
    "ScoringTelemetryManager",
    "scoring_telemetry_manager",
]
