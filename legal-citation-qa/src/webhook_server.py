"""
FastAPI webhook server for handling Box webhook events.
"""

import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
from pydantic_settings import BaseSettings
import uvicorn

from worker import CitationQAWorker
from box_handler import BoxHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings."""
    courtlistener_token: str = ""
    box_client_id: str = ""
    box_client_secret: str = ""
    box_access_token: str = ""
    box_webhook_signing_key: str = ""
    box_qa_folder_id: str = ""
    git_audit_path: str = "/data/audit"
    git_remote_url: str = ""
    output_dir: str = "/data/reports"
    verify_webhooks: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Initialize settings
settings = Settings()

# Create FastAPI app
app = FastAPI(
    title="Legal Citation QA Webhook Server",
    description="Webhook server for processing legal documents via Box",
    version="1.0.0"
)

# Initialize worker (shared instance)
worker = None


def get_worker() -> CitationQAWorker:
    """Get or create worker instance."""
    global worker
    if worker is None:
        worker = CitationQAWorker(
            courtlistener_token=settings.courtlistener_token,
            box_client_id=settings.box_client_id,
            box_client_secret=settings.box_client_secret,
            box_access_token=settings.box_access_token,
            git_audit_path=settings.git_audit_path,
            git_remote_url=settings.git_remote_url,
            output_dir=settings.output_dir,
            use_mock_services=False
        )
    return worker


class WebhookEvent(BaseModel):
    """Box webhook event model."""
    trigger: str
    source: Dict[str, Any]


async def process_document_task(file_id: str):
    """Background task to process a document."""
    try:
        logger.info(f"Starting background processing of file {file_id}")

        worker_instance = get_worker()
        report = worker_instance.process_box_file(file_id)

        logger.info(f"Successfully processed file {file_id}")
        logger.info(f"Report status: {report['summary']['overall_status']}")

    except Exception as e:
        logger.error(f"Failed to process file {file_id}: {e}", exc_info=True)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Legal Citation QA Webhook Server",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    }


@app.post("/webhook/box")
async def box_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Handle Box webhook events.

    This endpoint receives file upload notifications from Box,
    validates the webhook signature, and triggers document processing.
    """
    try:
        # Get raw body and headers
        body = await request.body()
        headers = dict(request.headers)

        # Verify webhook signature
        if settings.verify_webhooks and settings.box_webhook_signing_key:
            box_handler = BoxHandler(
                settings.box_client_id,
                settings.box_client_secret,
                settings.box_access_token
            )

            is_valid = box_handler.verify_webhook_signature(
                body,
                headers,
                settings.box_webhook_signing_key
            )

            if not is_valid:
                logger.warning("Invalid webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse event
        event_data = await request.json()

        logger.info(f"Received Box webhook event: {event_data.get('trigger')}")

        # Process event
        box_handler = BoxHandler(
            settings.box_client_id,
            settings.box_client_secret,
            settings.box_access_token
        )

        processed_event = box_handler.process_webhook_event(event_data)

        if not processed_event:
            logger.info("Event not relevant for processing")
            return {"status": "ignored", "reason": "Not a document upload event"}

        # Queue document processing as background task
        file_id = processed_event['file_id']
        background_tasks.add_task(process_document_task, file_id)

        logger.info(f"Queued processing for file {file_id}")

        return {
            "status": "accepted",
            "file_id": file_id,
            "file_name": processed_event['file_name']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process")
async def process_document(
    file_id: str,
    background_tasks: BackgroundTasks
):
    """
    Manually trigger document processing.

    Args:
        file_id: Box file ID to process

    This endpoint allows manual triggering of document processing
    without going through the webhook flow.
    """
    try:
        logger.info(f"Manual processing requested for file {file_id}")

        # Queue processing
        background_tasks.add_task(process_document_task, file_id)

        return {
            "status": "accepted",
            "file_id": file_id,
            "message": "Document processing queued"
        }

    except Exception as e:
        logger.error(f"Manual processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/audit/status")
async def audit_status():
    """Get git audit trail status."""
    try:
        worker_instance = get_worker()
        integrity = worker_instance.git_audit.verify_integrity()

        return {
            "audit_trail": integrity,
            "output_dir": settings.output_dir
        }

    except Exception as e:
        logger.error(f"Audit status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/audit/history")
async def audit_history(limit: int = 50):
    """Get audit trail history."""
    try:
        worker_instance = get_worker()
        history = worker_instance.git_audit.get_history(limit=limit)

        return {
            "total": len(history),
            "commits": history
        }

    except Exception as e:
        logger.error(f"Audit history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the webhook server."""
    logger.info(f"Starting webhook server on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    import sys

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    start_server(host, port)
