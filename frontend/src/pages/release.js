import {el} from '../dom.js';
import {studio} from '../booth-api.js';
import {artifacts,booths,desk} from '../booth-state.js';
import {percent,select,submit} from '../inputs.js';
import {status,titleBlock} from '../widgets.js';
import {showPicker} from '../components/show-picker.js';
import {tag} from '../components/status-tag.js';

export async function release(root,role) {
  const sheet=el('section',{class:'ledger'});
  const gate=el('section',{class:'action'});
  const {booths:all}=await studio.board();
  async function draw(code,message) {
    const data=await studio.reports(code);
    if (desk.booth!==code) return;
    const booth=data.booth;
    const current=data.reports.filter(row=>row.receipt_revision===booth.receipt_revision &&
      row.optical_epoch===booth.optical_epoch);
    sheet.replaceChildren(el('h2',{},booth.venue),el('p',{class:'clock'},booth.show_slot),
      tag(booths,booth.state),booth.released_measurement?el('div',{class:'callout'},
        el('strong',{},'放映回执'),el('p',{class:'mono'},booth.released_measurement)):null,
      el('h3',{},'本期画质凭证'),current.length?current.map(row=>el('div',{class:'stationrow'},
        el('p',{class:'mono'},row.code+' · '+percent(row.probability)),tag(artifacts,row.artifact))):
        status('当前接电与镜头版本下没有有效检测。'));
    gate.replaceChildren(el('h2',{},'交班放行'),message?status(message,'ok'):null,
      data.active_loan ? el('p',{class:'callout'},'当前镜头为替用件 · 复测必须引用 '+data.active_loan.original_measurement):null);
    if(role==='reviewer' && current.length && booth.state!=='cleared') {
      gate.append(submit('clear',[select('measurement_code','本期校准凭证',current.map(row=>[row.code,row.code + ' · ' + artifacts[row.artifact]]))],
        '确认放映放行',async form=>{
          await studio.clear(code,{measurement_code:form.get('measurement_code')});
          await draw(code,'已签放映回执，交给开场值守。');
        }));
    } else gate.append(status('复核员可对当前合格凭证签发开场。'));
  }
  root.replaceChildren(titleBlock('巡回放映 / 交班','放映核可单','当前电气、镜头和题卡版本全部吻合后，复核员签放映。'),
    showPicker(all,code=>draw(code).catch(error=>sheet.replaceChildren(status(error.message,'error')))),
    el('div',{class:'spread'},sheet,gate));
  await draw(desk.booth);
}
