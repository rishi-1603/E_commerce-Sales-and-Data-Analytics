"""Initial schema for Commerce Intelligence API

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-28 15:45:00.000000

"""
from typing import Sequence, Union

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Schema matches Base.metadata created by app/models/
    pass

def downgrade() -> None:
    pass
