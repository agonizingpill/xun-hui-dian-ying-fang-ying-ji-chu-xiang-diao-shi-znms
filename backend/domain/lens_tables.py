from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, Table
from core.db import metadata

lenses = Table(
    'spare_lenses', metadata,
    Column('code', String(24), primary_key=True),
    Column('mount', String(12), nullable=False),
    Column('focal_mm', Integer, nullable=False),
    Column('case_tag', String(24), nullable=False, unique=True),
    Column('state', String(12), nullable=False, default='stored'),
    CheckConstraint("state IN ('stored','on_loan')"),
    CheckConstraint('focal_mm BETWEEN 10 AND 220'),
)

loans = Table(
    'lens_loans', metadata,
    Column('code', String(24), primary_key=True),
    Column('booth_code', String(24), ForeignKey('projection_booths.code'), nullable=False),
    Column('lens_code', String(24), ForeignKey('spare_lenses.code'), nullable=False),
    Column('original_measurement', String(24), ForeignKey('card_measurements.code'), nullable=False),
    Column('epoch', Integer, nullable=False),
    Column('state', String(12), nullable=False, default='active'),
    Column('issued_by', String(90), nullable=False),
    Column('returned_by', String(90)),
    CheckConstraint("state IN ('active','returned')"),
)
