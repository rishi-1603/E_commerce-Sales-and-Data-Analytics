"""HTML/JS templates for the Pricing Lab + Win-Back dashboard pages.

Kept in a separate module so scripts/inject_pricing_dashboard.py stays readable.
All numbers are injected at runtime from DATA.pricing — nothing is typed by hand.
"""

NAV_START = "<!-- PRICING_NAV_START -->"
NAV_END = "<!-- PRICING_NAV_END -->"
PAGE_START = "<!-- PRICING_PAGES_START -->"
PAGE_END = "<!-- PRICING_PAGES_END -->"
DATA_START = "/* PRICING_DATA_START */"
DATA_END = "/* PRICING_DATA_END */"
JS_START = "// PRICING_JS_START"
JS_END = "// PRICING_JS_END"

NAV = """<!-- PRICING_NAV_START -->
    <div class="nav-item" role="button" tabindex="0" onclick="nav('pricing',this)">
      <svg class="icon" viewBox="0 0 16 16" fill="currentColor"><path d="M7.5 1.5a.5.5 0 00-1 0v.6a3.5 3.5 0 00-2.6 3.35c0 1.6 1.02 2.6 2.66 2.98l.94.22c.7.16 1.1.55 1.1 1.15 0 .72-.66 1.2-1.6 1.2-.86 0-1.5-.36-1.75-.95a.5.5 0 00-.92.38c.36.88 1.18 1.42 2.17 1.54v.53a.5.5 0 001 0v-.55a3.4 3.4 0 002.55-3.28c0-1.6-1.05-2.55-2.62-2.92l-.94-.22c-.75-.18-1.14-.55-1.14-1.14 0-.68.6-1.16 1.5-1.16.78 0 1.35.3 1.62.82a.5.5 0 00.88-.47A2.9 2.9 0 008.5 2.2v-.7z"/></svg>
      Pricing Lab
    </div>
    <div class="nav-item" role="button" tabindex="0" onclick="nav('winback',this)">
      <svg class="icon" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1.5a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM0 8a8 8 0 1116 0A8 8 0 010 8zm7.25-3.5a.75.75 0 011.5 0v3.19l2.03 1.17a.75.75 0 11-.75 1.3L7.75 8.7A.75.75 0 017.25 8V4.5z"/></svg>
      Win-Back Economics
    </div>
    <!-- PRICING_NAV_END -->"""

