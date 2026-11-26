from domain.booth_tables import booths, receipts
from domain.lens_tables import lenses

FIXTURES = (
    (booths, [
        {'code':'LM-SOUTH','venue':'藤川南场 · 礼堂','projector':'RIG-C12','mount':'PL',
         'title_card':'GRID-41','show_slot':'11-24 19:30 / 第一场'},
        {'code':'LM-RIVER','venue':'河台操场 · 周末影棚','projector':'RIG-C08','mount':'EF',
         'title_card':'GRID-62','show_slot':'11-24 20:00 / 主放','state':'powered','receipt_revision':1},
        {'code':'LM-YARD','venue':'岭背工友院 · 露天','projector':'RIG-C17','mount':'PL',
         'title_card':'GRID-79','show_slot':'11-24 19:00 / 提前场','state':'powered','receipt_revision':1},
    ]),
    (receipts, [
        {'code':'LM-RIVER-1','booth_code':'LM-RIVER','revision':1,'circuit':'BOX-06','voltage':218,
         'earth':True,'breakers':0,'valid':True,'signed_by':'operator@demo.test'},
        {'code':'LM-YARD-1','booth_code':'LM-YARD','revision':1,'circuit':'BOX-18','voltage':221,
         'earth':True,'breakers':0,'valid':True,'signed_by':'operator@demo.test'},
    ]),
    (lenses, [
        {'code':'LEN-PL-35','mount':'PL','focal_mm':35,'case_tag':'CASE-P35'},
        {'code':'LEN-PL-50','mount':'PL','focal_mm':50,'case_tag':'CASE-P50'},
        {'code':'LEN-EF-40','mount':'EF','focal_mm':40,'case_tag':'CASE-E40'},
    ]),
)
