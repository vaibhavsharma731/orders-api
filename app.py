"""
sample/app.py

Sample target microservice ("orders-api") for showcasing AegisAI.
Simulates a real-world cloud application with live CloudWatch logging
and built-in chaos endpoints to trigger realistic production incidents.
"""

import os
import sys
import time
import logging
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING SETUP: STDOUT + AWS CLOUDWATCH
# ─────────────────────────────────────────────────────────────────────────────
logger = logging.getLogger("orders-api")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")

# 1. Console Handler (stdout)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)

# 2. AWS CloudWatch Handler (Optional: automatically active if AWS creds exist)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
CLOUDWATCH_LOG_GROUP = os.getenv("CLOUDWATCH_LOG_GROUP", "/aws/apps/aegis-ai")

try:
    import boto3
    import watchtower

    cw_client = boto3.client(
        "logs",
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )
    cw_handler = watchtower.CloudWatchLogHandler(
        log_group_name=CLOUDWATCH_LOG_GROUP,
        log_stream_name="orders-api-stream",
        boto3_client=cw_client,
        send_interval=1
    )
    cw_handler.setFormatter(formatter)
    logger.addHandler(cw_handler)
    logger.info(f"[Init] CloudWatch logging enabled -> Group: '{CLOUDWATCH_LOG_GROUP}'")
except Exception as e:
    logger.info(f"[Init] CloudWatch logging not attached ({e}). Logging to stdout only.")


# ─────────────────────────────────────────────────────────────────────────────
# FASTAPI APP & STATE
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Orders API (Sample Target Service)", version="2.0.1")

# Global in-memory state to simulate leaks and disruptions
LEAK_MEMORY_BLOCKS: List[bytearray] = []
ACTIVE_DB_CONNECTIONS = 5
MAX_POOL_SIZE = 20
IS_DEGRADED = False
APP_VERSION = "v2.0.1"


class OrderRequest(BaseModel):
    item_id: str
    quantity: int = 1
    customer_id: str = "cust_99"


# ── Normal Endpoints ─────────────────────────────────────────────────────────

@app.get("/")
def home():
    return {
        "service": "orders-api",
        "version": APP_VERSION,
        "status": "degraded" if IS_DEGRADED else "healthy",
        "cloudwatch_log_group": CLOUDWATCH_LOG_GROUP
    }


@app.get("/health")
def health_check():
    """
    Health endpoint checked by load balancers and AegisAI verification.
    """
    latency_ms = 4800 if IS_DEGRADED else 45
    error_rate = 15.0 if IS_DEGRADED else 0.2

    status_code = 200
    if IS_DEGRADED:
        logger.warning(f"[HealthCheck] Service degraded! Latency: {latency_ms}ms, Error Rate: {error_rate}%")

    return {
        "status": "unhealthy" if IS_DEGRADED else "healthy",
        "latency_ms": latency_ms,
        "error_rate_pct": error_rate,
        "active_db_connections": ACTIVE_DB_CONNECTIONS,
        "memory_leaked_mb": len(LEAK_MEMORY_BLOCKS) * 10
    }


@app.post("/orders")
def create_order(req: OrderRequest):
    """
    Standard order creation business logic.
    """
    if IS_DEGRADED:
        time.sleep(2.5)  # Simulate slow I/O timeout
        logger.error(f"[ERROR] DatabaseQueryTimeout: Connection timeout on pool for customer {req.customer_id}")
        raise HTTPException(status_code=503, detail="Database connection timeout.")

    logger.info(f"[Order] Created order for item '{req.item_id}' (qty: {req.quantity}).")
    return {"order_id": f"ORD-{int(time.time())}", "status": "confirmed"}


# ── Chaos Simulation Endpoints (For AegisAI Demos) ───────────────────────────

@app.post("/chaos/db-exhaustion")
def trigger_db_exhaustion():
    """
    Scenario 1: Database Connection Pool Exhaustion.
    Fills up connection pool and emits CRITICAL database pool logs to CloudWatch.
    """
    global IS_DEGRADED, ACTIVE_DB_CONNECTIONS
    IS_DEGRADED = True
    ACTIVE_DB_CONNECTIONS = MAX_POOL_SIZE

    msg = f"[CRITICAL] DatabaseConnectionPoolExhausted: Pool max size {MAX_POOL_SIZE} reached. Waiting queue full (128 waiting queries). DB connection pool starvation."
    logger.error(msg)
    logger.error("[ERROR] ConnectionRefusedError: PostgreSQL max_connections limit exceeded.")
    return {"message": "DB connection exhaustion triggered. CloudWatch error logs emitted!", "status": "degraded"}


@app.post("/chaos/memory-leak")
def trigger_memory_leak(mb_to_leak: int = 200):
    """
    Scenario 2: Memory Leak.
    Allocates RAM chunks and logs OutOfMemory / heap exhaustion warnings.
    """
    global IS_DEGRADED
    IS_DEGRADED = True
    for _ in range(mb_to_leak // 10):
        LEAK_MEMORY_BLOCKS.append(bytearray(10 * 1024 * 1024))  # 10 MB per chunk

    msg = f"[CRITICAL] OutOfMemoryError imminent: Heap usage reached 94%. Garbage collection overhead limit exceeded in orders-api."
    logger.error(msg)
    return {"message": f"Leaked ~{mb_to_leak} MB of RAM. OutOfMemory logs emitted.", "total_leaked_mb": len(LEAK_MEMORY_BLOCKS) * 10}


@app.post("/chaos/bad-deployment")
def trigger_bad_deployment():
    """
    Scenario 3: Bad Deployment / Commit Regression.
    Logs broken commit regression and sets version to v2.1.0-broken.
    """
    global IS_DEGRADED, APP_VERSION
    IS_DEGRADED = True
    APP_VERSION = "v2.1.0-broken"

    msg = f"[CRITICAL] DeploymentFault: ModuleNotFoundError 'payments.v2.auth_handler' in commit 8f9b1c2. Service crashing on new routes."
    logger.error(msg)
    return {"message": "Bad deployment simulated. Error logs emitted for release rollback.", "version": APP_VERSION}


@app.post("/chaos/reset")
def reset_health():
    """
    Restores the service to full healthy state.
    """
    global IS_DEGRADED, ACTIVE_DB_CONNECTIONS, LEAK_MEMORY_BLOCKS, APP_VERSION
    IS_DEGRADED = False
    ACTIVE_DB_CONNECTIONS = 5
    LEAK_MEMORY_BLOCKS.clear()
    APP_VERSION = "v2.0.1"

    logger.info("[Recovery] System recovered. Metrics normalized, DB connections reset to 5, memory reclaimed.")
    return {"message": "Service reset to healthy state."}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    print(f"[*] Starting orders-api on http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
