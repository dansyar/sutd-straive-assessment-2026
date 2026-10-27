import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

// Exercise the shipped event handlers without packages, a browser, or a live DB.
// This DOM implements only the standard operations used by this application;
// visual layout and native browser behavior still require the browser QA pass.
const appSource = readFileSync(new URL('../web/app.js', import.meta.url), 'utf8');
const htmlSource = readFileSync(new URL('../web/index.html', import.meta.url), 'utf8');
const executable = appSource.slice(0, appSource.lastIndexOf('\n(async () => {'));
const decode = text => text.replace(/&(amp|lt|gt|quot|#39);/g,
  (_, entity) => ({amp: '&', lt: '<', gt: '>', quot: '"', '#39': "'"}[entity]));

class Element {
  constructor(tag, document, attributes = {}) {
    this.tagName = tag.toLowerCase(); this.ownerDocument = document;
    this.attributes = attributes; this.children = []; this.parentElement = null;
    this.classList = {
      add: (...names) => this.className = [...new Set([...this.className.split(/\s+/), ...names])].join(' ').trim(),
      remove: (...names) => this.className = this.className.split(/\s+/).filter(name => !names.includes(name)).join(' '),
      contains: name => this.className.split(/\s+/).includes(name)
    };
  }
  get id() {return this.attributes.id || '';}
  get className() {return this.attributes.class || '';}
  set className(value) {this.attributes.class = value;}
  get disabled() {return Object.hasOwn(this.attributes, 'disabled');}
  set disabled(value) {if (value) this.attributes.disabled = ''; else delete this.attributes.disabled;}
  get dataset() {return Object.fromEntries(Object.entries(this.attributes).filter(([name]) => name.startsWith('data-')).map(([name, value]) => [name.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase()), value]));}
  get textContent() {return this.tagName === '#text' ? this.text : this.children.map(child => child.textContent).join('');}
  set textContent(value) {
    this.children = [];
    if (String(value)) {const node = new Element('#text', this.ownerDocument); node.text = String(value); this.append(node);}
  }
  get innerHTML() {return this._html || '';}
  set innerHTML(html) {
    this._html = html; this.children = [];
    const stack = [this];
    const voidTags = new Set(['input', 'meta', 'link', 'br', 'hr', 'img']);
    for (const token of html.match(/<!--[\s\S]*?-->|<[^>]+>|[^<]+/g) || []) {
      if (token.startsWith('<!')) continue;
      if (token.startsWith('</')) {if (stack.length > 1) stack.pop(); continue;}
      if (token.startsWith('<')) {
        const tag = token.match(/^<([\w-]+)/)?.[1]; if (!tag) continue;
        const attributes = {};
        for (const match of token.slice(tag.length + 1, -1).matchAll(/([\w:-]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g)) {
          attributes[match[1]] = decode(match[2] ?? match[3] ?? match[4] ?? '');
        }
        const element = new Element(tag, this.ownerDocument, attributes);
        stack.at(-1).append(element);
        if (!voidTags.has(tag) && !token.endsWith('/>')) stack.push(element);
      } else {
        const node = new Element('#text', this.ownerDocument); node.text = decode(token); stack.at(-1).append(node);
      }
    }
  }
  get value() {
    if (this._value !== undefined) return this._value;
    if (this.tagName === 'select') {
      const options = this.querySelectorAll('option');
      const selected = options.find(option => Object.hasOwn(option.attributes, 'selected')) || options[0];
      return selected?.attributes.value ?? selected?.textContent ?? '';
    }
    return this.tagName === 'textarea' ? this.textContent : this.attributes.value || '';
  }
  set value(value) {this._value = String(value);}
  append(element) {element.parentElement = this; this.children.push(element);}
  focus() {this.ownerDocument.activeElement = this;}
  scrollIntoView() {}
  showModal() {this.attributes.open = '';}
  close() {delete this.attributes.open;}
  reset() {for (const field of this.querySelectorAll('input,select,textarea')) delete field._value;}
  matches(selector) {
    return selector.split(',').some(part => {
      let simple = part.trim();
      const attrs = [...simple.matchAll(/\[([\w-]+)(?:=(?:"([^"]*)"|'([^']*)'|([^\]]+)))?\]/g)];
      simple = simple.replace(/\[[^\]]+\]/g, '');
      if (attrs.some(([, name, double, single, plain]) => !Object.hasOwn(this.attributes, name)
        || ((double ?? single ?? plain) !== undefined && this.attributes[name] !== (double ?? single ?? plain)))) return false;
      const tag = simple.match(/^[\w-]+/)?.[0];
      if (tag && tag !== this.tagName) return false;
      if ([...simple.matchAll(/#([\w-]+)/g)].some(([, id]) => id !== this.id)) return false;
      if ([...simple.matchAll(/\.([\w-]+)/g)].some(([, name]) => !this.classList.contains(name))) return false;
      return true;
    });
  }
  closest(selector) {
    for (let element = this; element; element = element.parentElement) if (element.matches(selector)) return element;
    return null;
  }
  querySelectorAll(selector) {
    const result = [];
    const selectors = selector.split(',').map(part => part.trim().split(/\s+/));
    const visit = element => {
      for (const child of element.children) {
        if (child.tagName !== '#text' && selectors.some(parts => {
          if (!child.matches(parts.at(-1))) return false;
          let ancestor = child.parentElement;
          for (let i = parts.length - 2; i >= 0; i--) {
            while (ancestor && !ancestor.matches(parts[i])) ancestor = ancestor.parentElement;
            if (!ancestor) return false; ancestor = ancestor.parentElement;
          }
          return true;
        })) result.push(child);
        visit(child);
      }
    };
    visit(this); return result;
  }
  querySelector(selector) {return this.querySelectorAll(selector)[0] || null;}
}

const categories = {
  delay: {label: 'Delay', team: 'Transport operations'},
  documentation: {label: 'Documentation', team: 'Documentation desk'},
  safety: {label: 'Safety', team: 'Safety & security'}
};
const config = {categories, guide: [], default_evidence_dataset: 'fresh2'};
const incident = (id, extra = {}) => ({id, text: `Consignment ${id} needs attention. The receiving desk has the details.`,
  prediction: {category: 'delay', team: categories.delay.team, category_label: 'Delay', urgent: false, review: true},
  decision: null, ...extra});
const review = (id, readonly = true) => ({id, text: `Consignment ${id} is waiting. Its arrival was delayed.`, readonly,
  review: readonly ? {category: 'delay', urgency: 'routine', clarification: false, reason: 'The vehicle is waiting for its arrival slot.'} : null});
const evidence = id => ({id, revision: id, evaluation_n: 60, train_n: 240,
  available_datasets: [{id:'fresh', label:'Fresh 1'}, {id:'fresh2', label:'Fresh 2'}, {id:'test', label:'Original test'}],
  independent_review: {completed:60, total:60, final_test:'available'},
  methods: [{method:'learned', policy:'sensitive', category_n:55, urgency_n:52, urgent_total:13,
    category_accuracy:.89, macro_f1:.90, urgent_recall:1, urgent_misses:0, review_count:43, n:60,
    automation_coverage:.28, cost_units_sensitive:59, cost_units_standard:59, p95_ms:.11, latency_samples:300}]});

function harness() {
  const document = new Element('document', null); document.ownerDocument = document;
  document.createElement = tag => new Element(tag, document);
  document.getElementById = id => document.querySelector(`#${id}`);
  document.innerHTML = htmlSource;
  const local = new Map(), requests = [], listeners = new Map();
  const location = {hash:'#operations/all', reload() {}};
  const context = vm.createContext({document, location, console,
    localStorage: {getItem:key => local.get(key) ?? null, setItem:(key,value) => local.set(key,String(value)), removeItem:key => local.delete(key)},
    history: {replaceState:(_state,_unused,url) => location.hash = url},
    window: {addEventListener:(name, handler) => listeners.set(name,handler)},
    setTimeout:() => 1, clearTimeout() {},
    fetch:(path, options) => new Promise((resolve,reject) => requests.push({path,options,
      succeed:value => resolve({ok:true,json:async()=>value}),
      fail:message => resolve({ok:false,json:async()=>({detail:message})}), reject}))
  });
  vm.runInContext(executable, context, {filename:'web/app.js'});
  const run = code => vm.runInContext(code, context);
  const set = value => {context.fixture = value; run('Object.assign(state, fixture)');};
  set({config});
  return {document, location, local, requests, listeners, run, set,
    get:selector => document.querySelector(selector),
    snapshot:code => JSON.parse(run(`JSON.stringify(${code})`)),
    navigate:hash => {location.hash = hash; return run('navigate()');}};
}
const tick = () => new Promise(resolve => setImmediate(resolve));
const submit = form => form.onsubmit({target:form,preventDefault(){}});

test('late review navigation cannot replace the currently selected report set', async () => {
  const app = harness();
  const older = app.navigate('#review/fresh'), newer = app.navigate('#review/fresh2');
  app.requests[1].succeed([review('NEW')]); await newer;
  app.requests[0].succeed([review('OLD')]); await older;
  assert.deepEqual(app.snapshot('({source:state.reviewSource, ids:state.reviews.map(row=>row.id)})'), {source:'fresh2',ids:['NEW']});
  assert.equal(app.get('#review-source').value, 'fresh2');
  assert.match(app.get('.review-location').textContent, /NEW/);
});

test('late evidence navigation cannot replace the current result', async () => {
  const app = harness(); app.set({evidenceDataset:'fresh'});
  const older = app.navigate('#evidence'); app.set({evidenceDataset:'fresh2'});
  const newer = app.navigate('#evidence');
  app.requests[1].succeed(evidence('NEW')); await newer;
  app.requests[0].succeed(evidence('OLD')); await older;
  assert.equal(app.run('state.evidence.id'), 'NEW');
  assert.equal(app.get('#benchmark').value, 'fresh2');
});

test('late incident navigation cannot replace newer confirmed incident data', async () => {
  const app = harness();
  const older = app.navigate('#operations/all'), newer = app.navigate('#operations/done');
  app.requests[1].succeed([incident('ONE', {decision:{category:'documentation',urgent:false,note:'Checked',created_at:'2026-10-24T00:00:00Z'}})]); await newer;
  app.requests[0].succeed([incident('ONE')]); await older;
  assert.equal(app.run('state.incidents[0].decision?.category'), 'documentation');
  assert.match(app.get('.detail-status').textContent, /Done/);
});

test('manual review save finishing after a source change leaves the new set intact', async () => {
  const app = harness();
  app.set({view:'review',reviewSource:'human',reviews:[review('MANUAL',false)],reviewer:'Local reviewer'});
  app.run('renderReview()');
  app.get('#review-category').value = 'delay'; app.get('#review-urgency').value = 'routine';
  app.get('#review-clarify').value = 'no'; app.get('#review-reason').value = 'Waiting for an arrival slot.';
  const saving = submit(app.get('#review-form'));
  const navigating = app.navigate('#review/fresh2');
  app.requests[1].succeed([review('FRESH')]); await navigating;
  app.requests[0].succeed({saved:true}); await saving;
  assert.equal(app.requests[0].options.method, 'POST');
  assert.deepEqual(app.snapshot('({source:state.reviewSource, ids:state.reviews.map(row=>row.id), index:state.reviewIndex})'), {source:'fresh2',ids:['FRESH'],index:0});
  assert.equal(app.requests.length, 2, 'a completed save must not fetch manual rows into another source');
  assert.match(app.get('.review-location').textContent, /FRESH/);
});

test('benchmark changes keep the latest choice when responses arrive backwards', async () => {
  const app = harness(); app.set({view:'evidence',evidenceDataset:'fresh2',evidence:evidence('INITIAL')}); app.run('renderEvidence()');
  const selector = app.get('#benchmark'); selector.value = 'fresh';
  const older = selector.onchange({target:selector}); selector.value = 'test';
  const newer = selector.onchange({target:selector});
  app.requests[1].succeed(evidence('LATEST')); await newer;
  app.requests[0].succeed(evidence('OLDER')); await older;
  assert.deepEqual(app.snapshot('({dataset:state.evidenceDataset,id:state.evidence.id})'), {dataset:'test',id:'LATEST'});
  assert.equal(app.get('#benchmark').value, 'test');
});

test('successful creation followed by a refresh error offers refresh instead of duplicate creation', async () => {
  const app = harness(); app.run('openNew()');
  app.get('#new-text').value = 'A vehicle is waiting for a new arrival slot.';
  const creating = submit(app.get('#new-form'));
  app.requests[0].succeed({id:'NEW-ONE',prediction:incident('NEW-ONE').prediction}); await tick();
  assert.equal(app.requests[1].path.startsWith('/api/incidents?'), true);
  app.requests[1].fail('The local app is unavailable.'); await creating;
  assert.equal(app.get('dialog[open]'), null);
  assert.equal(app.get('#new-text').value, '');
  assert.equal(app.get('#new-error').textContent, '');
  assert.ok(app.get('#retry-load'), 'the visible recovery action must refresh the saved report');
  const retry = app.get('#retry-load').onclick();
  app.requests[2].succeed([incident('NEW-ONE')]); await retry;
  assert.equal(app.requests.filter(request => request.options.method === 'POST').length, 1);
  assert.equal(app.run('state.selected'), 'NEW-ONE');
});

test('Done search uses the confirmed team instead of the former prediction', () => {
  const app = harness();
  app.set({filter:'done',incidents:[incident('CORRECTED',{decision:{category:'documentation'}})],search:'Documentation desk'});
  assert.deepEqual(app.snapshot('filteredIncidents().map(row=>row.id)'), ['CORRECTED']);
  app.set({search:'Transport operations'});
  assert.equal(app.run('filteredIncidents().length'), 0);
});

test('an urgent report without a review flag still displays Urgent', () => {
  const app = harness();
  app.set({selected:'URGENT',incidents:[incident('URGENT',{prediction:{category:'safety',urgent:true,review:false}})]});
  app.run('renderOperations()');
  assert.equal(app.get('.detail-status').textContent, 'Urgent');
  assert.equal(app.get('#decision-urgency').value, 'urgent');
});

test('operations shortcuts do nothing while the queue is loading', async () => {
  const app = harness(); const navigating = app.navigate('#operations/all');
  assert.equal(app.get('#queue-list'), null);
  for (const key of ['j','k','n','Escape']) {
    assert.doesNotThrow(() => app.listeners.get('keydown')({key,target:app.get('body'),preventDefault(){}}));
  }
  assert.equal(app.get('dialog[open]'), null);
  app.requests[0].succeed([]); await navigating;
  assert.equal(app.get('#queue-list').textContent, 'All clear');
});

test('an empty review set renders a usable empty state without a broken form', () => {
  const app = harness(); app.set({view:'review',reviews:[],reviewIndex:59});
  assert.doesNotThrow(() => app.run('renderReview()'));
  assert.equal(app.get('.page-title h1').textContent, 'Reviews');
  assert.equal(app.get('.empty').textContent, 'No reviews available');
  assert.equal(app.get('#review-form'), null);
  assert.ok(app.get('#navigation').querySelector('a[href="#operations/all"]'));
});

test('confirming a route cannot discard edits made while its save is pending', async () => {
  const app = harness(); app.set({selected:'EDITED',incidents:[incident('EDITED')]});
  app.run('renderOperations()');
  const form = app.get('#decision-form');
  app.get('#decision-note').value = 'Submitted note'; form.oninput();
  const saving = submit(form), editable = !app.get('#decision-note').disabled;
  if (editable) {app.get('#decision-note').value = 'Newer unsaved note'; form.oninput();}
  else {
    assert.equal(app.get('#decision-category').disabled, true);
    assert.equal(app.get('#decision-urgency').disabled, true);
  }
  app.requests[0].succeed({saved:true,created_at:'2026-10-24T00:00:00Z'}); await saving;
  assert.equal(app.run('state.incidents[0].decision.note'), 'Submitted note');
  if (editable) assert.equal(app.run('state.decisionDrafts.EDITED?.note'), 'Newer unsaved note');
});

test('a pending create cannot be dismissed and replaced with a draft that its response erases', async () => {
  const app = harness(); app.run('openNew()'); app.get('#new-text').value = 'First report is ready for triage.';
  const creating = submit(app.get('#new-form'));
  const cancel = app.get('#cancel-new');
  if (!cancel.disabled) cancel.onclick();
  assert.ok(app.get('dialog[open]'), 'Cancel must not imply that an in-flight create was cancelled');
  assert.equal(app.get('#new-text').disabled, true, 'the pending report text must not be replaced before it is saved');
  app.requests[0].succeed({id:'NEW-PENDING'}); await tick();
  app.requests[1].succeed([incident('NEW-PENDING')]); await creating;
  assert.equal(app.get('dialog[open]'), null);
});
