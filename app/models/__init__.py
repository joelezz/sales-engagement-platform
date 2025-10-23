# Import all models to ensure they are registered with SQLAlchemy
from app.models.company import Company
from app.models.user import User, UserRole
from app.models.contact import Contact
from app.models.activity import Activity, ActivityType
from app.models.call import Call, CallStatus, CallDirection

__all__ = [
    "Company",
    "User", 
    "UserRole",
    "Contact",
    "Activity",
    "ActivityType",
    "Call",
    "CallStatus",
    "CallDirection"
]