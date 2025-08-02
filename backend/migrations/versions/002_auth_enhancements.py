"""Add auth enhancements - is_admin, last_login, api_keys table

Revision ID: 002_auth_enhancements
Revises: 001_auth_tables
Create Date: 2025-01-02 22:04:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision: str = '002_auth_enhancements'
down_revision: Union[str, None] = '001_auth_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration."""
    # Add missing columns to users table
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), default=False))
    op.add_column('users', sa.Column('last_login', sa.DateTime(), nullable=True))
    
    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('key_id', sa.String(32), unique=True, nullable=False, index=True),
        sa.Column('key_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('permissions', sa.Text(), nullable=True),
    )
    
    # Create composite indexes for api_keys
    op.create_index('ix_api_keys_active_user', 'api_keys', ['is_active', 'user_id'])
    op.create_index('ix_api_keys_active_key_id', 'api_keys', ['is_active', 'key_id'])


def downgrade() -> None:
    """Rollback migration."""
    # Drop api_keys table and indexes
    op.drop_index('ix_api_keys_active_key_id', 'api_keys')
    op.drop_index('ix_api_keys_active_user', 'api_keys')
    op.drop_table('api_keys')
    
    # Remove columns from users table
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'is_admin')
