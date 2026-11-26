import {el} from '../dom.js';
import {studio} from '../booth-api.js';
import {desk,lenses,loans} from '../booth-state.js';
import {input,select,submit} from '../inputs.js';
import {status,titleBlock} from '../widgets.js';
import {tag} from '../components/status-tag.js';

export async function cabinet(root,role) {
  const bin=el('div',{class:'lens-board'});
  const cards=el('div',{class:'film'});
  const editor=el('section',{class:'action'});
  async function load(message) {
    const [{lenses:spares,loans:log},{booths}]=await Promise.all([studio.cabinet(),studio.board()]);
    bin.replaceChildren(...spares.map(lens=>el('article',{class:'lens'},el('h3',{class:'mono'},lens.code),
      el('p',{},lens.mount+' · '+lens.focal_mm+' mm'),tag(lenses,lens.state),el('p',{class:'mono'},lens.case_tag))));
    cards.replaceChildren(...log.map(item=>el('details',{open:item.state==='active'?'':undefined},
      el('summary',{},item.code+' · '+item.lens_code+' · ',tag(loans,item.state)),
      el('p',{},item.booth_code+' · 原检测 '+item.original_measurement),
      ...(role==='reviewer' && item.state==='active'?[submit('back-'+item.code,
        [input('case_tag','归箱箱签',{placeholder:'CASE-P35'})],'核箱签并归还',async values=>{
          await studio.returnLens(item.code,{case_tag:values.get('case_tag')});
          await load(item.code+' 已归箱。');
        })]:[]))));
    if (!log.length) cards.append(status('暂无调拨单。'));
    editor.replaceChildren(el('h2',{},'发放备用镜头'),message?status(message,'ok'):null,
      role==='reviewer'?submit('lend',[
        input('code','领用单号',{placeholder:'LN-1124-01'}),
        select('booth_code','放映位',booths.map(x=>[x.code,x.venue]),desk.booth),
        select('lens_code','库内镜头',spares.filter(x=>x.state==='stored').map(x=>[x.code,x.code])),
        input('measurement_code','原软焦检测',{value:desk.fault || ''})],
      '锁镜头并出箱',async form=>{
        const result=await studio.lend(Object.fromEntries(form));
        desk.booth=result.booth_code;
        await load(result.code+' 出箱，必须按原卡项复测。');
      }):status('只有复核员可签发镜头和复核箱签。'));
  }
  root.replaceChildren(titleBlock('巡回放映 / 器材', '备用镜头箱柜','只有当前软焦记录可触发调拨。镜头型号和箱签随放映位跟踪。'),
    el('div',{class:'spread'},el('section',{class:'ledger'},el('h2',{},'箱内光学件'),bin,
      el('h2',{},'调拨与归箱'),cards),editor));
  await load();
}
