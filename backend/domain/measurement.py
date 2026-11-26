from fastapi import HTTPException
from core.audit import record
from core.db import transaction
from core.queueing import result, submit
from domain.booth_tables import booths, measurements
from domain.catalog import active_loan, lookup
from domain.learning import FEATURES
from domain.outlet import powered


def check_card(booth, active, readings):
    if readings['card'] != booth['title_card']:
        raise HTTPException(409, f"此放映位应使用校准卡 {booth['title_card']}")
    source = active['original_measurement'] if active else None
    if readings['source_measurement'] != source:
        raise HTTPException(409, '换镜后须重测同一异常片段并引用原校准记录')


def evaluate(booth_code, form, user):
    with transaction() as conn:
        booth = lookup(conn, booths, booth_code)
        powered(booth)
        reading = form.model_dump()
        check_card(booth, active_loan(conn, booth_code), reading)
    return submit(user,{'booth_code':booth_code,'receipt_revision':booth['receipt_revision'],
                        'optical_epoch':booth['optical_epoch'],'card':reading['card'],
                        'source_measurement':reading['source_measurement'],
                        'sensors':{field:reading[field] for field in FEATURES}})


def save(form, user):
    job = result(user,form.token)
    prompt, output = job['input'], job['result']
    booth_code = prompt['booth_code']
    with transaction() as conn:
        booth = lookup(conn, booths, booth_code, lock=True)
        powered(booth)
        if (booth['receipt_revision'], booth['optical_epoch']) != (prompt['receipt_revision'], prompt['optical_epoch']):
            raise HTTPException(409, '电气/换镜版本已改变，请重新跑校准卡')
        check_card(booth, active_loan(conn, booth_code), prompt)
        conn.execute(measurements.insert().values(code=form.code, booth_code=booth_code, card=prompt['card'],
                     receipt_revision=prompt['receipt_revision'], optical_epoch=prompt['optical_epoch'],
                     source_measurement=prompt['source_measurement'], **prompt['sensors'],
                     artifact=output['artifact'], probability=output['probability'],
                     model_version=output['model_version'], votes=output['votes'],
                     compute_token=form.token, measured_by=user['sub']))
        record(conn,user,f'measure:{form.code}:{output["artifact"]}')
        return lookup(conn, measurements, form.code)
