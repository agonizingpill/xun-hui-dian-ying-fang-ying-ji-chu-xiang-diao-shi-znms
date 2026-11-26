from fastapi import HTTPException
from core.audit import record
from core.db import transaction
from domain.booth_tables import booths, receipts
from domain.catalog import active_loan, lookup
from domain.states import BoothState

POWER_MIN = 209
POWER_MAX = 231
MAX_BREAKERS = 1


def inspect(booth_code, form, user):
    with transaction() as conn:
        booth = lookup(conn, booths, booth_code, lock=True)
        if booth['state'] == BoothState.CLEARED:
            raise HTTPException(409, '场次已放行，套箱回收后才可重新验收')
        revision = booth['receipt_revision'] + 1
        passed = (POWER_MIN <= form.voltage <= POWER_MAX and form.earth and form.breakers <= MAX_BREAKERS)
        if not passed:
            state = BoothState.SURVEY
        elif active_loan(conn, booth_code):
            state = BoothState.RETEST
        else:
            state = BoothState.POWERED
        code = f"{booth_code}-{revision}"
        conn.execute(receipts.insert().values(code=code, booth_code=booth_code, revision=revision,
                     **form.model_dump(), valid=passed, signed_by=user['sub']))
        conn.execute(booths.update().where(booths.c.code == booth_code)
                     .values(receipt_revision=revision, state=state))
        record(conn, user, f'outlet:{code}:{int(passed)}')
        return {'state': state, 'receipt': lookup(conn, receipts, code)}


def powered(booth):
    if booth['state'] == BoothState.SURVEY:
        raise HTTPException(409, '需要当前有效的插座验收单，先检查接地和电压')
    if booth['state'] == BoothState.CLEARED:
        raise HTTPException(409, '场次已经放行，需等待收卷')
