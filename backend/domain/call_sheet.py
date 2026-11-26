from fastapi import HTTPException
from core.audit import record
from core.db import transaction
from domain.booth_tables import booths, measurements
from domain.catalog import active_loan, lookup
from domain.outlet import powered
from domain.states import Artifact, BoothState

MIN_CLEAN_PROBABILITY = .8


def current(booth, report):
    same = (booth['code'], booth['receipt_revision'], booth['optical_epoch'])
    if same != (report['booth_code'], report['receipt_revision'], report['optical_epoch']):
        raise HTTPException(409, '该检测来自不同工位或旧电气、换镜版本')


def clear(booth_code, form, user):
    with transaction() as conn:
        booth = lookup(conn, booths, booth_code, lock=True)
        powered(booth)
        report = lookup(conn, measurements, form.measurement_code)
        current(booth, report)
        loan = active_loan(conn,booth_code)
        if loan and report['source_measurement'] != loan['original_measurement']:
            raise HTTPException(409,'替用镜头必须有一次引用原校准项的复测')
        if report['artifact'] != Artifact.CLEAN or report['probability'] < MIN_CLEAN_PROBABILITY:
            raise HTTPException(409, '检测未通过放映阈值，请处理画质问题后重测')
        conn.execute(booths.update().where(booths.c.code==booth_code)
                     .values(state=BoothState.CLEARED,released_measurement=form.measurement_code))
        record(conn,user,f'clear:{booth_code}:{form.measurement_code}')
        return lookup(conn,booths,booth_code)
