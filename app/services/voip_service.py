from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime
import uuid
import logging

from twilio.rest import Client
from twilio.base.exceptions import TwilioException

from app.models.call import Call, CallStatus, CallDirection
from app.models.contact import Contact
from app.models.user import User
from app.schemas.call import CallSession, CallRecording, TwilioWebhook, CallFilters
from app.core.config import settings
from app.core.exceptions import SalesEngagementException

logger = logging.getLogger(__name__)


class VoIPService:
    """Service for VoIP calling operations using Twilio"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = None
        
        if settings.twilio_account_sid and settings.twilio_auth_token:
            self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    
    def _ensure_twilio_configured(self):
        """Ensure Twilio is properly configured"""
        if not self.client:
            raise SalesEngagementException(
                "Twilio is not configured. Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN",
                "twilio_not_configured"
            )
    
    async def initiate_call(
        self, 
        contact_id: int, 
        user_id: int, 
        tenant_id: uuid.UUID,
        from_number: Optional[str] = None
    ) -> CallSession:
        """Initiate an outbound call to a contact"""
        self._ensure_twilio_configured()
        
        # Get contact details
        stmt = select(Contact).where(
            and_(
                Contact.id == contact_id,
                Contact.tenant_id == tenant_id,
                Contact.is_deleted.is_(False)
            )
        )
        result = await self.db.execute(stmt)
        contact = result.scalar_one_or_none()
        
        if not contact:
            raise SalesEngagementException("Contact not found", "contact_not_found")
        
        if not contact.phone:
            raise SalesEngagementException("Contact has no phone number", "no_phone_number")
        
        # Use provided from_number or default
        from_num = from_number or settings.twilio_phone_number
        if not from_num:
            raise SalesEngagementException(
                "No from number configured", 
                "no_from_number"
            )
        
        try:
            # Create webhook URL for call status updates
            webhook_url = f"{settings.base_url}/api/v1/webhooks/twilio/call-status"
            
            # Check if we're in development environment (localhost)
            is_development = "localhost" in settings.base_url or "127.0.0.1" in settings.base_url
            
            if is_development:
                # In development, create a simple call without webhooks
                twilio_call = self.client.calls.create(
                    to=contact.phone,
                    from_=from_num,
                    # Use TwiML for simple call without webhooks
                    twiml='<Response><Say>Hello, this is a test call from Sales Engagement Platform.</Say></Response>',
                    timeout=30  # Ring for 30 seconds
                )
            else:
                # In production, use full webhook integration
                twilio_call = self.client.calls.create(
                    to=contact.phone,
                    from_=from_num,
                    url=webhook_url,
                    status_callback=webhook_url,
                    status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                    record=True,  # Enable call recording
                    timeout=30  # Ring for 30 seconds
                )
            
            # Create call record in database
            call = Call(
                call_sid=twilio_call.sid,
                direction=CallDirection.OUTBOUND,
                status=CallStatus.INITIATED,
                from_number=from_num,
                to_number=contact.phone,
                contact_id=contact_id,
                user_id=user_id,
                tenant_id=tenant_id,
                company_id=contact.company_id
            )
            
            self.db.add(call)
            await self.db.commit()
            await self.db.refresh(call)
            
            logger.info(f"Call initiated: {call.call_sid} from {from_num} to {contact.phone}")
            
            return CallSession(
                call_id=call.id,
                call_sid=call.call_sid,
                status=call.status,
                from_number=call.from_number,
                to_number=call.to_number,
                contact_name=contact.full_name,
                started_at=call.created_at
            )
            
        except TwilioException as e:
            logger.error(f"Twilio error initiating call: {e}")
            error_msg = str(e)
            
            # Make error messages more user-friendly
            if "Unable to create record" in error_msg and "localhost" in error_msg:
                error_msg = "VoIP-palvelu ei ole käytettävissä kehitysympäristössä. Tarvitaan julkinen webhook URL."
            elif "HTTP 400 error" in error_msg:
                error_msg = "Twilio-konfiguraatio virhe. Tarkista webhook URL asetukset."
            elif "not a valid phone number" in error_msg.lower():
                error_msg = "Virheellinen puhelinnumero. Käytä kansainvälistä muotoa (+358...)."
            
            raise SalesEngagementException(f"Soiton aloitus epäonnistui: {error_msg}", "twilio_error")
        except Exception as e:
            logger.error(f"Error initiating call: {e}")
            await self.db.rollback()
            raise SalesEngagementException(f"Failed to initiate call: {str(e)}", "call_initiation_failed")
    
    async def handle_call_webhook(self, webhook_data: TwilioWebhook) -> None:
        """Handle Twilio webhook for call status updates"""
        try:
            # Find the call by SID
            stmt = select(Call).where(Call.call_sid == webhook_data.CallSid)
            result = await self.db.execute(stmt)
            call = result.scalar_one_or_none()
            
            if not call:
                logger.warning(f"Call not found for SID: {webhook_data.CallSid}")
                return
            
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
            
            new_status = status_mapping.get(webhook_data.CallStatus.lower(), CallStatus.FAILED)
            
            # Update call status
            call.status = new_status
            
            # Set start time when call is answered
            if new_status == CallStatus.IN_PROGRESS and not call.start_time:
                call.start_time = datetime.utcnow()
            
            # Set end time and duration when call is completed
            if new_status in [CallStatus.COMPLETED, CallStatus.FAILED, CallStatus.NO_ANSWER, CallStatus.CANCELED]:
                if not call.end_time:
                    call.end_time = datetime.utcnow()
                
                # Set duration from Twilio if provided
                if webhook_data.CallDuration:
                    call.duration = int(webhook_data.CallDuration)
                elif call.start_time:
                    # Calculate duration if not provided
                    duration = (call.end_time - call.start_time).total_seconds()
                    call.duration = int(duration)
            
            # Update recording information
            if webhook_data.RecordingUrl and webhook_data.RecordingSid:
                call.has_recording = True
                call.recording_url = webhook_data.RecordingUrl
                call.recording_sid = webhook_data.RecordingSid
            
            # Update pricing information
            if webhook_data.Price:
                call.price = float(webhook_data.Price)
                call.price_unit = webhook_data.PriceUnit or 'USD'
            
            await self.db.commit()
            
            logger.info(f"Call {call.call_sid} status updated to {new_status}")
            
            # Publish real-time call status update
            from app.services.notification_service import NotificationService
            call_notification_data = {
                "call_id": call.id,
                "call_sid": call.call_sid,
                "status": new_status.value,
                "contact_id": call.contact_id,
                "user_id": call.user_id,
                "duration": call.duration,
                "direction": call.direction.value,
                "from_number": call.from_number,
                "to_number": call.to_number,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            await NotificationService.publish_call_event(call_notification_data, call.tenant_id)
            
            # Create activity record for completed calls
            if new_status == CallStatus.COMPLETED:
                # Trigger background task for call completion processing
                from app.tasks.call_tasks import process_call_completion
                process_call_completion.delay(call.id)
                
                # Trigger recording download if available
                if call.has_recording:
                    from app.tasks.call_tasks import download_call_recording
                    download_call_recording.delay(call.id)
                
        except Exception as e:
            logger.error(f"Error handling call webhook: {e}")
            await self.db.rollback()
    
    async def _create_call_activity(self, call: Call) -> None:
        """Create an activity record for a completed call"""
        from app.models.activity import Activity, ActivityType
        
        activity_payload = {
            "call_id": call.id,
            "call_sid": call.call_sid,
            "duration": call.duration,
            "direction": call.direction.value,
            "from_number": call.from_number,
            "to_number": call.to_number,
            "has_recording": call.has_recording,
            "recording_url": call.recording_url if call.has_recording else None
        }
        
        activity = Activity(
            type=ActivityType.CALL,
            payload=activity_payload,
            contact_id=call.contact_id,
            user_id=call.user_id,
            tenant_id=call.tenant_id,
            company_id=call.company_id
        )
        
        self.db.add(activity)
        await self.db.commit()
    
    async def get_call_recording(self, call_sid: str, tenant_id: uuid.UUID) -> Optional[CallRecording]:
        """Get call recording information"""
        stmt = select(Call).where(
            and_(
                Call.call_sid == call_sid,
                Call.tenant_id == tenant_id,
                Call.has_recording == True
            )
        )
        result = await self.db.execute(stmt)
        call = result.scalar_one_or_none()
        
        if not call or not call.recording_sid:
            return None
        
        return CallRecording(
            call_id=call.id,
            recording_sid=call.recording_sid,
            recording_url=call.recording_url,
            duration=call.duration or 0
        )
    
    async def end_call(self, call_sid: str, tenant_id: uuid.UUID) -> bool:
        """End an active call"""
        self._ensure_twilio_configured()
        
        try:
            # Find the call
            stmt = select(Call).where(
                and_(
                    Call.call_sid == call_sid,
                    Call.tenant_id == tenant_id
                )
            )
            result = await self.db.execute(stmt)
            call = result.scalar_one_or_none()
            
            if not call:
                return False
            
            # End the call with Twilio
            twilio_call = self.client.calls(call_sid).update(status='completed')
            
            # Update local call status
            call.status = CallStatus.COMPLETED
            call.end_time = datetime.utcnow()
            
            if call.start_time:
                duration = (call.end_time - call.start_time).total_seconds()
                call.duration = int(duration)
            
            await self.db.commit()
            
            logger.info(f"Call {call_sid} ended manually")
            return True
            
        except TwilioException as e:
            logger.error(f"Twilio error ending call: {e}")
            return False
        except Exception as e:
            logger.error(f"Error ending call: {e}")
            return False
    
    async def get_call_history(self, filters: CallFilters, tenant_id: uuid.UUID) -> Tuple[List[Call], int]:
        """Get call history with filtering"""
        stmt = select(Call).where(Call.tenant_id == tenant_id)
        
        # Apply filters
        if filters.contact_id:
            stmt = stmt.where(Call.contact_id == filters.contact_id)
        
        if filters.status:
            stmt = stmt.where(Call.status == filters.status)
        
        if filters.direction:
            stmt = stmt.where(Call.direction == filters.direction)
        
        if filters.date_from:
            stmt = stmt.where(Call.created_at >= filters.date_from)
        
        if filters.date_to:
            stmt = stmt.where(Call.created_at <= filters.date_to)
        
        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        offset = (filters.page - 1) * filters.page_size
        stmt = stmt.order_by(Call.created_at.desc()).offset(offset).limit(filters.page_size)
        
        result = await self.db.execute(stmt)
        calls = result.scalars().all()
        
        return calls, total