from datetime import datetime
from sqlalchemy import text, Column, TIMESTAMP
from sqlmodel import Field, SQLModel, Relationship, JSON
from typing import List, Optional, Set
from sqlalchemy.dialects.postgresql import TEXT
from sqlalchemy.dialects import postgresql
from enum import Enum
from sqlalchemy.types import Integer, STRINGTYPE


class TableBase(SQLModel):
    """
    A base class for SQLModel tables.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
            onupdate=datetime.utcnow,
        )
    )