PAGES = """<!-- PRICING_PAGES_START -->
    <div class="page" id="page-pricing">
      <div class="band" style="margin-bottom:12px">
        <strong>Is the discount ladder buying us anything?</strong>
        In this dataset, no. Volume response to discount depth is not statistically
        significant (Kruskal-Wallis p=__P_KW__), while every rung costs margin. The
        break-even table shows what would have to be true for each depth to pay for itself.
      </div>

      <div class="kpi-grid">
        <div class="kpi-card"><div class="kpi-accent" style="background:#f85149"></div><div class="kpi-label">Volume response detected</div><div class="kpi-value" style="color:var(--red)">__P_VOL__</div><div class="kpi-delta neu">p = __P_KW__</div></div>
        <div class="kpi-card"><div class="kpi-accent" style="background:#d29922"></div><div class="kpi-label">Break-even lift at 20% off</div><div class="kpi-value" style="color:var(--amber)">+__P_BE20__%</div><div class="kpi-delta neu">volume needed</div></div>
        <div class="kpi-card"><div class="kpi-accent" style="background:#3fb950"></div><div class="kpi-label">Margin recovered (10% cap)</div><div class="kpi-value" style="color:var(--green)">__P_MREC__</div><div class="kpi-delta up">__P_MPCT__% of total margin</div></div>
        <div class="kpi-card"><div class="kpi-accent" style="background:#388bfd"></div><div class="kpi-label">Lines affected by cap</div><div class="kpi-value" style="color:var(--blue)">__P_LINES__</div><div class="kpi-delta neu">above 10% discount</div></div>
      </div>

      <div class="card" style="margin-bottom:12px">
        <div class="card-header">
          <div><div class="card-title">Margin Erosion vs Break-Even Requirement</div><div class="card-sub">Margin as a share of list price falls with every rung; the line is the volume lift each rung needs to hold total margin flat</div></div>
          <div class="legend">
            <div class="leg-item"><div class="leg-dot" style="background:#388bfd"></div>Margin % of list</div>
            <div class="leg-item"><div class="leg-dot" style="background:#d29922"></div>Break-even lift</div>
          </div>
        </div>
        <div class="chart-wrap" style="height:260px">
          <canvas id="ch_pricing_margin" role="img" aria-label="Margin erosion and break-even lift by discount depth"></canvas>
        </div>
      </div>

      <div class="card" style="margin-bottom:12px">
        <div class="card-header"><div><div class="card-title">Discount Lab — scenario simulator</div><div class="card-sub">Set a discount depth and an assumed volume lift. The simulator prices the scenario against the break-even requirement. The lift is an assumption — this dataset cannot identify it.</div></div></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:4px 0 12px">
          <div>
            <label for="lab_depth" style="display:block;font-size:12px;color:var(--muted);margin-bottom:6px">Discount depth: <strong id="lab_depth_v" style="color:var(--text)">10%</strong></label>
            <input id="lab_depth" type="range" min="0" max="20" step="5" value="10" style="width:100%" oninput="runDiscountLab()">
          </div>
          <div>
            <label for="lab_lift" style="display:block;font-size:12px;color:var(--muted);margin-bottom:6px">Assumed volume lift: <strong id="lab_lift_v" style="color:var(--text)">+0%</strong></label>
            <input id="lab_lift" type="range" min="-20" max="80" step="5" value="0" style="width:100%" oninput="runDiscountLab()">
          </div>
        </div>
        <div class="kpi-grid" id="lab_out" style="margin-bottom:8px"></div>
        <div class="band" id="lab_verdict"></div>
      </div>

      <div class="card">
        <div class="card-header"><div><div class="card-title">Break-Even Table</div><div class="card-sub">Volume lift required at each depth to hold total margin flat, and the share of line items at that depth</div></div></div>
        <div class="tbl-wrap">
          <table>
            <thead><tr><th>Discount</th><th class="num-right">Margin rate</th><th class="num-right">Margin % of list</th><th class="num-right">Break-even volume lift</th><th class="num-right">Share of line items</th></tr></thead>
            <tbody id="pricing_tbody"></tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="page" id="page-winback">
      <div class="band" style="margin-bottom:12px">
        <strong>Who is worth saving, and what does it return?</strong>
        Expected-value economics on the __W_CUST__ cooling-off customers. Every figure is an
        <em>expectation</em> under the stated cost model — no campaign has been run.
      </div>

      <div class="kpi-grid">
        <div class="kpi-card"><div class="kpi-accent" style="background:#388bfd"></div><div class="kpi-label">Cooling-off customers</div><div class="kpi-value" style="color:var(--blue)">__W_CUST__</div><div class="kpi-delta neu">__W_HIST__ historical spend</div></div>
        <div class="kpi-card"><div class="kpi-accent" style="background:#3fb950"></div><div class="kpi-label">Expected profit per contact</div><div class="kpi-value" style="color:var(--green)">__W_EVPC__</div><div class="kpi-delta up">at __W_RATE__% recovery</div></div>
        <div class="kpi-card"><div class="kpi-accent" style="background:#3fb950"></div><div class="kpi-label">Campaign expected profit</div><div class="kpi-value" style="color:var(--green)">__W_EVTOT__</div><div class="kpi-delta neu">contact all __W_CUST__</div></div>
        <div class="kpi-card"><div class="kpi-accent" style="background:#d29922"></div><div class="kpi-label">Break-even churn probability</div><div class="kpi-value" style="color:var(--amber)">__W_BEP__%</div><div class="kpi-delta neu">equals churn model Bayes threshold</div></div>
      </div>

      <div class="card" style="margin-bottom:12px">
        <div class="card-header"><div><div class="card-title">Sensitivity — how wrong can the assumptions be?</div><div class="card-sub">Expected profit per contact across recovery rate and offer cost. The recovery rate is the single most sensitive assumption, which is why it is shown as a range rather than a point</div></div></div>
        <div class="chart-wrap" style="height:260px">
          <canvas id="ch_winback_sens" role="img" aria-label="Win-back expected profit sensitivity by recovery rate and offer cost"></canvas>
        </div>
      </div>

      <div class="card" style="margin-bottom:12px">
        <div class="card-header"><div><div class="card-title">Budget Worklist</div><div class="card-sub">Ranked by expected value (p × r × V − C), not by churn probability alone — a likely churner who spends little is not worth a call</div></div></div>
        <label for="wb_budget" style="display:block;font-size:12px;color:var(--muted);margin-bottom:6px">Monthly budget: <strong id="wb_budget_v" style="color:var(--text)">Rs 25,000</strong></label>
        <input id="wb_budget" type="range" min="0" max="112000" step="2500" value="25000" style="width:100%" oninput="runBudgetWorklist()">
        <div class="kpi-grid" id="wb_out" style="margin-top:12px"></div>
      </div>

      <div class="card">
        <div class="card-header"><div><div class="card-title">Tiered Scenarios</div><div class="card-sub">Expected profit in rupees — including the do-nothing baseline</div></div></div>
        <div class="tbl-wrap">
          <table>
            <thead><tr><th>Scenario</th><th class="num-right">Audience</th><th class="num-right">Expected profit</th></tr></thead>
            <tbody id="winback_tbody"></tbody>
          </table>
        </div>
      </div>
    </div>
    <!-- PRICING_PAGES_END -->"""

