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
    const status = input.status || 'proposed';
    if (!['proposed', 'approved', 'deferred'].includes(status)) throw new Error('Choose a supported decision status.');
    const note = text(input.observedNote || '', 'Follow-up note');
    return {schema_version: 1, project: 'ecommerce', created_at_utc: new Date().toISOString(),
      source: {dataset: 'data/processed/master_orders.csv', classification: 'synthetic',
        definition: 'Embedded dashboard monthly order counts and whole-rupee revenue totals; checked against the underlying dataset in tests.'},
      scope: {previous_period: text(input.previousPeriod || '', 'Previous period'),
        current_period: text(input.currentPeriod || '', 'Current period'),
        definition: 'Synthetic order-line snapshot; revenue uses Delivered + Processing orders and counts distinct order IDs. Embedded dashboard values are rounded to whole rupees.'},
      evidence: bridge,
      assumptions: {expected_incremental_orders: input.incrementalOrders,
        assumed_contribution_per_order_inr: input.contributionPerOrder, assumed_campaign_cost_inr: input.campaignCost},
      scenarios: scenarios,
      decision: {status: status, action: text(input.action || '', 'Action'),
        success_metric: text(input.kpi || '', 'KPI'), follow_up: text(input.followUp || '', 'Validation plan')},
      observed_outcome: note ? {source: 'user-entered, unverified', note: note} : null,
      limitations: 'Synthetic dataset. Order-volume versus average-basket decomposition is descriptive, not a price/quantity/mix or causal decomposition. Scenarios are modeled assumptions, not actual revenue, profit, savings or results.'};
  }
  const api = {revenueBridge, scenario, makeRecord};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (typeof document === 'undefined') return;
  root.BVDIE = api;
  document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('bv-form');
    if (!form || typeof DATA === 'undefined' || !DATA.decision || !DATA.decision.mom) return;
    const mom = DATA.decision.mom;
    const output = document.getElementById('bv-output'), error = document.getElementById('bv-error');
    const download = document.getElementById('bv-download');
    let record = null;
    const fmt = n => '₹' + n.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2});
    function line(label, value) {
      const row = document.createElement('p');
      const strong = document.createElement('strong'); strong.textContent = label + ': ';
      row.appendChild(strong); row.appendChild(document.createTextNode(value)); output.appendChild(row);
    }
    function invalidate() { record = null; download.disabled = true; output.replaceChildren(); error.textContent = ''; }
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
          observedNote: document.getElementById('bv-observed').value});
        const b = record.evidence, s = record.scenarios;
        line('Revenue change (' + mom.prev_label + ' → ' + mom.label + ')', fmt(b.total_change));
        line('Order-volume component', fmt(b.volume_effect));
        line('Average-basket component', fmt(b.basket_effect));
        ['low','base','high'].forEach(name => line(name + ' modeled net', fmt(s[name].net_inr)));
        line('Break-even incremental orders', s.break_even_incremental_orders === null ? 'Not attainable with zero contribution and positive cost' : String(s.break_even_incremental_orders));
        download.disabled = false;
      } catch (err) { error.textContent = err.message; }
    });
    download.addEventListener('click', function () {
      if (!record) return;
      const url = URL.createObjectURL(new Blob([JSON.stringify(record, null, 2)], {type:'application/json'}));
      const link = document.createElement('a'); link.href = url; link.download = 'ecommerce_decision_record.json';
      document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    });
  });
})(typeof globalThis !== 'undefined' ? globalThis : this);
