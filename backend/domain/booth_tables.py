from sqlalchemy import CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table, UniqueConstraint
from core.db import metadata

booths = Table(
    'projection_booths', metadata,
    Column('code', String(24), primary_key=True),
    Column('venue', String(80), nullable=False),
    Column('projector', String(24), nullable=False),
    Column('mount', String(12), nullable=False),
    Column('title_card', String(36), nullable=False),
    Column('show_slot', String(30), nullable=False),
    Column('state', String(12), nullable=False, default='survey'),
    Column('receipt_revision', Integer, nullable=False, default=0),
    Column('optical_epoch', Integer, nullable=False, default=0),
    Column('released_measurement', String(24), unique=True),
    CheckConstraint("state IN ('survey','powered','retest','cleared')"),
    CheckConstraint("mount IN ('PL','EF')"),
)

receipts = Table(
    'outlet_receipts', metadata,
    Column('code', String(34), primary_key=True),
    Column('booth_code', String(24), ForeignKey('projection_booths.code'), nullable=False),
    Column('revision', Integer, nullable=False),
    Column('circuit', String(24), nullable=False),
    Column('voltage', Float, nullable=False),
    Column('earth', Integer, nullable=False),
    Column('breakers', Integer, nullable=False),
    Column('valid', Integer, nullable=False),
    Column('signed_by', String(90), nullable=False),
    UniqueConstraint('booth_code', 'revision'),
    CheckConstraint('voltage BETWEEN 150 AND 290 AND breakers BETWEEN 0 AND 100'),
)

measurements = Table(
    'card_measurements', metadata,
    Column('code', String(24), primary_key=True),
    Column('booth_code', String(24), ForeignKey('projection_booths.code'), nullable=False),
    Column('source_measurement', String(24), ForeignKey('card_measurements.code')),
    Column('card', String(36), nullable=False),
    Column('receipt_revision', Integer, nullable=False),
    Column('optical_epoch', Integer, nullable=False),
    Column('edge_loss', Float, nullable=False),
    Column('color_error', Float, nullable=False),
    Column('flicker_index', Float, nullable=False),
    Column('frame_var', Float, nullable=False),
    Column('artifact', String(24), nullable=False),
    Column('probability', Float, nullable=False),
    Column('votes', JSON, nullable=False),
    Column('model_version', String(24), nullable=False),
    Column('compute_token', String(50), nullable=False, unique=True),
    Column('measured_by', String(100), nullable=False),
    CheckConstraint("artifact IN ('clean','soft_focus','color_shift','flicker')"),
    CheckConstraint('probability BETWEEN 0 AND 1'),
)
