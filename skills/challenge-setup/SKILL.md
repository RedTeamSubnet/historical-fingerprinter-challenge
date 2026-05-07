---
name: challenge-setup
description: Use for local challenge environment setup, boot, and health checks.
---

# Purpose

Set up and run the Historical Fingerprinter challenge locally with Docker Compose, validate required environment variables, and verify service health.

# Quick Start

From challenge root:

```bash
./skills/challenge-setup/scripts/setup.sh
./skills/challenge-setup/scripts/healthcheck.sh
```

Build image before start (optional):

```bash
./skills/challenge-setup/scripts/setup.sh --build
```

# Important Files

- `compose.yml` - runs `challenge-api` service on `HFP_CHALLENGE_API_PORT` (default `10001`).
- `.env` - runtime environment values loaded by Docker Compose and helper scripts.
- `.env.example` - template for initial environment setup.
- `skills/challenge-setup/scripts/setup.sh` - setup and boot helper.
- `skills/challenge-setup/scripts/healthcheck.sh` - API reachability checks.

# Requirements

Required before setup:

- Docker
- Docker Compose plugin (`docker compose`)

Optional for development workflow (from README):

- Python >= 3.10 and pip >= 23
- git
- SSH key (if cloning with SSH)

# Setup Workflow

1. Ensure dependencies are installed.
2. Ensure `.env` exists (script auto-copies from `.env.example` when missing).
3. Confirm `HFP_CHALLENGE_API_KEY` is defined.
4. Start with `docker compose up` (optionally `--build`).
5. Run health checks for `/ping` and `/health`.

# Environment Variables

Critical:

- `HFP_CHALLENGE_API_KEY`
    - Required for protected challenge endpoints (for example: `/score`).
    - Setup script fails fast if this key is missing.

Debugging:

- `DEBUG`
    - When enabled (for example `DEBUG=true`), debug mode increases log verbosity.
    - Useful for inspecting fingerprinter execution behavior during development.

Production-parity caution:

- `HFP_CHALLENGE_ACCEPTABLE_MISS_COUNT`
- `HFP_CHALLENGE_SINGLE_REQUEST_TIMEOUT`

Do not change these for production-grade score validation. You may tune them temporarily for local development, but final checks should use production-like values.

# Do / Don't

Do:

- keep `HFP_CHALLENGE_API_KEY` set before scoring.
- run healthcheck after every setup/start.
- use `--build` when Docker image or dependencies changed.

Don't:

- rely on modified timeout/miss-count values for final score conclusions.
- skip checking container logs when API behavior is unexpected.

# Helper Scripts

- `./skills/challenge-setup/scripts/setup.sh`
    - validates Docker + Compose
    - ensures `.env`
    - validates `HFP_CHALLENGE_API_KEY`
    - starts challenge service

- `./skills/challenge-setup/scripts/healthcheck.sh`
    - checks `GET /ping`
    - checks `GET /health`
    - prints docs and OpenAPI URLs

# Verification Steps

1. Run `./skills/challenge-setup/scripts/setup.sh`.
2. Run `./skills/challenge-setup/scripts/healthcheck.sh`.
3. Open:
   - `http://localhost:10001/docs`
   - `http://localhost:10001/openapi.json`

# Troubleshooting

- Setup fails with missing API key:
    - add `HFP_CHALLENGE_API_KEY` to `.env`.
- API not reachable:
    - check `docker compose ps` and ensure port `10001` mapping is active.
- Need deeper execution details:
    - inspect Docker logs of the running challenge container for scoring/runtime traces.
    - example: `docker compose logs -f challenge-api`

# Expected Success States

- `docker compose ps` shows `challenge-api` as running.
- `GET /ping` and `GET /health` return success.
- API docs are accessible on `http://localhost:10001/docs`.
