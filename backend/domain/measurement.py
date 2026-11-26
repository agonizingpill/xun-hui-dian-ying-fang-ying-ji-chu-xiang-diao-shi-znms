from fastapi import HTTPException
from sqlalchemy import select
from core.audit import record
from core.db import transaction
from core.queueing import result, submit
from domain.booth_tables import booths, measurements
from domain.catalog import active_loan, lookup
from domain.learning import FEATURES
from domain.outlet import powered
from domain.states import BoothState

VALUE_TOLERANCE = 1e-6


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


def gaps(row):
    return [field for field in FEATURES if row[field] is None]


def supplement_job(booth_code, report, sensors, separate):
    return {'booth_code': booth_code, 'receipt_revision': report['receipt_revision'],
            'optical_epoch': report['optical_epoch'], 'card': report['card'],
            'source_measurement': report['source_measurement'], 'sensors': sensors,
            'supplement_of': report['code'], 'separate': separate}


def supplement(booth_code, form, user):
    with transaction() as conn:
        booth = lookup(conn, booths, booth_code, lock=True)
        report = lookup(conn, measurements, form.measurement_code, lock=True)
        if report['booth_code'] != booth_code:
            raise HTTPException(404, f"编号 {form.measurement_code} 不存在")
        missing = gaps(report)
        if booth['state'] == BoothState.CLEARED:
            if booth['released_measurement'] != report['code']:
                raise HTTPException(409, '场次已经放行，需等待收卷')
            if not missing:
                raise HTTPException(409, '该校准单四项读数齐全，无需补测')
            sensors = {field: report[field] for field in FEATURES}
            sensors[missing[0]] = form.value
            # 签放先办成：另记补测，原单与签放凭据留原样
            return submit(user, supplement_job(booth_code, report, sensors, True)) | {'separate': True}
        powered(booth)
        if (booth['receipt_revision'], booth['optical_epoch']) != (report['receipt_revision'], report['optical_epoch']):
            raise HTTPException(409, '电气/换镜版本已改变，旧单不能补测或签放')
        if report['judgment_pending']:
            if abs(report['supplement_value'] - form.value) > VALUE_TOLERANCE:
                raise HTTPException(409, '同次补测已入账，重试不重复入账')
            sensors = {field: report[field] for field in FEATURES}
            sensors[report['supplement_field']] = report['supplement_value']
            return submit(user, supplement_job(booth_code, report, sensors, False)) | {'separate': False}
        if not missing:
            raise HTTPException(409, '该校准单四项读数齐全，无需补测')
        field = missing[0]
        sensors = {name: report[name] for name in FEATURES}
        sensors[field] = form.value
        conn.execute(measurements.update().where(measurements.c.code == report['code'])
                     .values(judgment_pending=1, supplement_field=field, supplement_value=form.value))
        record(conn, user, f'supplement:{report["code"]}:{field}')
        return submit(user, supplement_job(booth_code, report, sensors, False)) | {'separate': False}


def save(form, user):
    job = result(user,form.token)
    prompt, output = job['input'], job['result']
    booth_code = prompt['booth_code']
    with transaction() as conn:
        booth = lookup(conn, booths, booth_code, lock=True)
        if prompt.get('supplement_of'):
            return save_supplement(conn, booth, form, prompt, output, user)
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


def save_supplement(conn, booth, form, prompt, output, user):
    report = lookup(conn, measurements, prompt['supplement_of'], lock=True)
    if report['booth_code'] != booth['code']:
        raise HTTPException(404, f"编号 {prompt['supplement_of']} 不存在")
    if prompt.get('separate'):
        # 签放凭据留原样：补测另记新单，不改已签放的原单
        if form.code == report['code']:
            raise HTTPException(409, '另记补测需使用新的检测单号')
        existing = conn.execute(select(measurements).where(measurements.c.compute_token == form.token)).mappings().first()
        if existing is not None:
            return dict(existing)
        conn.execute(measurements.insert().values(code=form.code, booth_code=booth['code'], card=report['card'],
                     receipt_revision=report['receipt_revision'], optical_epoch=report['optical_epoch'],
                     source_measurement=report['source_measurement'], supplement_of=report['code'],
                     **prompt['sensors'], artifact=output['artifact'], probability=output['probability'],
                     model_version=output['model_version'], votes=output['votes'],
                     compute_token=form.token, measured_by=user['sub']))
        record(conn, user, f'supplement-note:{form.code}:{report["code"]}')
        return lookup(conn, measurements, form.code)
    # 补齐原单再判，已有读数照留
    if not report['judgment_pending']:
        return report
    powered(booth)
    if (booth['receipt_revision'], booth['optical_epoch']) != (prompt['receipt_revision'], prompt['optical_epoch']):
        raise HTTPException(409, '电气/换镜版本已改变，请重新跑校准卡')
    if form.code != report['code']:
        raise HTTPException(409, '补齐原单须沿用原检测单号')
    conn.execute(measurements.update().where(measurements.c.code == report['code'])
                 .values(**{report['supplement_field']: report['supplement_value']},
                         artifact=output['artifact'], probability=output['probability'],
                         model_version=output['model_version'], votes=output['votes'],
                         judgment_pending=0, supplement_field=None, supplement_value=None))
    record(conn, user, f'remeasure:{report["code"]}:{output["artifact"]}')
    return lookup(conn, measurements, report['code'])
