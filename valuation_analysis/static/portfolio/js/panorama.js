(() => {
  const API = 'http://localhost:8001/market';
  const groups = {
    brasil: ['ibovespa', 'small_caps', 'ifix', 'ewz'],
    americas: ['sp500', 'dow_jones', 'nasdaq', 'russell_2000', 'vix', 'sp_tsx'],
    europa: ['ftse_100', 'dax', 'cac_40', 'euro_stoxx_50', 'ibex_35', 'smi'],
    asia: ['nikkei_225', 'topix', 'hang_seng', 'shanghai', 'shenzhen', 'kospi', 'nifty_50', 'sensex', 'asx_200'],
    etfs: ['msci_world', 'msci_em', 'ftse_all_world', 'rare_earth'],
  };
  const names = {ibovespa:'Ibovespa', small_caps:'Small Caps', ifix:'IFIX', ewz:'MSCI Brazil (EWZ)',
    sp500:'S&P 500', dow_jones:'Dow Jones', nasdaq:'Nasdaq', russell_2000:'Russell 2000', vix:'VIX', sp_tsx:'S&P/TSX',
    ftse_100:'FTSE 100', dax:'DAX', cac_40:'CAC 40', euro_stoxx_50:'Euro Stoxx 50', ibex_35:'IBEX 35', smi:'SMI',
    nikkei_225:'Nikkei 225', topix:'TOPIX', hang_seng:'Hang Seng', shanghai:'Shanghai', shenzhen:'Shenzhen', kospi:'KOSPI',
    nifty_50:'Nifty 50', sensex:'Sensex', asx_200:'ASX 200', msci_world:'MSCI World', msci_em:'MSCI EM',
    ftse_all_world:'FTSE All-World', rare_earth:'Terras Raras (REMX)', ouro:'Ouro', prata:'Prata', petroleo_wti:'Petróleo WTI',
    petroleo_brent:'Petróleo Brent', cobre:'Cobre', ferro:'Minério de ferro', btc:'Bitcoin', bitcoin:'Bitcoin', eth:'Ethereum', ethereum:'Ethereum',
    treasury_10y:'Treasury 10 anos', treasury_5y:'Treasury 5 anos', sp500_fut:'S&P 500', nasdaq_fut:'Nasdaq', dow_jones_fut:'Dow Jones'};
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const numeric = value => value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value));
  const fmt = (value, digits=2) => numeric(value) ? Number(value).toLocaleString('pt-BR', {minimumFractionDigits:digits, maximumFractionDigits:digits}) : 'Indisponível';
  const empty = (cols=2) => `<tr><td colspan="${cols}" class="market-state">Dados indisponíveis. Tente atualizar.</td></tr>`;
  let region = 'brasil', indices = {}, loading = true;

  function renderIndices() {
    document.getElementById('market-indices').innerHTML = loading
      ? '<tr><td colspan="3" class="market-state">Consultando índices…</td></tr>'
      : groups[region].map(key => {
        const item = indices[key] || {};
        const change = numeric(item.percent_change) ? Number(item.percent_change) : null;
        const css = change > 0 ? 'text-success' : change < 0 ? 'text-danger' : '';
        return `<tr><td>${esc(names[key] || key)}</td><td>${fmt(item.price)}</td><td class="${css}">${change === null ? '—' : `${change > 0 ? '+' : ''}${fmt(change)}%`}</td></tr>`;
      }).join('');
  }
  async function get(endpoint) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(`${API}/${endpoint}`, {signal:controller.signal});
      if (!response.ok) throw new Error('Consulta indisponível');
      return await response.json();
    } finally { clearTimeout(timeout); }
  }
  function rows(data, id, unit='') {
    const entries = Object.entries(data || {});
    let available = 0;
    document.getElementById(id).innerHTML = entries.map(([key,item]) => {
      const value = item && typeof item === 'object' ? item.price : item;
      if (numeric(value)) available++;
      const suffix = item && typeof item === 'object' ? item.currency || unit : unit;
      return `<tr><td>${esc(names[key.toLowerCase()] || key.replace(/_/g,' '))}</td><td>${fmt(value)}${numeric(value) ? ` ${esc(suffix)}` : ''}</td></tr>`;
    }).join('') || empty();
    return available > 0;
  }
  function highlight(id,value,prefix='') {
    document.getElementById(id).textContent = numeric(value) ? prefix + fmt(value) : '—';
  }
  async function refresh() {
    const button = document.getElementById('refresh-market');
    button.disabled = true;
    loading = true;
    indices = {};
    renderIndices();
    document.getElementById('market-status').textContent = 'Consultando os mercados…';
    document.querySelectorAll('.market-highlight dd').forEach(el => el.textContent = '—');
    for (const id of ['currency','commodities','rates','futures','crypto']) {
      document.getElementById(`market-${id}`).innerHTML = '<tr><td colspan="2" class="market-state">Consultando…</td></tr>';
    }
    const jobs = [
      (async () => {
        try {
          const response = await get('indices/all');
          indices = response.data || {};
          highlight('highlight-ibov',indices.ibovespa?.price);
          highlight('highlight-sp500',indices.sp500?.price);
          return Object.values(indices).some(item => numeric(item?.price));
        } finally { loading = false; renderIndices(); }
      })(),
      ...[['commodities',''],['rates','%'],['futures','pts'],['crypto','USD']].map(async ([category,unit]) => {
        try {
          const response = await get(`${category}/all`);
          if (category === 'crypto') {
            const btc = response.data?.BTC ?? response.data?.btc ?? response.data?.bitcoin;
            highlight('highlight-btc',typeof btc === 'object' ? btc?.price : btc,'US$ ');
          }
          return rows(response.data, `market-${category}`, unit);
        } catch (error) {
          document.getElementById(`market-${category}`).innerHTML = empty();
          throw error;
        }
      }),
      (async () => {
        const keys = ['usd','eur','gbp','chf','dxy'];
        const results = await Promise.allSettled(keys.map(key => get(`currency/${key}`)));
        document.getElementById('market-currency').innerHTML = results.map((res,i) => {
          const value = res.status === 'fulfilled' ? res.value.price : null;
          if (i === 0) highlight('highlight-usd',value,'R$ ');
          return `<tr><td>${keys[i].toUpperCase()}</td><td>${numeric(value) && i < 4 ? 'R$ ' : ''}${fmt(value,3)}${i === 4 && numeric(value) ? ' pts' : ''}</td></tr>`;
        }).join('');
        return results.every(res => res.status === 'fulfilled' && numeric(res.value.price));
      })(),
    ];
    const results = await Promise.allSettled(jobs);
    const complete = results.every(result => result.status === 'fulfilled' && result.value);
    const hour = new Date().toLocaleTimeString('pt-BR');
    document.getElementById('market-status').textContent = `Última consulta às ${hour} · ${complete ? 'Consulta concluída' : 'Alguns dados estão indisponíveis'}`;
    button.disabled = false;
  }
  document.querySelectorAll('[data-region]').forEach(button => button.addEventListener('click', () => {
    region = button.dataset.region;
    document.querySelectorAll('[data-region]').forEach(tab => tab.setAttribute('aria-pressed',String(tab === button)));
    renderIndices();
  }));
  document.getElementById('refresh-market').addEventListener('click', refresh);
  refresh();
})();
