# Do and Don't

## Do

- design for identity stability across noisy sessions (timezone changes, language changes, VPN/proxy, incognito, anti-fingerprint browsers).
- prioritize hardware-leaning and hard-to-spoof signals over high-variance surface signals.
- normalize aggressively (case, formatting, ordering, missing/null handling, bounded numeric buckets).
- build multi-stage matching in `linker.py`:
    - exact stable-key match first
    - weighted similarity match second
    - cautious fallback/new identity last
- persist intermediate signatures/features in DB to support faster candidate retrieval and repeatable matching.
- use thresholds with confidence bands instead of binary all-or-nothing checks.
- tune for both:
    - low collision (different devices should not collapse)
    - low fragmentation (same device should not split)
- iterate with score feedback and endpoint telemetry/logs after each meaningful change.

## Don't

- do not rely on only user-agent hashing or browser-level identity.
- do not overfit to a single browser or a single test case.
- do not include unstable network/session data (raw IP, transient values) as hard identity anchors.
- do not treat every small payload drift as a new fingerprint.
- do not make linking rules too permissive; high recall with poor precision causes collisions.
- do not ignore miss/timeout behavior; request failures can zero out final score if misses exceed limits.
- do not change production-parity scoring env values for final validation (`HFP_CHALLENGE_ACCEPTABLE_MISS_COUNT`, `HFP_CHALLENGE_SINGLE_REQUEST_TIMEOUT`).
