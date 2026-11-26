from fastapi import APIRouter, Depends
from core.auth import actor, allow
from core.roles import REVIEW, WRITE
from domain import call_sheet, catalog, measurement, outlet, spares
from domain.schema import CardReading, Clearance, LensReturn, Loan, Outlet, SaveCard

power = APIRouter(prefix='/booths')
optics = APIRouter(prefix='/optics')
cabinet = APIRouter(prefix='/lenses')
routers = (power, optics, cabinet)


@power.get('')
def power_board(user=Depends(actor)):
    return catalog.power_board()


@power.post('/{code}/outlet')
def power_receipt(code: str, form: Outlet, user=Depends(actor)):
    allow(user,WRITE)
    return outlet.inspect(code,form,user)


@optics.get('/{code}')
def reports(code: str,user=Depends(actor)):
    return catalog.report_board(code)


@optics.post('/{code}/evaluate',status_code=202)
def judge(code: str,form: CardReading,user=Depends(actor)):
    allow(user,WRITE)
    return measurement.evaluate(code,form,user)


@optics.post('/save',status_code=201)
def save(form: SaveCard,user=Depends(actor)):
    allow(user,WRITE)
    return measurement.save(form,user)


@cabinet.get('')
def stock(user=Depends(actor)):
    return catalog.cabinet()


@cabinet.post('/lend',status_code=201)
def lend(form: Loan,user=Depends(actor)):
    allow(user,REVIEW)
    return spares.lend(form,user)


@cabinet.post('/{code}/return')
def back(code: str,form: LensReturn,user=Depends(actor)):
    allow(user,REVIEW)
    return spares.restore(code,form,user)


@power.post('/{code}/clear')
def clear(code: str,form: Clearance,user=Depends(actor)):
    allow(user,REVIEW)
    return call_sheet.clear(code,form,user)
