import {el} from '../dom.js';
import {artifacts,fields} from '../booth-state.js';
import {percent} from '../inputs.js';
import {tag} from './status-tag.js';

export function pattern(card) {
  return el('div',{class:'cal-card',role:'img','aria-label':'校准卡 ' + card},
    ['01','02','03','04'].map(mark=>el('i',{},mark)));
}

export function votes(output) {
  return el('ul',{class:'votes'},Object.entries(output.votes).map(([label,value]) =>
    el('li',{},el('span',{},artifacts[label]),el('meter',{min:0,max:1,value,'aria-label':artifacts[label]}),
      el('span',{class:'mono'},percent(value)))));
}

export function measurement(report) {
  return el('details',{},el('summary',{},report.code+' · ',tag(artifacts,report.artifact),' · '+percent(report.probability)),
    el('p',{class:'mono'},report.card+' · 电气 '+report.receipt_revision+' · 光学 '+report.optical_epoch),
    el('p',{},report.source_measurement ? '原检测 '+report.source_measurement:'首次检测'),
    el('p',{},Object.entries(fields).map(([key,label])=>label+' '+report[key].toFixed(2)).join(' · ')),
    votes(report));
}
