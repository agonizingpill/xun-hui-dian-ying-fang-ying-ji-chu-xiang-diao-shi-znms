from fastapi import HTTPException
from core.audit import record
from core.db import transaction
from domain.booth_tables import booths, measurements
from domain.call_sheet import current
from domain.catalog import active_loan, lookup
from domain.lens_tables import lenses, loans
from domain.outlet import powered
from domain.states import Artifact, BoothState, LensState, LoanState


def lend(form,user):
    with transaction() as conn:
        booth = lookup(conn,booths,form.booth_code,lock=True)
        powered(booth)
        fault = lookup(conn,measurements,form.measurement_code)
        current(booth,fault)
        if fault['artifact'] != Artifact.SOFT:
            raise HTTPException(409,'只有当前软焦报告可触发备用镜头调拨')
        if active_loan(conn,form.booth_code):
            raise HTTPException(409,'放映位仍有未归箱的镜头')
        lens = lookup(conn,lenses,form.lens_code,lock=True)
        if lens['mount'] != booth['mount']:
            raise HTTPException(409,'备用镜头接口与放映机不匹配')
        if lens['state'] != LensState.STORED:
            raise HTTPException(409,'备用镜头已被其他放映位领用')
        epoch = booth['optical_epoch'] + 1
        conn.execute(loans.insert().values(code=form.code,booth_code=form.booth_code,lens_code=form.lens_code,
                     original_measurement=form.measurement_code,epoch=epoch,issued_by=user['sub']))
        conn.execute(lenses.update().where(lenses.c.code==form.lens_code).values(state=LensState.ON_LOAN))
        conn.execute(booths.update().where(booths.c.code==form.booth_code)
                     .values(optical_epoch=epoch,state=BoothState.RETEST))
        record(conn,user,f'lend:{form.code}:{form.lens_code}')
        return lookup(conn,loans,form.code)


def restore(code, form, user):
    with transaction() as conn:
        initial = lookup(conn,loans,code)
        booth = lookup(conn,booths,initial['booth_code'],lock=True)
        loan = lookup(conn,loans,code,lock=True)
        lens = lookup(conn,lenses,loan['lens_code'],lock=True)
        if loan['state'] != LoanState.ACTIVE:
            raise HTTPException(409,'这张领用单已归箱')
        if lens['case_tag'] != form.case_tag:
            raise HTTPException(409,'箱签错配，镜头未归位')
        state = BoothState.SURVEY if booth['state'] != BoothState.RETEST else BoothState.POWERED
        conn.execute(loans.update().where(loans.c.code==code).values(state=LoanState.RETURNED,returned_by=user['sub']))
        conn.execute(lenses.update().where(lenses.c.code==lens['code']).values(state=LensState.STORED))
        conn.execute(booths.update().where(booths.c.code==booth['code'])
                     .values(optical_epoch=booth['optical_epoch']+1,state=state,released_measurement=None))
        record(conn,user,f'restore:{code}:{lens["code"]}')
        return lookup(conn,loans,code)
