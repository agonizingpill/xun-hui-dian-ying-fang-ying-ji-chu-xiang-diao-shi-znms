import {awaitCompute,request} from './api.js';

export const studio = {
  board: () => request('/booths'),
  outlet: (booth, body) => request('/booths/' + booth + '/outlet', body),
  reports: booth => request('/optics/' + booth),
  test: (booth, body) => request('/optics/' + booth + '/evaluate', body),
  result: awaitCompute,
  save: body => request('/optics/save', body),
  cabinet: () => request('/lenses'),
  lend: body => request('/lenses/lend', body),
  returnLens: (code, body) => request('/lenses/' + code + '/return', body),
  clear: (booth, body) => request('/booths/' + booth + '/clear',body),
};
