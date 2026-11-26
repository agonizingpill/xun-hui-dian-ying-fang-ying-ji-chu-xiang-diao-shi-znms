import {el} from '../dom.js';
import {studio} from '../booth-api.js';
import {booths,desk} from '../booth-state.js';
import {input,mayWrite,submit} from '../inputs.js';
import {status,titleBlock} from '../widgets.js';
import {showPicker} from '../components/show-picker.js';
import {tag} from '../components/status-tag.js';

export async function power(root,role) {
  const venue=el('section',{class:'ledger'});
  const actions=el('section',{class:'action'});
  const lineup=el('div',{class:'strip'});
  async function load() {
    const data=await studio.board();
    lineup.replaceChildren(showPicker(data.booths,draw));
    draw(desk.booth);
    function draw(code) {
      const booth=data.booths.find(row=>row.code===code);
      const history=data.receipts.filter(row=>row.booth_code===code).sort((a,b)=>b.revision-a.revision);
      venue.replaceChildren(el('h2',{},booth.venue),el('p',{class:'clock'},booth.show_slot),
        el('p',{},booth.projector+' · '+booth.mount+' 卡口 · '+booth.title_card),
        tag(booths,booth.state),el('h3',{},'电气签收'),
        history.length ? history.map(row=>el('div',{class:'stationrow'},
          el('div',{},el('p',{class:'mono'},row.code+' / '+row.circuit),
            el('p',{},row.voltage+' V · '+(row.earth?'接地确认':'未接地')+' · 跳闸 '+row.breakers+' 次')),
          el('div',{},row.valid?'验收合格':'拒绝接电'))) : status('此场地尚未验收。'));
      actions.replaceChildren(el('h2',{},'实际测电回执'));
      if (!mayWrite(role) || booth.state==='cleared') {
        actions.append(status('此放映位当前不可写入电气回执。'));
        return;
      }
      actions.append(submit('outlet',[input('circuit','配电箱回路',{value:'BOX-03'}),
        input('voltage','线电压（V）',{type:'number',step:'.1',value:'220'}),
        input('breakers','试运行跳闸次数',{type:'number',min:'0',max:'100',value:'0'}),
        el('label',{},el('input',{type:'checkbox',name:'earth'}),' 接地确认')],
        '签电气回执',async form=>{
          const result=await studio.outlet(booth.code,{circuit:form.get('circuit'),voltage:Number(form.get('voltage')),
            breakers:Number(form.get('breakers')),earth:form.has('earth')});
          await load();
          actions.prepend(status(result.receipt.valid?'插座验收通过，允许跑校准卡。':'接电条件不足，已留拒绝回执。','ok'));
        }));
    }
  }
  root.replaceChildren(titleBlock('巡回放映 / 电气', '放映点插座验收','每个场次留独立配电回执。接地、电压和试运行跳闸条件必须同时合格。'),
    lineup,el('div',{class:'spread'},venue,actions));
  await load();
}
