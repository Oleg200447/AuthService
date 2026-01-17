"""Initial migration - create tables

Revision ID: 001
Revises: 
Create Date: 2026-01-04 04:54:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgcrypto extension for UUID generation
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    
    # Create users table
    op.create_table(
        'users',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column('username', sa.Text(), nullable=False),
        sa.Column('google_sub', sa.Text(), nullable=False),
        sa.Column('email', sa.Text(), nullable=True),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('google_sub')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_google_sub'), 'users', ['google_sub'], unique=True)

    # Create system_accounts table
    op.create_table(
        'system_accounts',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column('username', sa.Text(), nullable=False),
        sa.Column('secret_key_hash', sa.Text(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_system_accounts_username'), 'system_accounts', ['username'], unique=True)

    # Create pre_auth_sessions table
    op.create_table(
        'pre_auth_sessions',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column('google_sub', sa.Text(), nullable=False),
        sa.Column('email', sa.Text(), nullable=True),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('google_sub')
    )
    op.create_index(op.f('ix_pre_auth_sessions_google_sub'), 'pre_auth_sessions', ['google_sub'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_pre_auth_sessions_google_sub'), table_name='pre_auth_sessions')
    op.drop_table('pre_auth_sessions')
    op.drop_index(op.f('ix_system_accounts_username'), table_name='system_accounts')
    op.drop_table('system_accounts')
    op.drop_index(op.f('ix_users_google_sub'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
