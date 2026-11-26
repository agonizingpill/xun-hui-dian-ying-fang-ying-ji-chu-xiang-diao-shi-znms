import {el} from '../dom.js';
import {studio} from '../booth-api.js';
import {artifacts,booths,desk,fields} from '../booth-state.js';
import {input,mayWrite,percent,submit} from '../inputs.js';
import {status,titleBlock} from '../widgets.js';
import {pattern,votes,measurement} from '../components/card-readout.js';
import {showPicker} from '../components/show-picker.js';
import {tag} from '../components/status-tag.js';

export async function optics(root,role) {
  const picker=el('div',{});
  const reading=el('section',{class:'action'});
  const result=el('section',{class:'ledger'});
  const {booths:all}=await studio.board();
  async function load(code) {
    const data=await studio.reports(code);
    const booth=data.booth;
    if (desk.booth!==code) return;
    result.replaceChildren(el('div',{class:'light-table'},pattern(booth.title_card),
      el('div',{class:'exposure'},el('strong',{},booth.title_card),tag(booths,booth.state),
        el('span',{class:'mono'},'电气 '+booth.receipt_revision+' · 光学 '+booth.optical_epoch))),
      el('h2',{},'历次校准'),data.reports.length ? el('div',{class:'film'},data.reports.map(measurement))
        : status('本放映位还没有签入的校准。'));
    reading.replaceChildren(el('h2',{},'实测校准卡'));
    if (!mayWrite(role) || ['survey','cleared'].includes(booth.state)) {
      reading.append(status('等待有效电气回执，已放行的场次进入归箱。'));
      return;
    }
    const source=data.active_loan?.original_measurement;
    reading.append(submit('checkout',[input('card','校准卡码',{value:booth.title_card}),
      ...(source?[input('source_measurement','引用原异常段',{value:source})]:[]),
      el('div',{class:'fields'},Object.entries(fields).map(([key,label]) =>
        input(key,label+' / 归一值',{type:'number',min:'0',max:'1',step:'.01',value:'.12'})))],
    '判别画质',async form=>{
      const sensors=Object.fromEntries(Object.keys(fields).map(key=>[key,Number(form.get(key))]));
      const command=await studio.test(code,{card:form.get('card'),source_measurement:form.get('source_measurement'),...sensors});
      const prediction=await studio.result(command.token,job=>{
        if (job.status==='queued') result.prepend(status('计算待命'));
      });
      if(prediction.status!=='ready') throw new Error(prediction.detail);
      if(desk.booth!==code || !result.isConnected) return;
      const rating=prediction.result;
      result.replaceChildren(el('h2',{},'校准判别回执'),el('div',{class:'callout'},
        tag(artifacts,rating.artifact),el('span',{class:'mono'},' · '+percent(rating.probability))),
        votes(rating),el('p',{class:'mono'},rating.model_version+' · 模拟留出 '+rating.holdout.holdout+' 条'),
        submit('save-card',[input('code','检测单号',{placeholder:'RD-1124-A'})],'签入检测单',async values=>{
          const record=await studio.save({code:values.get('code'),token:command.token});
          desk.fault=record.artifact==='soft_focus'?record.code:null;
          await load(code);
          result.prepend(status(record.code+' 检测单已签入。','ok'));
        }));
    }));
  }
  picker.append(showPicker(all,code=>load(code).catch(error=>result.replaceChildren(status(error.message,'error')))));
  root.replaceChildren(titleBlock('巡回放映 / 光学', '校准卡画质判别','输入卡面测得的四项特征。更换镜头后要引用同一异常片段重新检测。'),
    picker,el('div',{class:'spread reversed'},reading,result));
  await load(desk.booth);
}
