import {power} from './power.js';
import {optics} from './optics.js';
import {cabinet} from './cabinet.js';
import {release} from './release.js';

export const info = {title:'岚幕巡回放映',customer:'岚幕放映车队 · 调试班',
  purpose:'先签放映点配电，再用校准卡追踪软焦、色偏和闪变。'};
export const pages = [
  {key:'power',title:'插座验收',render:power}, {key:'optics',title:'校准卡判别',render:optics},
  {key:'cabinet',title:'镜头箱柜',render:cabinet}, {key:'release',title:'放映交班',render:release},
];
