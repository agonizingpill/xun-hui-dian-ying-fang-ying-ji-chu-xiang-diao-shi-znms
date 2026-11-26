import {el} from '../dom.js';
import {desk} from '../booth-state.js';

export function showPicker(rows,onSelect) {
  const box=el('div',{class:'strip','aria-label':'选择放映位'});
  for(const booth of rows) {
    const button=el('button',{type:'button',class:desk.booth===booth.code ? 'current':'quiet',onclick:() => {
      desk.booth=booth.code;
      for(const other of box.querySelectorAll('button')) other.className=other===button ? 'current':'quiet';
      onSelect(booth.code);
    }},booth.code);
    box.append(button);
  }
  return box;
}
