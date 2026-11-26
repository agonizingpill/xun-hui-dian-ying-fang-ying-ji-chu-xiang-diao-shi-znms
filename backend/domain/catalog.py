from fastapi import HTTPException
from sqlalchemy import select
from core.db import transaction
from domain.booth_tables import booths, measurements, receipts
from domain.lens_tables import lenses, loans


def lookup(conn, table, code, lock=False):
    statement = select(table).where(table.c.code == code)
    if lock:
        statement = statement.with_for_update()
    row = conn.execute(statement).mappings().first()
    if row is None:
        raise HTTPException(404, f'编号 {code} 不存在')
    return dict(row)


def records(conn, table, filters=(), limit=150):
    statement = select(table).where(*filters).order_by(table.c.code.desc()).limit(limit)
    return [dict(row) for row in conn.execute(statement).mappings()]


def power_board():
    with transaction() as conn:
        return {'booths': records(conn, booths), 'receipts': records(conn, receipts)}


def report_board(booth_code):
    with transaction() as conn:
        booth = lookup(conn, booths, booth_code)
        reports = records(conn, measurements, (measurements.c.booth_code == booth_code,))
        loan = active_loan(conn, booth_code)
        return {'booth': booth, 'reports': reports, 'active_loan': loan}


def cabinet():
    with transaction() as conn:
        return {'lenses': records(conn, lenses), 'loans': records(conn, loans)}


def active_loan(conn, booth_code):
    rows = records(conn, loans, (loans.c.booth_code == booth_code, loans.c.state == 'active'), 1)
    return rows[0] if rows else None
