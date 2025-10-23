from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.core.database import get_db
from app.services.voip_service import VoIPService
from app.schemas.call import TwilioWebhook

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.post("/twilio/call-status")
async def twilio_call_status_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    # Twilio sends data as form-encoded
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    Direction: str = Form(...),
    CallDuration: Optional[str] = Form(None),
    RecordingUrl: Optional[str] = Form(None),
    RecordingSid: Optional[str] = Form(None),
    Price: Optional[str] = Form(None),
    PriceUnit: Optional[str] = Form(None)
):
    """Handle Twilio call status webhooks"""
    try:
        # Create webhook data object
        webhook_data = TwilioWebhook(
            CallSid=CallSid,
            CallStatus=CallStatus,
            From=From,
            To=To,
            Direction=Direction,
            CallDuration=CallDuration,
            RecordingUrl=RecordingUrl,
            RecordingSid=RecordingSid,
            Price=Price,
            PriceUnit=PriceUnit
        )
        
        logger.info(f"Received Twilio webhook for call {CallSid}: {CallStatus}")
        
        # Process the webhook
        voip_service = VoIPService(db)
        await voip_service.handle_call_webhook(webhook_data)
        
        return {"status": "success", "message": "Webhook processed"}
        
    except Exception as e:
        logger.error(f"Error processing Twilio webhook: {e}")
        # Return 200 to prevent Twilio from retrying
        return {"status": "error", "message": str(e)}


@router.post("/twilio/recording")
async def twilio_recording_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    CallSid: str = Form(...),
    RecordingUrl: str = Form(...),
    RecordingSid: str = Form(...),
    RecordingDuration: Optional[str] = Form(None)
):
    """Handle Twilio recording webhooks"""
    try:
        logger.info(f"Received recording webhook for call {CallSid}")
        
        # Update call with recording information
        from sqlalchemy import select, update
        from app.models.call import Call
        
        # Update the call record with recording info
        stmt = update(Call).where(Call.call_sid == CallSid).values(
            has_recording=True,
            recording_url=RecordingUrl,
            recording_sid=RecordingSid
        )
        
        await db.execute(stmt)
        await db.commit()
        
        logger.info(f"Updated call {CallSid} with recording {RecordingSid}")
        
        return {"status": "success", "message": "Recording webhook processed"}
        
    except Exception as e:
        logger.error(f"Error processing recording webhook: {e}")
        return {"status": "error", "message": str(e)}