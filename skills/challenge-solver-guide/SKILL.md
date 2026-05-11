---
name: challenge-solver-guide
description: Use for designing and implementing high-score fingerprint linking submissions for this challenge.
---

# Purpose

Guide agents to solve the Historical Fingerprinter challenge with production-grade linking logic, not simplistic hashing.

Primary objective:

- maximize score by reducing both collision and fragmentation under realistic browser/device variability.

# Quick Start

1. Set up and run challenge services:
   - `./skills/challenge-setup/scripts/setup.sh`
   - `./skills/challenge-setup/scripts/healthcheck.sh`
2. Implement changes only in submission files:
   - `initializer.py`, `metrics_collector.py`, `linker.py`
3. Score after each meaningful iteration:
   - `python3 skills/challenge-score/scripts/check_score.py`
4. Inspect diagnostics:
   - `GET /telemetry`, `GET /results`, and container logs.

# Important Files

See full map in:

- `skills/challenge-solver-guide/references/important-files.md`

Core challenge data/input locations:

- dataset used by scoring replay: `volumes/storage/historical_fingerprinter/data/metrics.csv`
- required submission implementation directory: `src/hfp_challenge/challenge/fingerprinter/src/submissions`

Submission location is mandatory for local scoring flow because the score helper reads files from that submissions directory.

# Architecture Overview

High-level pipeline:

1. Challenge API `/score` receives your submitted files.
2. API spins up a fingerprinter container with those files mounted.
3. Dataset rows are replayed; each row sends CreepJS `products` payload to `/fingerprint`.
4. Fingerprinter runs:
   - `preprocess_metrics` -> payload normalization
   - server fingerprint creation
   - `generate_and_link` persistence + matching
5. API computes final score from collisions, fragmentation, and weighted testcase success.

Implementation implication:

- strong solutions need robust normalization + probabilistic linking, not direct raw-payload hashing.

# Scoring System

Current scoring composition (`payload_managers.py`):

- collision score: 40%
- fragmentation score: 40%
- weighted testcase score: 20%

Hard failure behavior:

- if collision score is `0.0` or fragmentation score is `0.0`, final score is forced to `0.0`.
- if request misses exceed `HFP_CHALLENGE_ACCEPTABLE_MISS_COUNT`, score becomes `0.0`.

Weighted testcases (from config) emphasize harder scenarios:

- anti-fingerprint browser
- timezone change
- language change
- incognito + vpn/proxy combinations

Optimization priority:

- keep collision and fragmentation both below threshold first.
- then improve weighted-case robustness.

# Solver Workflow

1. Baseline
   - run current score and capture telemetry.
2. Feature strategy
   - identify stable features and unstable/noisy features.
   - define canonical normalization rules.
3. Linking strategy
   - implement two-stage linking:
     - exact/high-confidence key
     - weighted similarity with threshold bands
4. Data model updates
   - add DB indexes or helper columns in `initializer.py` for candidate lookup.
5. Iterate
   - run scoring, inspect errors, compare collisions vs fragmentation effects.
6. Harden
   - ensure logic handles spoofing, partial tampering, and missing fields gracefully.

# Investigation Priorities

1. Robust feature extraction in `metrics_collector.py`
   - canonicalize lists/strings/booleans/numbers.
   - generate compact stable signatures from multi-field combinations.
2. Adaptive matching in `linker.py`
   - exact on strongest anchors, fuzzy on secondary features.
   - avoid both over-merge (collision) and over-split (fragmentation).
3. Storage/query ergonomics in `initializer.py`
   - schema fields for signatures and confidence metadata.
   - indexes for frequent candidate queries.
4. Failure resilience
   - guard against malformed payloads and missing optional keys.

# Common Vulnerability Patterns

- Over-collision pattern:
    - broad fingerprints from too few features (for example only UA/platform/screen).
- Over-fragmentation pattern:
    - strict equality over volatile fields (timezone, language order, incognito artifacts).
- Anti-fingerprint blind spots:
    - trusting spoofable browser claims without cross-signal consistency checks.
- Noise amplification:
    - including transient fields as primary identity anchors.

# Challenge-Specific Hints

- Dataset is intentionally high-variance and realistic:
    - multiple device types, browsers, IP changes, timezone changes, and anti-fingerprint behavior.
- Treat identity as a confidence problem:
    - combine stable hardware-leaning signals with tolerant thresholds.
- Use consistency checks:
    - penalize improbable combinations instead of hard failing immediately.
- Prefer graceful degradation:
    - when high-confidence match fails, attempt secondary matching before creating new identity.

# Do / Don't

See:

- `skills/challenge-solver-guide/references/do-and-dont.md`

# Helper Scripts

- Setup:
    - `./skills/challenge-setup/scripts/setup.sh`
    - `./skills/challenge-setup/scripts/healthcheck.sh`
- Score:
    - `python3 skills/challenge-score/scripts/check_score.py`

# Verification Steps

1. Run scoring script and record float score in `[0, 1]`.
2. Check `GET /telemetry` for runtime, network usage, and reported score.
3. Check `GET /results` shape to confirm fingerprints are produced consistently.
4. Review container logs when behavior is unexpected:
   - `docker compose logs -f challenge-api`
5. Repeat after each strategic change and compare score deltas.

# Troubleshooting

- Score drops to zero suddenly:
    - likely collision/fragmentation threshold breach or miss-count overflow.
- Many request errors/timeouts:
    - simplify expensive logic and keep runtime predictable.
- No meaningful improvement after changes:
    - rebalance matching thresholds and feature stability assumptions.
- Inconsistent local results:
    - reset environment, rerun setup, and validate `.env` + API key.

# Example Requests

- "Analyze current submission logic and propose a collision/fragmentation reduction plan."
- "Implement stable feature normalization for CreepJS payload and explain why each feature is selected."
- "Refactor linker to use exact + weighted fuzzy matching with confidence thresholds."
- "Run score, inspect telemetry, and explain the most likely bottleneck for higher weighted testcase performance."

# Expected Success States

- score is consistently non-zero and trending upward across iterations.
- misses stay below `HFP_CHALLENGE_ACCEPTABLE_MISS_COUNT`.
- linking logic handles slight payload drift without excessive fragmentation.
- stronger resistance to spoofing/tampering than simple UA/browser hashing baselines.
