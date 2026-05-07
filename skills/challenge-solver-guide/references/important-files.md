# Important Files

Use these files first when solving this challenge.

## Submission entry points (your code)

- `src/hfp_challenge/challenge/fingerprinter/src/submissions/initializer.py`
    - creates/updates SQLite schema for fingerprint storage.
    - add indexes and helper columns here for faster candidate lookup.
- `src/hfp_challenge/challenge/fingerprinter/src/submissions/metrics_collector.py`
    - transforms raw CreepJS payload (`products`) into normalized stable metrics.
    - this is where robust feature extraction should live.
- `src/hfp_challenge/challenge/fingerprinter/src/submissions/linker.py`
    - performs linking logic (new vs known device) and persistence.
    - this is where anti-fragmentation and anti-collision decisions should live.

## Runtime and API flow

- `src/hfp_challenge/challenge/fingerprinter/src/app.py`
    - `/fingerprint` flow: preprocess -> fingerprint generation -> link.
    - default implementation hashes full normalized payload; improving logic usually requires changing this path or the submission behavior around it.
- `src/hfp_challenge/challenge/fingerprinter/src/data_types.py`
    - request/response schema for fingerprinter service.

## Scoring and dataset behavior

- `src/hfp_challenge/challenge/api/endpoints/challenge/service.py`
    - runs your submission in a container, replays dataset rows, tracks misses/timeouts, computes final score.
- `src/hfp_challenge/challenge/api/endpoints/challenge/payload_managers.py`
    - score composition and penalties:
        - collision score (40%)
        - fragmentation score (40%)
        - weighted testcase score (20%)
    - if collision or fragmentation score reaches 0, final score becomes 0.
- `src/hfp_challenge/challenge/api/core/configs/_challenge.py`
    - challenge config: request timeout, acceptable misses, testcase weights, penalties, submission file names.

## Local operations

- `skills/challenge-setup/SKILL.md`
    - setup/run/health checks and environment guidance.
- `skills/challenge-score/SKILL.md`
    - scoring flow and endpoint references.
- `skills/challenge-score/scripts/check_score.py`
    - quick local score command.
