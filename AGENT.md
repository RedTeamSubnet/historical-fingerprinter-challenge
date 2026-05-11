# AGENT Guide

This repository is a RedTeam Historical Fingerprinter challenge.

Use this guide as the default operating playbook for any coding agent working in this repo.

## Challenge Summary

- Goal: implement robust device fingerprint linking under realistic noise.
- Input: each request contains full CreepJS-style payload (`products`).
- Output: return stable fingerprint IDs that link the same device across slight changes while avoiding cross-device merges.
- Score drivers:
    - low collision (different devices should not collapse into one fingerprint)
    - low fragmentation (same device should not split into many fingerprints)
    - strong performance in hard weighted scenarios (anti-fingerprint browser, timezone/language changes, vpn/proxy, incognito).

## Where To Implement

Only submission files are intended for solver logic:

- `src/hfp_challenge/challenge/fingerprinter/src/submissions/initializer.py`
- `src/hfp_challenge/challenge/fingerprinter/src/submissions/metrics_collector.py`
- `src/hfp_challenge/challenge/fingerprinter/src/submissions/linker.py`

Important:

- keep solver implementation inside `src/hfp_challenge/challenge/fingerprinter/src/submissions`.
- scoring helpers retrieve submission files from this path.

Challenge dataset used during scoring replay:

- `volumes/storage/historical_fingerprinter/data/metrics.csv`

Execution flow:

1. `preprocess_metrics` transforms raw metrics.
2. server fingerprint path runs.
3. `generate_and_link` decides existing vs new identity and persists data.

## Scoring Behavior (Important)

Scoring is computed from:

- collision score: 40%
- fragmentation score: 40%
- weighted testcase score: 20%

Critical rules:

- if collision score is `0.0` OR fragmentation score is `0.0`, final score is forced to `0.0`.
- if request misses exceed `HFP_CHALLENGE_ACCEPTABLE_MISS_COUNT`, final score is `0.0`.

Keep logic efficient and resilient to avoid request failures/timeouts.

## Skills

### 1) challenge-setup

- Location: `skills/challenge-setup/SKILL.md`
- Scripts:
    - `skills/challenge-setup/scripts/setup.sh`
    - `skills/challenge-setup/scripts/healthcheck.sh`
- Use when:
    - preparing local environment
    - validating `.env` and API availability
    - booting challenge services with Docker Compose
- Quick usage:
    - `./skills/challenge-setup/scripts/setup.sh`
    - `./skills/challenge-setup/scripts/setup.sh --build`
    - `./skills/challenge-setup/scripts/healthcheck.sh`

### 2) challenge-score

- Location: `skills/challenge-score/SKILL.md`
- Script: `skills/challenge-score/scripts/check_score.py`
- Use when:
    - running `/score` against current submissions
    - validating payload schema expectations
    - checking endpoint-level score behavior quickly
- Quick usage:
    - `python3 skills/challenge-score/scripts/check_score.py`

### 3) challenge-solver-guide

- Location: `skills/challenge-solver-guide/SKILL.md`
- References:
    - `skills/challenge-solver-guide/references/important-files.md`
    - `skills/challenge-solver-guide/references/do-and-dont.md`
- Use when:
    - designing robust linking logic
    - deciding stable features vs noisy features
    - planning iterations to reduce both collision and fragmentation

## Agent Workflow (Recommended)

1. Setup
   - run challenge setup + health check.
2. Baseline
   - run score script and record score.
3. Analyze
   - inspect submission logic and scoring implications.
4. Implement
   - update normalization/linking/persistence strategy in submissions.
5. Re-score
   - run score script after each meaningful change.
6. Diagnose
   - use telemetry/results and logs to understand regressions.
7. Iterate
   - tune thresholds/features for better collision-fragmentation balance.

## Key Endpoints

- `POST /score` - evaluates current submission package.
- `GET /status` - scoring state.
- `GET /results` - stored scoring/fingerprint outcomes.
- `GET /telemetry` - runtime, network, size, score metrics.
- `GET /task` - returns current task input shape.

## Environment Notes

- `HFP_CHALLENGE_API_KEY` is required for protected challenge endpoints.
- `DEBUG=true` increases logs and helps troubleshooting.
- For final production-grade validation, do not alter:
    - `HFP_CHALLENGE_ACCEPTABLE_MISS_COUNT`
    - `HFP_CHALLENGE_SINGLE_REQUEST_TIMEOUT`

## Debugging

- API/container startup issues:
    - `docker compose ps`
    - `docker compose logs -f challenge-api`
- Scoring anomalies:
    - check `/telemetry` and `/results`
    - inspect collision/fragmentation side effects in linking rules
- Runtime failures:
    - reduce expensive operations in request path
    - handle missing/malformed fields defensively

## Solver Quality Bar

Avoid simplistic approaches (for example plain user-agent hashing).

Preferred approach:

- robust feature extraction from stable signals
- canonical normalization
- multi-stage matching (exact + weighted fuzzy)
- careful thresholds to prevent both over-merge and over-split
- resilience to spoofing/tampering and minor payload drift
