import traceback
import requests

import bittensor as bt

from redteam_core.validator.models import MinerChallengeCommit, ScoringLog
from redteam_core.challenge_pool.controller import Controller
from redteam_core.challenge_pool import docker_utils
from redteam_core.config.main import constants


class HFPController(Controller):

    def __init__(
        self,
        challenge_name: str,
        challenge_info: dict,
        miner_commits: list[MinerChallengeCommit],
        reference_comparison_commits: list[MinerChallengeCommit],
        seed_inputs: list[dict] = [],
    ):

        super().__init__(
            challenge_name,
            challenge_info,
            miner_commits,
            reference_comparison_commits,
            seed_inputs,
        )
        comparison_config = self.challenge_info.get("comparison_config", {})
        self.comparison_min_acceptable_score = comparison_config.get(
            "min_acceptable_score", 0.6
        )

    def start_challenge(self):
        """
        Initiates the challenge lifecycle by setting up and executing the challenge Docker container.

        This process involves:
        1. Building and running the challenge container within an isolated Docker network.
        2. Generating or retrieving challenge inputs to evaluate miners.
        3. Iteratively running each miner's Docker container to submit and score their solutions.
        4. Collecting and logging the results, including any errors encountered during execution.
        5. Cleaning up Docker resources to ensure no residual containers or images remain.

        The method ensures that each miner's submission is evaluated against the challenge inputs,
        and comparison logs are generated to assess performance relative to reference commits.
        """
        if self._is_scoring_in_progress():
            bt.logging.info(
                "[CONTROLLER] Skipping start_challenge because the status endpoint reports scoring"
            )
            return None

        self._setup_challenge()

        num_task = self.challenge_info.get(
            "num_tasks", constants.N_CHALLENGES_PER_EPOCH
        )
        # Start with seed inputs and generate more if needed to reach num_task
        challenge_inputs = self.seed_inputs.copy()
        remaining_tasks = max(0, num_task - len(challenge_inputs))
        if remaining_tasks > 0:
            challenge_inputs.extend(
                [self._get_challenge_from_container() for _ in range(remaining_tasks)]
            )

        bt.logging.debug(
            f"[CONTROLLER] Generated {len(challenge_inputs)} challenge inputs"
        )

        for miner_commit in self.miner_commits:
            uid, hotkey = miner_commit.miner_uid, miner_commit.miner_hotkey

            try:
                self._setup_miner_container(miner_commit)

                self._generate_scoring_logs(miner_commit, challenge_inputs)

                self._run_reference_comparison_inputs(miner_commit)

                self._score_miner_with_new_inputs(miner_commit, challenge_inputs)

            except Exception as e:
                bt.logging.error(f"Error while processing miner {uid} - {hotkey}: {e}")
                bt.logging.error(traceback.format_exc())
                if not miner_commit.scoring_logs:
                    miner_commit.scoring_logs.append(
                        ScoringLog(
                            miner_input=None,
                            miner_output=None,
                            score=0,
                            error=str(e),
                        )
                    )

            docker_utils.remove_container_by_port(
                client=self.docker_client,
                port=constants.MINER_DOCKER_PORT,
            )
            docker_utils.clean_docker_resources(
                client=self.docker_client,
                remove_containers=True,
                remove_images=False,
            )

        bt.logging.debug(
            "[CONTROLLER] Challenge completed, cleaning up challenge container"
        )

        docker_utils.remove_container(
            client=self.docker_client,
            container_name=self.challenge_name,
            stop_timeout=10,
            force=True,
            remove_volumes=True,
        )
        docker_utils.clean_docker_resources(
            client=self.docker_client,
            remove_containers=True,
            remove_images=False,
        )

    def _score_miner_with_new_inputs(
        self, miner_commit: MinerChallengeCommit, challenge_inputs
    ) -> None:
        _scoring_log = miner_commit.scoring_logs[0]
        for i, miner_input in enumerate(challenge_inputs):

            _higest_comparison_score = miner_commit.get_higest_comparison_score()
            if (
                _higest_comparison_score >= self.comparison_min_acceptable_score
                or _higest_comparison_score == 0.0
            ):
                bt.logging.info(
                    f"[CONTROLLER - MyController] Skipping scoring for miner {miner_commit.miner_hotkey} on task {i} "
                    f"due to high comparison score: {_higest_comparison_score}"
                )
                _scoring_log.score = 0.0
                if _scoring_log.error:
                    _scoring_log.error += (
                        " | Skipped scoring due to high comparison score."
                    )
                else:
                    _scoring_log.error = "Skipped scoring due to high comparison score."
                continue

            score = (
                self._score_challenge(
                    miner_input=miner_input,
                    miner_output=_scoring_log.miner_output,
                    task_id=i,
                )
                if _scoring_log.miner_output is not None
                else 0.0
            )

            _scoring_log.score = score

        return

    def _exclude_output_keys(self, miner_output: dict, reference_output: dict) -> None:
        miner_output["commit_files"] = None
        reference_output["commit_files"] = None

    def _is_scoring_in_progress(self) -> bool:
        """Check if the external challenge status endpoint reports active scoring."""

        status_url = "http://localhost:100001/status"
        try:
            response = requests.get(status_url, timeout=5, verify=False)  # nosec
            response.raise_for_status()
            payload = response.json() if response.content else {}
        except Exception as exc:
            bt.logging.debug(
                f"[CONTROLLER] Unable to reach challenge status endpoint ({exc}); continuing"
            )
            return False

        status_value = None
        if isinstance(payload, dict):
            status_value = payload.get("status") or payload.get("state")

        if isinstance(status_value, str) and status_value.lower() == "scoring":
            bt.logging.warning(
                "[CONTROLLER] Challenge status endpoint reports scoring in progress"
            )
            return True

        return False


__all__ = [
    "HFPController",
]
