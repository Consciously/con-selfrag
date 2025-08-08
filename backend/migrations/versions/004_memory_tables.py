"""Create episodic_memories and semantic_memories tables

# =============================================================================
# Project: Selfrag
# Module: Memory Service (Phase 3)
# File: migrations/versions/004_memory_tables.py
# Purpose: Alembic migration creating episodic & semantic memory tables.
# Owner: Core Platform (RAG + Memory)
# Status: Draft (Phase 3) | Created: 2025-08-08
# Notes: Keep Agents out. Coordinator only routes. No external tools.
# =============================================================================

Revision ID: 004_memory_tables
Revises: 003_add_memory_logs_table
Create Date: 2025-08-08 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '004_memory_tables'
down_revision: Union[str, None] = '003_add_memory_logs_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:  # noqa: D401
    op.create_table(
        'episodic_memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tokens', sa.Integer(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('embedding', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('ix_episodic_memories_id', 'episodic_memories', ['id'], unique=False)
    op.create_index('ix_episodic_memories_user_id', 'episodic_memories', ['user_id'], unique=False)
    op.create_index('ix_episodic_memories_session_id', 'episodic_memories', ['session_id'], unique=False)
    op.create_index('idx_ep_mem_user_created', 'episodic_memories', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_ep_mem_tags', 'episodic_memories', ['tags'], unique=False, postgresql_using='gin')

    op.create_table(
        'semantic_memories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('source_ref', sa.String(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('embedding', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
    )
    op.create_index('ix_semantic_memories_id', 'semantic_memories', ['id'], unique=False)
    op.create_index('ix_semantic_memories_user_id', 'semantic_memories', ['user_id'], unique=False)
    op.create_index('idx_se_mem_user_created', 'semantic_memories', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_se_mem_tags', 'semantic_memories', ['tags'], unique=False, postgresql_using='gin')


def downgrade() -> None:
    op.drop_index('idx_se_mem_tags', table_name='semantic_memories')
    op.drop_index('idx_se_mem_user_created', table_name='semantic_memories')
    op.drop_index('ix_semantic_memories_user_id', table_name='semantic_memories')
    op.drop_index('ix_semantic_memories_id', table_name='semantic_memories')
    op.drop_table('semantic_memories')

    op.drop_index('idx_ep_mem_tags', table_name='episodic_memories')
    op.drop_index('idx_ep_mem_user_created', table_name='episodic_memories')
    op.drop_index('ix_episodic_memories_session_id', table_name='episodic_memories')
    op.drop_index('ix_episodic_memories_user_id', table_name='episodic_memories')
    op.drop_index('ix_episodic_memories_id', table_name='episodic_memories')
    op.drop_table('episodic_memories')