JS = r"""// PRICING_JS_START
function fmtINR(x){
  const a = Math.abs(x);
  if (a >= 1e7) return 'Rs ' + (x/1e7).toFixed(2) + ' Cr';
  if (a >= 1e5) return 'Rs ' + (x/1e5).toFixed(2) + ' L';
  return 'Rs ' + Math.round(x).toLocaleString('en-IN');
}

function buildPricingMargin(){
  const el = document.getElementById('ch_pricing_margin');
  if (!el || !DATA.pricing) return;
  const D = DATA.pricing.discount;
  new Chart(el, {
    type:'bar',
    data:{
      labels: D.depths.map(d => Math.round(d*100) + '%'),
      datasets:[
        { label:'Margin % of list', data:D.margin_pct_of_list.map(v=>+(v*100).toFixed(1)),
          backgroundColor:'rgba(56,139,253,0.55)', borderColor:'#388bfd', borderWidth:1,
          yAxisID:'y', order:2 },
        { label:'Break-even lift (%)', data:D.break_even_lift.map(v=>+(v*100).toFixed(1)),
          type:'line', borderColor:'#d29922', backgroundColor:'transparent',
          borderWidth:2, pointBackgroundColor:'#d29922', tension:0.25, yAxisID:'y1', order:1 }
      ]
    },
    options:{ responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{display:false},
        tooltip:{ callbacks:{ label:c => c.dataset.label + ': ' + c.parsed.y } } },
      scales:{
        y:{ beginAtZero:true, max:60, ticks:{ color:MUT }, grid:GRD,
            title:{display:true,text:'Margin % of list',color:MUT} },
        y1:{ position:'right', beginAtZero:true, ticks:{ color:'#d29922' }, grid:{display:false},
             title:{display:true,text:'Volume lift needed (%)',color:'#d29922'} },
        x:{ ticks:{ color:MUT }, grid:{display:false} }
      }
    }
  });
}

function buildPricingTable(){
  const tb = document.getElementById('pricing_tbody');
  if (!tb || !DATA.pricing) return;
  const D = DATA.pricing.discount;
  tb.innerHTML = D.depths.map((d,i) => '<tr>' +
    '<td>' + Math.round(d*100) + '%</td>' +
    '<td class="num-right">' + (D.margin_rate[i]*100).toFixed(1) + '%</td>' +
    '<td class="num-right">' + (D.margin_pct_of_list[i]*100).toFixed(1) + '%</td>' +
    '<td class="num-right">' + (d === 0 ? '—' : '+' + (D.break_even_lift[i]*100).toFixed(1) + '%') + '</td>' +
    '<td class="num-right">' + (D.share_of_items[i]*100).toFixed(1) + '%</td>' +
  '</tr>').join('');
}

function runDiscountLab(){
  if (!DATA.pricing) return;
  const D = DATA.pricing.discount;
  const depth = +(document.getElementById('lab_depth').value) / 100;
  const lift  = +(document.getElementById('lab_lift').value) / 100;
  document.getElementById('lab_depth_v').textContent = Math.round(depth*100) + '%';
  document.getElementById('lab_lift_v').textContent  = (lift>=0?'+':'') + Math.round(lift*100) + '%';

  const dep = D.depths, mpl = D.margin_pct_of_list, bel = D.break_even_lift;
  let lo = 0, hi = dep.length - 1;
  for (let i = 0; i < dep.length - 1; i++) {
    if (depth >= dep[i] && depth <= dep[i+1]) { lo = i; hi = i+1; }
  }
  const w = (depth - dep[lo]) / ((dep[hi] - dep[lo]) || 1);
  const margin = mpl[lo] + (mpl[hi] - mpl[lo]) * w;
  const be = bel[lo] + (bel[hi] - bel[lo]) * w;
  const base = mpl[0];

  const marginChange = ((margin / base) * (1 + lift)) - 1;
  const revenueChange = ((1 - depth) * (1 + lift)) - 1;
  const beats = lift >= be;
  const up = v => v >= 0 ? 'var(--green)' : 'var(--red)';

  document.getElementById('lab_out').innerHTML =
    '<div class="kpi-card"><div class="kpi-accent" style="background:#388bfd"></div>' +
      '<div class="kpi-label">Margin vs no discount</div>' +
      '<div class="kpi-value" style="color:' + up(marginChange) + '">' + (marginChange*100).toFixed(1) + '%</div>' +
      '<div class="kpi-delta neu">volume held at assumption</div></div>' +
    '<div class="kpi-card"><div class="kpi-accent" style="background:#bc8cff"></div>' +
      '<div class="kpi-label">Revenue vs no discount</div>' +
      '<div class="kpi-value" style="color:' + up(revenueChange) + '">' + (revenueChange*100).toFixed(1) + '%</div>' +
      '<div class="kpi-delta neu">price x volume</div></div>' +
    '<div class="kpi-card"><div class="kpi-accent" style="background:#d29922"></div>' +
      '<div class="kpi-label">Break-even lift needed</div>' +
      '<div class="kpi-value" style="color:var(--amber)">+' + (be*100).toFixed(1) + '%</div>' +
      '<div class="kpi-delta neu">at this depth</div></div>' +
    '<div class="kpi-card"><div class="kpi-accent" style="background:' + (beats?'#3fb950':'#f85149') + '"></div>' +
      '<div class="kpi-label">Verdict</div>' +
      '<div class="kpi-value" style="color:' + (beats?'var(--green)':'var(--red)') + ';font-size:17px">' +
        (beats ? 'Clears break-even' : 'Below break-even') + '</div>' +
      '<div class="kpi-delta neu">assumption vs requirement</div></div>';

  document.getElementById('lab_verdict').innerHTML = beats
    ? '<strong>Clears the bar.</strong> At a ' + Math.round(depth*100) + '% discount the assumed +' +
      Math.round(lift*100) + '% volume lift exceeds the ' + (be*100).toFixed(1) +
      '% required to hold margin flat. <em>But note:</em> the measured response in this dataset is not ' +
      'statistically significant (p=' + D.kruskal_p + '), so this lift is an assumption you are asserting, not a finding the data supports.'
    : '<strong>Does not clear the bar.</strong> A ' + Math.round(depth*100) + '% discount would need +' +
      (be*100).toFixed(1) + '% volume just to hold margin flat; you assumed +' + Math.round(lift*100) +
      '%. This scenario destroys margin relative to not discounting.';
}

function buildWinbackSens(){
  const el = document.getElementById('ch_winback_sens');
  if (!el || !DATA.pricing) return;
  const S = DATA.pricing.winback.sensitivity;
  const costs = [...new Set(S.map(s => s.c))].sort((a,b)=>a-b);
  const rates = [...new Set(S.map(s => s.r))].sort((a,b)=>a-b);
  const palette = ['#f85149','#d29922','#3fb950','#388bfd'];
  new Chart(el, {
    type:'bar',
    data:{
      labels: rates.map(r => Math.round(r*100) + '%'),
      datasets: costs.map((c,i) => ({
        label: 'Rs ' + c + '/contact',
        data: rates.map(r => {
          const row = S.find(s => s.r === r && s.c === c);
          return row ? +row.profit.toFixed(0) : 0;
        }),
        backgroundColor: palette[i % palette.length] + 'aa',
        borderColor: palette[i % palette.length], borderWidth:1
      }))
    },
    options:{ responsive:true, maintainAspectRatio:false,
      plugins:{ legend:{ labels:{ color:MUT, boxWidth:12 }, position:'bottom' },
        tooltip:{ callbacks:{ label:c => c.dataset.label + ': ' + fmtINR(c.parsed.y) + ' per contact' } } },
      scales:{
        y:{ ticks:{ color:MUT }, grid:GRD,
            title:{display:true,text:'Expected profit per contact',color:MUT} },
        x:{ ticks:{ color:MUT }, grid:{display:false},
            title:{display:true,text:'Recovery rate assumption',color:MUT} }
      }
    }
  });
}

function buildWinbackTable(){
  const tb = document.getElementById('winback_tbody');
  if (!tb || !DATA.pricing) return;
  tb.innerHTML = DATA.pricing.winback.tiers.map(t => '<tr>' +
    '<td>' + t.label + '</td>' +
    '<td class="num-right">' + t.audience + '</td>' +
    '<td class="num-right">' + fmtINR(t.profit) + '</td>' +
  '</tr>').join('');
}

function runBudgetWorklist(){
  if (!DATA.pricing) return;
  const W = DATA.pricing.winback;
  const budget = +(document.getElementById('wb_budget').value);
  document.getElementById('wb_budget_v').textContent = fmtINR(budget);
  const calls = Math.floor(budget / W.contact_cost);
  const eligible = W.worklist.eligible_customers;
  const selected = Math.min(calls, eligible);
  const profit = selected * W.ev_per_contact;
  document.getElementById('wb_out').innerHTML =
    '<div class="kpi-card"><div class="kpi-accent" style="background:#388bfd"></div>' +
      '<div class="kpi-label">Calls affordable</div>' +
      '<div class="kpi-value" style="color:var(--blue)">' + calls + '</div>' +
      '<div class="kpi-delta neu">at ' + fmtINR(W.contact_cost) + ' each</div></div>' +
    '<div class="kpi-card"><div class="kpi-accent" style="background:#bc8cff"></div>' +
      '<div class="kpi-label">Customers contacted</div>' +
      '<div class="kpi-value" style="color:var(--purple)">' + selected + '</div>' +
      '<div class="kpi-delta neu">' + eligible + ' eligible</div></div>' +
    '<div class="kpi-card"><div class="kpi-accent" style="background:#3fb950"></div>' +
      '<div class="kpi-label">Expected profit</div>' +
      '<div class="kpi-value" style="color:var(--green)">' + fmtINR(profit) + '</div>' +
      '<div class="kpi-delta up">' + fmtINR(W.ev_per_contact) + ' per contact</div></div>' +
    '<div class="kpi-card"><div class="kpi-accent" style="background:#d29922"></div>' +
      '<div class="kpi-label">Return per unit spent</div>' +
      '<div class="kpi-value" style="color:var(--amber)">' + (budget > 0 ? (profit/budget).toFixed(2) + 'x' : '—') + '</div>' +
      '<div class="kpi-delta neu">expected profit / budget</div></div>';
}

function buildPricing(){
  buildPricingMargin();
  buildPricingTable();
  buildWinbackSens();
  buildWinbackTable();
  runDiscountLab();
  runBudgetWorklist();
}
// PRICING_JS_END"""
