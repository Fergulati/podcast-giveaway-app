import enum
from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    DateTime,
    Text,
    Enum,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)

    engagements = relationship('Engagement', back_populates='user', cascade='all, delete-orphan')
    ledger_entries = relationship('PointsLedger', back_populates='user', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"


class EventType(enum.Enum):
    COMMENT = 'COMMENT'
    LIKE = 'LIKE'
    SUPERCHAT = 'SUPERCHAT'
    LIVESTREAM_CHAT = 'LIVESTREAM_CHAT'


class Engagement(Base):
    __tablename__ = 'engagements'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    event_id = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    raw_json = Column(Text)

    user = relationship('User', back_populates='engagements')
    ledger_entries = relationship('PointsLedger', back_populates='engagement')

    def __repr__(self) -> str:
        return (
            f"<Engagement id={self.id} user_id={self.user_id} "
            f"event_type={self.event_type.name} event_id={self.event_id}>"
        )


class PointsLedger(Base):
    __tablename__ = 'points_ledger'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    engagement_id = Column(Integer, ForeignKey('engagements.id'))
    points_delta = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)

    user = relationship('User', back_populates='ledger_entries')
    engagement = relationship('Engagement', back_populates='ledger_entries')

    def __repr__(self) -> str:
        return (
            f"<PointsLedger id={self.id} user_id={self.user_id} "
            f"points_delta={self.points_delta} reason={self.reason!r}>"
        )
