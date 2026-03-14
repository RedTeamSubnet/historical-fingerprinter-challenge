import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Body, HTTPException
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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/fingerprint", response_model=FingerprintOutput)
def fingerprint(fingerprint_input: FingerprintInput = Body(...)) -> FingerprintOutput:
    logger.info("Processing fingerprint request...")

    try:
        payload = preprocess_metrics(fingerprint_input.products)
        result = generate_and_link(payload, app.state.db)

        return FingerprintOutput(
            fingerprint=result["fingerprint"], is_new=result["is_new"]
        )
    except Exception as err:
        logger.error(f"Failed to process fingerprint: {str(err)}")
        raise HTTPException(status_code=500, detail="Failed to process fingerprint.")


__all__ = ["app"]
