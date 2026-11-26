import {el} from './dom.js';
import {status} from './widgets.js';

export const mayWrite = role => role === 'operator' || role === 'reviewer';
export const percent = value => (value * 100).toFixed(1) + '%';

export function input(name,label,props={}) {
  return el('label',{},el('span',{},label),el('input',{name,required:'',...props}));
}

export function select(name,label,options,selected) {
  return el('label',{},el('span',{},label),el('select',{name,required:''},options.map(([value,text]) =>
    el('option',{value,selected: value === selected ? '' : undefined},text))));
}

export function submit(id,children,label,perform) {
  const note=status('');
  const button=el('button',{type:'submit'},label);
  const form=el('form',{id},children,button,note);
  form.addEventListener('submit',async event => {
    event.preventDefault();
    note.textContent='';
    button.disabled=true;
    try {
      const result=await perform(new FormData(form));
      note.className='status ok';
      note.textContent=result || '';
    } catch(error) {
      note.className='status error';
      note.textContent=error.message;
    } finally {button.disabled=false;}
  });
  return form;
}
