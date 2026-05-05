import sys
import logging
import hashlib
import json
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Body, HTTPException, Request

from data_types import FingerprintInput, FingerprintOutput
from submissions import initialize_db, generate_and_link, preprocess_metrics

logger = logging.getLogger(__name__)
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S %z",
    format="[%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d]: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = initialize_db()
    logger.info("Database connection initialized")
    yield
    app.state.db.close()
    logger.info("Database connection closed")


app = FastAPI(lifespan=lifespan)


def _generate_server_fingerprint(payload: dict[str, Any]) -> str:
    normalized: dict[str, str] = {}
    for key, value in payload.items():
        if value is None:
            normalized[key] = ""
        elif isinstance(value, bool):
            normalized[key] = "1" if value else "0"
        elif isinstance(value, (int, float)):
            normalized[key] = str(value)
        else:
            normalized[key] = str(value).lower().strip()

    sorted_json = json.dumps(normalized, sort_keys=True)
    fingerprint = hashlib.sha256(sorted_json.encode()).hexdigest()
    logger.info("Generated server fingerprint: %s...", fingerprint[:16])
    return fingerprint


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/fingerprint", response_model=FingerprintOutput)
def fingerprint(
    request: Request, fingerprint_input: FingerprintInput = Body(...)
) -> FingerprintOutput:
    logger.info("Processing fingerprint request...")
    # Generate a unique request ID for tracing
    _request_id: str = uuid4().hex
    if "X-Request-ID" in request.headers:
        _request_id: str = request.headers.get("X-Request-ID", _request_id)
    elif "X-Correlation-ID" in request.headers:
        _request_id: str = request.headers.get("X-Correlation-ID", _request_id)
    try:
        payload = preprocess_metrics(fingerprint_input.products)
        fingerprint_hash = _generate_server_fingerprint(payload)
        result = generate_and_link(fingerprint_hash, payload, app.state.db)

        return FingerprintOutput(
            fingerprint=result["fingerprint"],
            is_new=result["is_new"],
            payload=payload,
            request_id=_request_id,
        )
    except Exception as err:
        logger.error(f"Failed to process fingerprint: {str(err)}")
        raise HTTPException(status_code=500, detail="Failed to process fingerprint.")


__all__ = ["app"]
