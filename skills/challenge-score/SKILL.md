---
name: challenge-score
description: Use for scoring current submissions and inspecting score-related endpoints.
---

# Purpose

This skill provides a reliable way to score the current submission files in this challenge repository and quickly inspect score-related outputs.

# Quick Start

From challenge root:

```bash
python3 skills/challenge-score/scripts/check_score.py
```

What it does:

1. Loads `HFP_CHALLENGE_API_KEY` from root `.env` (if present).
2. Reads submission files from `src/hfp_challenge/challenge/fingerprinter/src/submissions`.
3. Sends `POST http://localhost:10001/score` with `X-API-Key` header.
4. Prints score output (expected float from `0` to `1`).

# Important Files

- `skills/challenge-score/scripts/check_score.py` - local scoring helper script.
- `src/hfp_challenge/challenge/api/endpoints/challenge/schemas.py` - `MinerOutput` and score telemetry schema.
- `src/hfp_challenge/challenge/api/endpoints/challenge/router.py` - challenge endpoint definitions.
- `src/hfp_challenge/challenge/fingerprinter/src/submissions` - current submission files.

# Scoring System

The script builds payload using the same submission file pattern used by the challenge:

```json
{
  "miner_input": {
    "random_val": "<random string>"
  },
  "miner_output": {
    "commit_files": [
      {"file_name": "initializer.py", "content": "..."},
      {"file_name": "metrics_collector.py", "content": "..."},
      {"file_name": "linker.py", "content": "..."}
    ]
  }
}
```

`MinerOutput` constraints (from schema):

- `commit_files` is required.
- each item requires `file_name` and `content`.
- extension must be `.py`.
- names must match configured submission names.
- submitted file count must match configured expected count.
- each file must respect configured line limit.

Expected `/score` behavior:

- endpoint scores provided `miner_output`.
- response is a score float in `[0, 1]`.

# Do / Don't

Do:

- keep required file names stable (`initializer.py`, `metrics_collector.py`, `linker.py`).
- score after every meaningful submission change.
- inspect telemetry/results when score changes unexpectedly.

Don't:

- send partial `commit_files` payloads.
- rename submission files unless challenge config is updated accordingly.
- assume stale score state; rerun scoring after edits.

# Helper Scripts

- `python3 skills/challenge-score/scripts/check_score.py`
    - reads submissions
    - calls `/score`
    - prints score or raw error response

# Verification Steps

1. Ensure API server is running on `localhost:10001`.
2. Ensure root `.env` has `HFP_CHALLENGE_API_KEY`.
3. Run script and confirm numeric output between `0` and `1`.
4. Optional: inspect `GET /telemetry` and `GET /results` for deeper validation.

# Troubleshooting

- Missing file error:
    - confirm files exist in `src/hfp_challenge/challenge/fingerprinter/src/submissions`.
- Auth failure:
    - confirm `HFP_CHALLENGE_API_KEY` value in root `.env`.
- Validation error:
    - compare payload to `MinerOutput` in `src/hfp_challenge/challenge/api/endpoints/challenge/schemas.py`.
- Connection error:
    - verify local API is reachable at `http://localhost:10001`.
- Need detailed scoring breakdown:
    - inspect Docker container logs for the challenge API/scorer service; logs include deeper scoring and failure details.

# Related Endpoints

From `src/hfp_challenge/challenge/api/endpoints/challenge/router.py`:

- `GET /task` - returns current miner input(which is random string in each call).
- `POST /score` - scores submission payload.
- `GET /status` - current scoring status.
- `GET /results` - stored fingerprint results.
- `GET /telemetry` - latest scoring telemetry (`request_id`, runtime, network bytes, score).

# Expected Success States

- scoring script exits with code `0`.
- output is a float score in `[0, 1]`.
- telemetry endpoint shows latest run metrics with a populated `score`.
