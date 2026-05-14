from api.logger import logger
from api.config import config
from enum import Enum
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class ScoringTelemetry:
    request_id: str | None = None
    total_file_size_bytes: int = 0
    runtime_seconds: float = 0.0
    network_rx_bytes: int = 0
    network_tx_bytes: int = 0
    score: float | None = None


class ScoringTelemetryManager:
    def __init__(self):
        self._latest: ScoringTelemetry = ScoringTelemetry()

    def set_telemetry(
        self,
        request_id: str | None = None,
        total_file_size_bytes: int = 0,
        runtime_seconds: float = 0.0,
        network_rx_bytes: int = 0,
        network_tx_bytes: int = 0,
        score: float | None = None,
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
        self._scores_breakdown: dict[str, float] = {}

    def restart_manager(self) -> None:
        self.fingerprints = []
        self._scores_breakdown = {}

    def store_scores_breakdown(
        self, collision_score: float, fragmentation_score: float, weighted_score: float
    ):
        self._scores_breakdown = {
            "collision_score": collision_score,
            "fragmentation_score": fragmentation_score,
            "weighted_score": weighted_score,
        }

    def get_scores_breakdown(self) -> dict[str, float]:
        return self._scores_breakdown

    def store_fingerprint(
        self,
        social_id: str,
        fingerprint: str,
        payload: dict,
        request_id: str = None,
        unique_device: str | None = None,
        test_case: str | None = None,
        browser: str | None = None,
        username: str | None = None,
        device_model: str | None = None,
    ) -> None:
        normalized_unique_device = (unique_device or "").strip().lower()
        normalized_test_case = (test_case or "").strip().lower()
        normalized_browser = (browser or "").strip().lower()

        if not normalized_unique_device:
            logger.warning(f"Missing unique_device for social_id: {social_id}")
            return

        self.fingerprints.append(
            {
                "social_id": social_id,
                "testcase": normalized_test_case,
                "sendername": (username or "").strip().lower(),
                "device": (device_model or "").strip().lower(),
                "browser": normalized_browser,
                "unique_device": normalized_unique_device,
                "fingerprint": fingerprint,
                "payload": payload,
                "request_id": request_id,
            }
        )

    def get_fingerprints(self) -> list[dict]:
        return self.fingerprints

    def fingerprint_count(self) -> int:
        return len(self.fingerprints)

    def calculate_score(self) -> tuple[float, float, float, float]:
        if not self.fingerprints:
            logger.warning("No fingerprints to score")
            return 0.0, 0.0, 0.0, 0.0

        scoring_cfg = config.challenge.scoring

        collision_score, collided_fps = self.score_collision(
            self.fingerprints, scoring_cfg.max_collision_threshold
        )
        fragmentation_score, fragmented_fps = self.score_fragmentation(
            self.fingerprints,
            collided_fps,
            scoring_cfg.max_fragmentation_threshold,
        )
        weighted_score = self.score_testcase_n_browser(
            self.fingerprints,
            scoring_cfg.testcase_weights,
            collided_fps,
        )
        logger.info(
            f"Scores - Collision: {collision_score} \nFragmentation: {fragmentation_score} \nWeighted: {weighted_score}"
        )
        if collision_score == 0.0 or fragmentation_score == 0.0:
            final_score = 0.0
        else:
            final_score = (
                (collision_score * 0.4)
                + (fragmentation_score * 0.4)
                + (weighted_score * 0.2)
            )
        return final_score, collision_score, fragmentation_score, weighted_score

    def score_collision(
        self,
        fingerprints,
        collision_threshold_percent=0.1,
    ):
        _collided_fingerprints = []
        _collision_tracker = defaultdict(lambda: defaultdict(int))
        if not fingerprints:
            logger.warning("No fingerprints to score")
            return 0.0
        for fp in fingerprints:
            key = fp["unique_device"]
            _collision_tracker[key][fp["fingerprint"]] += 1
        _sorted_collision_tracker = {
            k: dict(sorted(v.items(), key=lambda item: item[1], reverse=True))
            for k, v in _collision_tracker.items()
        }
        _collided_fingerprints_count = 0
        for key, collisions in _sorted_collision_tracker.items():
            if len(collisions) > 1:
                for index, (fingerprint, count) in enumerate(collisions.items()):
                    if index >= 1:
                        _collided_fingerprints_count += count
                        if fingerprint not in _collided_fingerprints:
                            _collided_fingerprints.append(fingerprint)
        _collision_percentile = _collided_fingerprints_count / len(fingerprints)
        if _collision_percentile > collision_threshold_percent:
            return 0.0, _collided_fingerprints
        _collision_score = 1 - (_collision_percentile / collision_threshold_percent)

        return round(_collision_score, 3), _collided_fingerprints

    def score_fragmentation(
        self,
        fingerprints,
        fragmented_fingerprints: list,
        fragmentation_threshold_percent=0.1,
    ):
        _collision_tracker = defaultdict(lambda: defaultdict(int))

        if not fingerprints:
            logger.warning("No fingerprints to score")
            return 0.0
        for fp in fingerprints:
            key = fp["unique_device"]
            _collision_tracker[fp["fingerprint"]][key] += 1
        _sorted_fragmentation_tracker = {
            k: dict(sorted(v.items(), key=lambda item: item[1], reverse=True))
            for k, v in _collision_tracker.items()
        }
        _fragmented_fingerprints_count = 0
        for key, collisions in _sorted_fragmentation_tracker.items():
            if len(collisions) > 1:
                for index, (_fingerprint, count) in enumerate(collisions.items()):
                    if index >= 1:
                        _fragmented_fingerprints_count += count
                        if _fingerprint not in fragmented_fingerprints:
                            fragmented_fingerprints.append(_fingerprint)
        _fragmentation_percentile = _fragmented_fingerprints_count / len(fingerprints)

        if _fragmentation_percentile > fragmentation_threshold_percent:
            return 0.0, fragmented_fingerprints
        _fragmentation_score = 1 - (
            _fragmentation_percentile / fragmentation_threshold_percent
        )

        return round(_fragmentation_score, 3), fragmented_fingerprints

    def score_testcase_n_browser(
        self,
        fingerprints,
        testcase_weights: dict,
        invalid_fingerprints,
    ):
        _total_weight = 0
        valid_weights = 0
        if not fingerprints:
            logger.warning("No fingerprints to score")
            return 0.0
        for fp in fingerprints:
            testcase = fp["testcase"]
            _current_weight = testcase_weights.get(testcase, 1)
            if fp["fingerprint"] in invalid_fingerprints:
                _total_weight += _current_weight
                continue
            valid_weights += _current_weight
            _total_weight += _current_weight

        if _total_weight == 0:
            return 0.0
        return valid_weights / _total_weight


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
