"""Initial migration - create tables and seed system accounts

Revision ID: 001
Revises: 
Create Date: 2026-01-04 04:54:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from passlib.context import CryptContext

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('username', sa.Text(), nullable=False),
        sa.Column('google_sub', sa.Text(), nullable=False),
        sa.Column('email', sa.Text(), nullable=True),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('google_sub')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_google_sub'), 'users', ['google_sub'], unique=True)

    # Create system_accounts table
    op.create_table(
        'system_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('username', sa.Text(), nullable=False),
        sa.Column('secret_key_hash', sa.Text(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_system_accounts_username'), 'system_accounts', ['username'], unique=True)

    # Create pre_auth_sessions table
    op.create_table(
        'pre_auth_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('google_sub', sa.Text(), nullable=False),
        sa.Column('email', sa.Text(), nullable=True),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('google_sub')
    )
    op.create_index(op.f('ix_pre_auth_sessions_google_sub'), 'pre_auth_sessions', ['google_sub'], unique=True)

    # Seed system accounts (secret keys will come from env variables)
    # The actual secret keys should be stored in .env file
    # Here we're creating hashes for the placeholder secrets
    from app.config import settings
    
    system_accounts = [
        {
            'id': str(uuid.uuid4()),
            'username': 'system_1',
            'secret_key_hash': pwd_context.hash(settings.SYSTEM_1_SECRET),
            'active': True
        },
        {
            'id': str(uuid.uuid4()),
            'username': 'system_2',
            'secret_key_hash': pwd_context.hash(settings.SYSTEM_2_SECRET),
            'active': True
        },
        {
            'id': str(uuid.uuid4()),
            'username': 'system_3',
            'secret_key_hash': pwd_context.hash(settings.SYSTEM_3_SECRET),
            'active': True
        },
        {
            'id': str(uuid.uuid4()),
            'username': 'system_4',
            'secret_key_hash': pwd_context.hash(settings.SYSTEM_4_SECRET),
            'active': True
        },
        {
            'id': str(uuid.uuid4()),
            'username': 'system_5',
            'secret_key_hash': pwd_context.hash(settings.SYSTEM_5_SECRET),
            'active': True
        }
    ]
    
    op.bulk_insert(
        sa.table('system_accounts',
                 sa.column('id', postgresql.UUID),
                 sa.column('username', sa.Text),
                 sa.column('secret_key_hash', sa.Text),
                 sa.column('active', sa.Boolean)),
        system_accounts
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_pre_auth_sessions_google_sub'), table_name='pre_auth_sessions')
    op.drop_table('pre_auth_sessions')
    op.drop_index(op.f('ix_system_accounts_username'), table_name='system_accounts')
    op.drop_table('system_accounts')
    op.drop_index(op.f('ix_users_google_sub'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')
