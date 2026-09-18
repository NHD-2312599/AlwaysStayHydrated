"""
Flashcard models — Always Stay Hydrated
Chỉ chứa Tab / Card / CardStatus trên flashcard.db (bind mặc định).
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    username   = db.Column(db.String(100), primary_key=True)
    password   = db.Column(db.Text, nullable=False)
    role       = db.Column(db.String(20), nullable=False, default='view')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Tab(db.Model):
    __tablename__ = 'tabs'

    id         = db.Column(db.String(50), primary_key=True)
    name       = db.Column(db.String(200), nullable=False)
    order_index = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cards = db.relationship('Card', backref='tab', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':         self.id,
            'name':       self.name,
            'cards':      [c.to_dict() for c in self.cards],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class Card(db.Model):
    __tablename__ = 'cards'

    id         = db.Column(db.String(50), primary_key=True)
    tab_id     = db.Column(db.String(50), db.ForeignKey('tabs.id'), nullable=False)
    ref        = db.Column(db.String(100), default='')
    title      = db.Column(db.Text, default='')
    verse      = db.Column(db.Text, default='')
    analysis   = db.Column(db.Text, default='')
    speech     = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    statuses = db.relationship('CardStatus', backref='card', lazy=True, cascade='all, delete-orphan')
    review_schedules = db.relationship('CardReviewSchedule', backref='card', lazy=True, cascade='all, delete-orphan')

    def to_dict(self, include_statuses=True):
        data = {
            'id':         self.id,
            'tab_id':     self.tab_id,
            'ref':        self.ref,
            'title':      self.title,
            'verse':      self.verse,
            'analysis':   self.analysis,
            'speech':     self.speech,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_statuses:
            data['statuses'] = [s.to_dict() for s in self.statuses]
        return data


class CardStatus(db.Model):
    __tablename__ = 'card_statuses'

    id         = db.Column(db.Integer, primary_key=True)
    card_id    = db.Column(db.String(50), db.ForeignKey('cards.id'), nullable=False)
    user_id    = db.Column(db.String(100), nullable=False)
    status     = db.Column(db.String(1), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('card_id', 'user_id', name='uq_card_user_status'),
    )

    def to_dict(self):
        return {
            'id':         self.id,
            'card_id':    self.card_id,
            'user_id':    self.user_id,
            'status':     self.status,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class CardReviewSchedule(db.Model):
    __tablename__ = 'card_review_schedules'

    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.String(50), db.ForeignKey('cards.id'), nullable=False)
    user_id = db.Column(db.String(100), nullable=False)
    next_review = db.Column(db.DateTime, nullable=False)
    last_reviewed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_status = db.Column(db.String(1), nullable=False, default='r')
    interval_days = db.Column(db.Integer, nullable=False, default=1)
    review_count = db.Column(db.Integer, nullable=False, default=0)

    __table_args__ = (
        db.UniqueConstraint('card_id', 'user_id', name='uq_card_user_review_schedule'),
        db.Index('ix_review_schedule_user_next_review', 'user_id', 'next_review'),
    )

    def to_dict(self):
        return {
            'card_id': self.card_id,
            'user_id': self.user_id,
            'nextReview': self.next_review.isoformat() if self.next_review else None,
            'lastReviewedAt': self.last_reviewed_at.isoformat() if self.last_reviewed_at else None,
            'lastStatus': self.last_status,
            'intervalDays': self.interval_days,
            'reviewCount': self.review_count,
        }


class ExamReviewStatus(db.Model):
    __tablename__ = 'exam_review_statuses'

    id = db.Column(db.Integer, primary_key=True)
    tab_id = db.Column(db.String(50), nullable=False)
    card_id = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='review')
    wrong_count = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('tab_id', 'card_id', 'user_id', name='uq_exam_review_user_card'),
    )

    def to_dict(self):
        return {
            'tab_id': self.tab_id,
            'card_id': self.card_id,
            'status': self.status,
            'wrong_count': self.wrong_count,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


def init_db(app):
    """Tạo bảng flashcard trên flashcard.db nếu chưa có."""
    with app.app_context():
        db.create_all()
