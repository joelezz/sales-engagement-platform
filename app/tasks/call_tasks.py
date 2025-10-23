from celery import Celery
from celery.schedules import crontab
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, and_, update
from datetime import datetime, timedelta
import asyncio
import logging
import uuid

from app.core.celery import celery_app
from app.core.config import settings
from app.models.call import Call, CallStatus
from app.models.activity import Activity, ActivityType
from app.core.database import Base

logger = logging.getLogger(__name__)

# Create async engine for Celery tasks
engine = create_async_engine(settings.database_url)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session():
    """Get database session for async tasks"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@celery_app.task(bind=True, max_retries=3)
def process_call_completion(self, call_id: int):
    """Process call completion and create activity record"""
    try:
        asyncio.run(_process_call_completion_async(call_id))
    except Exception as exc:
        logger.error(f"Error processing call completion for call {call_id}: {exc}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


async def _process_call_completion_async(call_id: int):
    """Async implementation of call completion processing"""
    async with AsyncSessionLocal() as db:
        try:
            # Get the call
            stmt = select(Call).where(Call.id == call_id)
            result = await db.execute(stmt)
            call = result.scalar_one_or_none()
            
            if not call:
                logger.warning(f"Call {call_id} not found")
                return
            
            # Only process completed calls
            if call.status != CallStatus.COMPLETED:
                logger.info(f"Call {call_id} is not completed, skipping activity creation")
                return
            
            # Check if activity already exists
            activity_stmt = select(Activity).where(
                and_(
                    Activity.type == ActivityType.CALL,
                    Activity.payload['call_id'].astext == str(call_id)
                )
            )
            activity_result = await db.execute(activity_stmt)
            existing_activity = activity_result.scalar_one_or_none()
            
            if existing_activity:
                logger.info(f"Activity already exists for call {call_id}")
                return
            
            # Create activity record using activity service
            from app.services.activity_service import ActivityService
            from app.schemas.activity import ActivityCreate
            
            activity_payload = {
                "call_id": call.id,
                "call_sid": call.call_sid,
                "duration": call.duration,
                "direction": call.direction.value,
                "from_number": call.from_number,
                "to_number": call.to_number,
                "has_recording": call.has_recording,
                "recording_url": call.recording_url if call.has_recording else None,
                "start_time": call.start_time.isoformat() if call.start_time else None,
                "end_time": call.end_time.isoformat() if call.end_time else None,
                "title": f"Call completed ({call.duration}s)" if call.duration else "Call completed",
                "description": f"Call from {call.from_number} to {call.to_number}"
            }
            
            activity_service = ActivityService(db)
            activity_create = ActivityCreate(
                type=ActivityType.CALL,
                payload=activity_payload,
                contact_id=call.contact_id
            )
            
            await activity_service.create_activity(
                activity_create,
                call.user_id,
                call.tenant_id,
                call.company_id
            )
            
            logger.info(f"Created activity for completed call {call_id}")
            
        except Exception as e:
            logger.error(f"Error in call completion processing: {e}")
            await db.rollback()
            raise


@celery_app.task(bind=True, max_retries=3)
def download_call_recording(self, call_id: int):
    """Download and store call recording"""
    try:
        asyncio.run(_download_call_recording_async(call_id))
    except Exception as exc:
        logger.error(f"Error downloading recording for call {call_id}: {exc}")
        raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes


async def _download_call_recording_async(call_id: int):
    """Async implementation of call recording download"""
    async with AsyncSessionLocal() as db:
        try:
            # Get the call
            stmt = select(Call).where(
                and_(
                    Call.id == call_id,
                    Call.has_recording == True,
                    Call.recording_url.is_not(None)
                )
            )
            result = await db.execute(stmt)
            call = result.scalar_one_or_none()
            
            if not call:
                logger.warning(f"Call {call_id} not found or has no recording")
                return
            
            # Here you would implement actual recording download logic
            # For now, we'll just log that the recording is available
            logger.info(f"Recording available for call {call_id}: {call.recording_url}")
            
            # You could implement:
            # 1. Download the recording file from Twilio
            # 2. Store it in S3 or local storage
            # 3. Update the call record with local storage path
            # 4. Optionally transcribe the recording
            
        except Exception as e:
            logger.error(f"Error downloading call recording: {e}")
            raise


@celery_app.task
def cleanup_old_calls():
    """Clean up old call records and recordings"""
    try:
        asyncio.run(_cleanup_old_calls_async())
    except Exception as exc:
        logger.error(f"Error in call cleanup: {exc}")


async def _cleanup_old_calls_async():
    """Async implementation of call cleanup"""
    async with AsyncSessionLocal() as db:
        try:
            # Define retention period (e.g., 1 year)
            retention_date = datetime.utcnow() - timedelta(days=365)
            
            # Find old calls
            stmt = select(Call).where(Call.created_at < retention_date)
            result = await db.execute(stmt)
            old_calls = result.scalars().all()
            
            logger.info(f"Found {len(old_calls)} calls older than {retention_date}")
            
            for call in old_calls:
                # Here you would implement cleanup logic:
                # 1. Delete recording files from storage
                # 2. Anonymize or delete call records based on GDPR requirements
                # 3. Keep aggregated statistics
                
                logger.info(f"Would clean up call {call.id} from {call.created_at}")
            
            # For now, just log what would be cleaned up
            # In production, you'd actually perform the cleanup
            
        except Exception as e:
            logger.error(f"Error in call cleanup: {e}")
            raise


@celery_app.task
def sync_call_status_with_twilio():
    """Sync call status with Twilio for any pending calls"""
    try:
        asyncio.run(_sync_call_status_async())
    except Exception as exc:
        logger.error(f"Error syncing call status: {exc}")


async def _sync_call_status_async():
    """Async implementation of call status sync"""
    from twilio.rest import Client
    
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        logger.warning("Twilio not configured, skipping status sync")
        return
    
    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    
    async with AsyncSessionLocal() as db:
        try:
            # Find calls that might need status updates
            pending_statuses = [CallStatus.INITIATED, CallStatus.RINGING, CallStatus.IN_PROGRESS]
            
            # Only check calls from the last 24 hours
            since_date = datetime.utcnow() - timedelta(hours=24)
            
            stmt = select(Call).where(
                and_(
                    Call.status.in_(pending_statuses),
                    Call.created_at >= since_date
                )
            )
            result = await db.execute(stmt)
            pending_calls = result.scalars().all()
            
            logger.info(f"Syncing status for {len(pending_calls)} pending calls")
            
            for call in pending_calls:
                try:
                    # Get call status from Twilio
                    twilio_call = client.calls(call.call_sid).fetch()
                    
                    # Map Twilio status to our status
                    status_mapping = {
                        'queued': CallStatus.INITIATED,
                        'initiated': CallStatus.INITIATED,
                        'ringing': CallStatus.RINGING,
                        'in-progress': CallStatus.IN_PROGRESS,
                        'completed': CallStatus.COMPLETED,
                        'failed': CallStatus.FAILED,
                        'busy': CallStatus.BUSY,
                        'no-answer': CallStatus.NO_ANSWER,
                        'canceled': CallStatus.CANCELED
                    }
                    
                    new_status = status_mapping.get(twilio_call.status, CallStatus.FAILED)
                    
                    if new_status != call.status:
                        logger.info(f"Updating call {call.call_sid} status from {call.status} to {new_status}")
                        
                        # Update call status
                        update_stmt = update(Call).where(Call.id == call.id).values(
                            status=new_status,
                            duration=twilio_call.duration,
                            price=float(twilio_call.price) if twilio_call.price else None,
                            price_unit=twilio_call.price_unit
                        )
                        
                        await db.execute(update_stmt)
                        
                        # If call is now completed, trigger activity creation
                        if new_status == CallStatus.COMPLETED:
                            process_call_completion.delay(call.id)
                
                except Exception as e:
                    logger.error(f"Error syncing call {call.call_sid}: {e}")
                    continue
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error in call status sync: {e}")
            await db.rollback()
            raise


# Schedule periodic tasks
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks"""
    
    # Cleanup old calls daily at 2 AM
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        cleanup_old_calls.s(),
        name='cleanup old calls'
    )
    
    # Sync call status every 5 minutes
    sender.add_periodic_task(
        300.0,  # 5 minutes
        sync_call_status_with_twilio.s(),
        name='sync call status'
    )