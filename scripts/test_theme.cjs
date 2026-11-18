// Optional developer test: Node's standard library only. Node is NOT needed to run FoodLink.
const vm = require('node:vm');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const source = fs.readFileSync(require('node:path').join(__dirname, '../static/theme.js'), 'utf8');
function run({saved=null,dark=false,blocked=false}={}) {
  const data = new Map(saved ? [['foodlink-theme',saved]] : []);
  const attributes = {}, domEvents={},windowEvents={};
  const button={hidden:true,attrs:{},label:{},events:{},setAttribute(k,v){this.attrs[k]=v},querySelector(){return this.label},addEventListener(k,v){this.events[k]=v}};
  const media={matches:dark,addEventListener(k,v){this.change=v}};
  const localStorage={getItem(k){if(blocked)throw Error('blocked');return data.get(k)||null},setItem(k,v){if(blocked)throw Error('blocked');data.set(k,v)}};
  const document={documentElement:{style:{},setAttribute(k,v){attributes[k]=v},getAttribute(k){return attributes[k]}},querySelectorAll(){return [button]},addEventListener(k,v){domEvents[k]=v}};
  const window={matchMedia(){return media},addEventListener(k,v){windowEvents[k]=v}};
  vm.runInNewContext(source,{window,document,localStorage});
  domEvents.DOMContentLoaded();
  return {data,attributes,button,media,windowEvents};
}
let t=run();assert.equal(t.attributes['data-bs-theme'],'light');
t=run({dark:true});assert.equal(t.attributes['data-bs-theme'],'dark');
t=run({saved:'light',dark:true});assert.equal(t.attributes['data-bs-theme'],'light');
t.button.events.click();assert.equal(t.attributes['data-bs-theme'],'dark');assert.equal(t.data.get('foodlink-theme'),'dark');assert.equal(t.button.attrs['aria-label'],'Switch to light mode');
assert.equal(run({saved:t.data.get('foodlink-theme')}).attributes['data-bs-theme'],'dark');
t=run({blocked:true});t.button.events.click();assert.equal(t.attributes['data-bs-theme'],'dark');
t=run({saved:'invalid',dark:true});assert.equal(t.attributes['data-bs-theme'],'dark');
t=run();t.media.change({matches:true});assert.equal(t.attributes['data-bs-theme'],'dark');
t=run({saved:'light'});t.media.change({matches:true});assert.equal(t.attributes['data-bs-theme'],'light');
t.data.set('foodlink-theme','dark');t.windowEvents.storage({key:'foodlink-theme'});assert.equal(t.attributes['data-bs-theme'],'dark');assert.equal(t.attributes['data-theme'],'dark');assert.equal(t.button.hidden,false);
console.log('Theme checks passed: system defaults, saved preference, toggle, persistence, blocked storage, invalid preference, system changes, cross-tab updates and accessible labels.');
