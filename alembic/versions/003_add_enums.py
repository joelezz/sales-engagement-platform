"""Add enum types

Revision ID: 003
Revises: 002
Create Date: 2025-01-23 18:58:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE userrole AS ENUM ('ADMIN', 'USER')")
    op.execute("CREATE TYPE activitytype AS ENUM ('CALL', 'EMAIL', 'SMS', 'NOTE', 'MEETING', 'TASK')")
    op.execute("CREATE TYPE callstatus AS ENUM ('INITIATED', 'RINGING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'BUSY', 'NO_ANSWER', 'CANCELLED')")


def downgrade() -> None:
    op.execute("DROP TYPE IF EXISTS callstatus")
    op.execute("DROP TYPE IF EXISTS activitytype") 
    op.execute("DROP TYPE IF EXISTS userrole")