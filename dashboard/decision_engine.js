/* Business value snapshot: deterministic math; no model or external service. */
(function (root) {
  'use strict';
  function number(value, label, max, integer) {
    if (typeof value !== 'number' || !Number.isFinite(value) || value < 0 || value > max || (integer && !Number.isInteger(value))) {
      throw new Error(label + ' must be a finite number in the supported range.');
    }
    return value;
  }
  function text(value, label) {
    if (typeof value !== 'string' || value.length > 500) throw new Error(label + ' must contain at most 500 characters.');
    return value.trim();
  }
  function revenueBridge(previous, current, previousOrders, currentOrders) {
    previous = number(previous, 'Previous revenue', 1e15, false);
    current = number(current, 'Current revenue', 1e15, false);
    previousOrders = number(previousOrders, 'Previous orders', 1e9, true);
    currentOrders = number(currentOrders, 'Current orders', 1e9, true);
    if (!previousOrders || !currentOrders) throw new Error('Both periods need at least one order.');
    const priorAov = previous / previousOrders, currentAov = current / currentOrders;
    return {previous_revenue_inr: previous, current_revenue_inr: current,
      previous_orders: previousOrders, current_orders: currentOrders,
      previous_aov_inr: priorAov, current_aov_inr: currentAov,
      volume_effect: (currentOrders - previousOrders) * priorAov,
      basket_effect: currentOrders * (currentAov - priorAov), total_change: current - previous};
  }
  function scenario(incrementalOrders, contributionPerOrder, campaignCost) {
    const orders = number(incrementalOrders, 'Expected incremental orders', 1e9, false);
    const contribution = number(contributionPerOrder, 'Contribution per order', 1e9, false);
    const cost = number(campaignCost, 'Campaign cost', 1e12, false);
    const compute = multiplier => ({assumed_incremental_orders: orders * multiplier,
      assumed_incremental_contribution_inr: orders * multiplier * contribution,
      campaign_cost_inr: cost, net_inr: orders * multiplier * contribution - cost});
    return {low: compute(.5), base: compute(1), high: compute(1.5),
      break_even_incremental_orders: contribution > 0 ? Math.ceil(cost / contribution) : (cost === 0 ? 0 : null)};
  }
  function makeRecord(input) {
    const bridge = revenueBridge(input.previous, input.current, input.previousOrders, input.currentOrders);
    const scenarios = scenario(input.incrementalOrders, input.contributionPerOrder, input.campaignCost);
    let productBridge = null;
    if (input.productBridge) {
      const p = input.productBridge;
      if (p.schema_version !== 1 || p.previous_period !== input.previousPeriod || p.current_period !== input.currentPeriod ||
          Math.abs(p.previous_revenue_inr - input.previous) > 0.51 || Math.abs(p.current_revenue_inr - input.current) > 0.51 ||
          !p.reconciliation || p.reconciliation.sql_pandas !== 'PASS' || Math.abs(p.reconciliation.bridge_residual_inr) > 0.0001) {
        throw new Error('Product bridge does not match the dashboard periods and totals.');
      }
      productBridge = p;
    }
    const status = input.status || 'proposed';
    if (!['proposed', 'approved', 'deferred'].includes(status)) throw new Error('Choose a supported decision status.');
    const note = text(input.observedNote || '', 'Follow-up note');
    return {schema_version: 1, project: 'ecommerce', created_at_utc: new Date().toISOString(),
      source: {dataset: 'data/processed/master_orders.csv', classification: 'synthetic',
        definition: 'Embedded dashboard monthly order counts and whole-rupee revenue totals; checked against the underlying dataset in tests.'},
      scope: {previous_period: text(input.previousPeriod || '', 'Previous period'),
        current_period: text(input.currentPeriod || '', 'Current period'),
        definition: 'Synthetic order-line snapshot; revenue uses Delivered + Processing orders and counts distinct order IDs. Embedded dashboard values are rounded to whole rupees.'},
      evidence: bridge, product_price_volume_mix: productBridge,
      assumptions: {expected_incremental_orders: input.incrementalOrders,
        assumed_contribution_per_order_inr: input.contributionPerOrder, assumed_campaign_cost_inr: input.campaignCost},
      scenarios: scenarios,
      decision: {status: status, action: text(input.action || '', 'Action'),
        success_metric: text(input.kpi || '', 'KPI'), follow_up: text(input.followUp || '', 'Validation plan')},
      observed_outcome: note ? {source: 'user-entered, unverified', note: note} : null,
      limitations: 'Synthetic dataset. Order-volume versus average-basket decomposition is descriptive, not a causal decomposition. Product price/volume/mix bridge is a separate, path-dependent calculation when provided. Scenarios are modeled assumptions, not actual revenue, profit, savings or results.'};
  }
  const HISTORY_LIMIT = 256000, ENTRY_LIMIT = 30;
  function safeCopy(value) {
    function check(item, depth) {
      if (depth > 30) throw new Error('History nesting is too deep.');
      if (item === null || typeof item === 'string' || typeof item === 'boolean') return;
      if (typeof item === 'number') { if (!Number.isFinite(item)) throw new Error('Non-finite values are not allowed.'); return; }
      if (Array.isArray(item)) { item.forEach(v => check(v, depth + 1)); return; }
      if (typeof item === 'object') { Object.values(item).forEach(v => check(v, depth + 1)); return; }
      throw new Error('History must contain JSON values only.');
    }
    check(value, 0);
    const encoded = JSON.stringify(value);
    if (new TextEncoder().encode(encoded).length > HISTORY_LIMIT) throw new Error('History exceeds 256 KB.');
    return JSON.parse(encoded);
  }
  function newHistory() { return {schema_version:1, project:'ecommerce', trust:'local browser, unverified', entries:[]}; }
  function checkHistory(h) {
    if (!h || h.schema_version !== 1 || h.project !== 'ecommerce' || !Array.isArray(h.entries) || h.entries.length > ENTRY_LIMIT) throw new Error('Invalid history version, project or size.');
    const ids = new Set();
    h.entries.forEach(entry => {
      if (!entry || typeof entry.id !== 'string' || !/^[0-9a-f]{32}$/.test(entry.id) || ids.has(entry.id)) throw new Error('Invalid or duplicate entry id.');
      ids.add(entry.id);
      const r=entry.record;
      if (!r || r.schema_version !== 1 || r.project !== 'ecommerce' || ['source','scope','evidence','assumptions','scenarios','decision'].some(k => !r[k] || typeof r[k] !== 'object' || Array.isArray(r[k]))) throw new Error('Invalid decision record.');
      text(r.decision.action || '', 'Action');
      if (!['proposed','approved','deferred'].includes(r.decision.status)) throw new Error('Invalid decision status.');
      if (!Array.isArray(entry.followups) || entry.followups.length > ENTRY_LIMIT) throw new Error('Invalid follow-ups.');
      entry.followups.forEach(f => {
        if (!f || !text(f.metric, 'Metric') || !text(f.unit, 'Unit') || f.metric.length > 120 || f.unit.length > 80) throw new Error('Metric and unit are required.');
        text(f.note, 'Note');
        if (typeof f.observed !== 'number' || !Number.isFinite(f.observed) || Math.abs(f.observed)>1e15 || (f.baseline !== null && (typeof f.baseline !== 'number' || !Number.isFinite(f.baseline) || Math.abs(f.baseline)>1e15))) throw new Error('Follow-up values must be finite.');
        if (typeof f.observed_date !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(f.observed_date) || !Number.isFinite(Date.parse(f.observed_date)) || new Date(f.observed_date).toISOString().slice(0,10) !== f.observed_date) throw new Error('Date must be valid YYYY-MM-DD.');
        if (f.verification !== 'user-entered, unverified') throw new Error('Follow-up verification label is invalid.');
        if ((f.baseline === null && f.difference !== null) || (f.baseline !== null && (typeof f.difference !== 'number' || Math.abs(f.difference - (f.observed - f.baseline)) > 1e-8))) throw new Error('Follow-up difference does not reconcile.');
      });
    });
    return h;
  }
  function addSnapshot(history, record) {
    const h=checkHistory(safeCopy(history)), r=safeCopy(record);
    if (h.entries.length >= ENTRY_LIMIT) throw new Error('History is full; export it before starting a new one.');
    if (!r || r.project !== 'ecommerce' || r.schema_version !== 1) throw new Error('Decision record does not match this project.');
    if (!root.crypto || typeof root.crypto.randomUUID !== 'function') throw new Error('Secure browser context is required to save a history entry.');
    h.entries.push({id:root.crypto.randomUUID().replaceAll('-', ''), record:r, followups:[]});
    return checkHistory(h);
  }
  function addFollowup(history, id, input) {
    const h=checkHistory(safeCopy(history)), entry=h.entries.find(e=>e.id===id);
    if (!entry || entry.followups.length >= ENTRY_LIMIT) throw new Error('Entry is missing or has too many follow-ups.');
    const observed=input.observed, baseline=input.baseline === undefined ? null : input.baseline;
    entry.followups.push({metric:text(input.metric,'Metric'),unit:text(input.unit,'Unit'),baseline:baseline,observed:observed,
      difference:baseline===null?null:observed-baseline,observed_date:input.observed_date,note:text(input.note || '', 'Note'),
      verification:'user-entered, unverified',recorded_at_utc:new Date().toISOString()});
    return checkHistory(h);
  }
  function exportHistory(history) { return JSON.stringify(checkHistory(safeCopy(history)), null, 2); }
  function importHistory(raw) {
    if (typeof raw !== 'string' || new TextEncoder().encode(raw).length > HISTORY_LIMIT) throw new Error('Import must be JSON no larger than 256 KB.');
    let h; try { h=JSON.parse(raw); } catch (_) { throw new Error('Invalid JSON history.'); }
    h=checkHistory(safeCopy(h)); h.trust='imported, unverified'; return h;
  }
  const api = {revenueBridge, scenario, makeRecord, newHistory, addSnapshot, addFollowup, exportHistory, importHistory};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof document === 'undefined') return;
  root.BVDIE = api;
  document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('bv-form');
    if (!form || typeof DATA === 'undefined' || !DATA.decision || !DATA.decision.mom) return;
    const mom = DATA.decision.mom;
    const output = document.getElementById('bv-output'), error = document.getElementById('bv-error');
    const download = document.getElementById('bv-download');
    const saveHistory = document.getElementById('bv-save-history');
    let record = null;
    const fmt = n => '₹' + n.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    function line(label, value) {
      const row = document.createElement('p');
      const strong = document.createElement('strong'); strong.textContent = label + ': ';
      row.appendChild(strong); row.appendChild(document.createTextNode(value)); output.appendChild(row);
    }
    function invalidate() { record = null; download.disabled = true; saveHistory.disabled = true; output.replaceChildren(); error.textContent = ''; }
    form.addEventListener('input', invalidate);
    form.addEventListener('change', invalidate);
    form.addEventListener('submit', function (event) {
      event.preventDefault(); invalidate();
      try {
        record = makeRecord({previous: mom.revenue[0], current: mom.revenue[1], previousOrders: mom.orders[0],
          currentOrders: mom.orders[1], previousPeriod: mom.prev_label, currentPeriod: mom.label,
          incrementalOrders: document.getElementById('bv-orders').valueAsNumber,
          contributionPerOrder: document.getElementById('bv-contribution').valueAsNumber,
          campaignCost: document.getElementById('bv-cost').valueAsNumber,
          action: document.getElementById('bv-action').value, kpi: document.getElementById('bv-kpi').value,
          followUp: document.getElementById('bv-follow').value, status: document.getElementById('bv-status').value,
          observedNote: document.getElementById('bv-observed').value, productBridge: root.BVDIE_PVM || null});
        const b = record.evidence, s = record.scenarios;
        line('Revenue change (' + mom.prev_label + ' → ' + mom.label + ')', fmt(b.total_change));
        line('Order-volume component', fmt(b.volume_effect));
        line('Average-basket component', fmt(b.basket_effect));
        if (record.product_price_volume_mix) {
          const p = record.product_price_volume_mix, c = p.components;
          line('Product bridge — volume (common products)', fmt(c.volume_inr));
          line('Product bridge — mix (common products)', fmt(c.mix_inr));
          line('Product bridge — realized price (common products)', fmt(c.realized_price_inr));
          line('Product entry / exit', fmt(c.entry_inr) + ' / ' + fmt(c.exit_inr));
        }
        ['low','base','high'].forEach(name => line(name + ' modeled net', fmt(s[name].net_inr)));
        line('Break-even incremental orders', s.break_even_incremental_orders === null ? 'Not attainable with zero contribution and positive cost' : String(s.break_even_incremental_orders));
        download.disabled = false; saveHistory.disabled = false;
      } catch (err) { error.textContent = err.message; }
    });
    function downloadJson(value, filename) {
      const url = URL.createObjectURL(new Blob([value], {type:'application/json'}));
      const link = document.createElement('a'); link.href = url; link.download = filename;
      document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
    download.addEventListener('click', function () {
      if (record) downloadJson(JSON.stringify(record, null, 2), 'ecommerce_decision_record.json');
    });
    const storageKey = 'bvdie:ecommerce:decision_history:v1';
    const info = document.getElementById('bv-history-info'), historyError = document.getElementById('bv-history-error');
    const select = document.getElementById('bv-history-choice'), historyDownload = document.getElementById('bv-export-history');
    const followButton = document.getElementById('bv-follow-add'), followOutput = document.getElementById('bv-followup-output');
    let history = null;
    function drawHistory() {
      select.replaceChildren(); followOutput.replaceChildren();
      const entries = history ? history.entries : [];
      entries.forEach(e=>{ const opt=document.createElement('option'); opt.value=e.id; opt.textContent=(e.record.decision.action || 'Untitled').slice(0,80)+' · '+e.id.slice(0,8); select.appendChild(opt); });
      info.textContent = entries.length + ' snapshot(s); ' + (history ? history.trust : 'history unavailable') + '.';
      historyDownload.disabled = !entries.length; followButton.disabled = !entries.length;
      const current=entries.find(e=>e.id===select.value);
      if (current) current.followups.forEach(f=>{ const p=document.createElement('p'); p.textContent=f.metric + ': ' + f.observed + ' ' + f.unit + (f.difference===null?'':' (difference ' + f.difference + ')') + ' — user-entered, unverified; not causal.'; followOutput.appendChild(p); });
    }
    function store(h) { localStorage.setItem(storageKey, exportHistory(h)); history=h; historyError.textContent=''; drawHistory(); }
    try { const raw=localStorage.getItem(storageKey); history=raw ? importHistory(raw) : newHistory(); drawHistory(); }
    catch (_) { historyError.textContent='Local history could not be loaded. Import a valid file to replace it.'; }
    saveHistory.addEventListener('click', function () {
      try { if (!history) throw new Error('Import a valid history before saving.'); store(addSnapshot(history, record)); }
      catch (err) { historyError.textContent=err.message; }
    });
    historyDownload.addEventListener('click', function () { if (history) downloadJson(exportHistory(history), 'ecommerce_decision_history.json'); });
    document.getElementById('bv-import-history').addEventListener('click', async function () {
      try { const file=document.getElementById('bv-history-file').files[0];
        if (!file || file.size>HISTORY_LIMIT) throw new Error('Choose a JSON file no larger than 256 KB.');
        store(importHistory(await file.text())); info.textContent += ' Imported content is unverified.';
      } catch (err) { historyError.textContent=err.message; }
    });
    select.addEventListener('change', function () {
      const id=select.value; drawHistory(); select.value=id; followOutput.replaceChildren();
      const e=history.entries.find(x=>x.id===id);
      if (e) e.followups.forEach(f=>{const p=document.createElement('p');p.textContent=f.metric+': '+f.observed+' '+f.unit+(f.difference===null?'':' (difference '+f.difference+')')+' — user-entered, unverified; not causal.';followOutput.appendChild(p);});
    });
    document.getElementById('bv-followup-form').addEventListener('submit', function (event) {
      event.preventDefault();
      try {
        const base=document.getElementById('bv-follow-baseline').value;
        const obs=document.getElementById('bv-follow-observed').valueAsNumber;
        const selectedId = select.value;
        store(addFollowup(history, selectedId, {metric:document.getElementById('bv-follow-metric').value,
          unit:document.getElementById('bv-follow-unit').value, baseline:base===''?null:Number(base), observed:obs,
          observed_date:document.getElementById('bv-follow-date').value, note:document.getElementById('bv-follow-note').value}));
        select.value=selectedId; select.dispatchEvent(new Event('change'));
      } catch (err) { historyError.textContent=err.message; }
    });
  });
})(typeof globalThis !== 'undefined' ? globalThis : this);
