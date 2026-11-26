import {el} from '../dom.js';

export function tag(labels,value) {
  return el('span',{class:'tag','data-state':value},labels[value] || value);
}
