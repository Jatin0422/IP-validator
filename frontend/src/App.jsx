import { useState } from 'react';

const API = 'http://localhost:8000';
const tabs = ['Validate', 'Subnet'];

export default function App() {
  const [tab, setTab] = useState(tabs[0]);
  const [values, setValues] = useState({ addresses: '', ip: '', mask: '/24', compareIp: '', splitCount: '' });
  const [compareEnabled, setCompareEnabled] = useState(false);
  const [splitEnabled, setSplitEnabled] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const set = (key, value) => setValues(old => ({ ...old, [key]: value }));

  function changeTab(next) {
    setTab(next);
    setResult(null);
    setError('');
  }

  async function post(path, body) {
    const response = await fetch(`${API}/api/${path}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    });
    const data = await response.json();
    if (!response.ok) {
      const detail = Array.isArray(data.detail) ? data.detail[0]?.msg : data.detail;
      throw new Error(detail || data.error || 'Request failed');
    }
    return data;
  }

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    setResult(null);
    try {
      if (tab === 'Validate') {
        const addresses = values.addresses.split(/\r?\n/).map(address => address.trim()).filter(Boolean);
        if (addresses.length === 1) {
          setResult({ mode: 'single', data: await post('validate', { ip: addresses[0] }) });
        } else if (addresses.length > 1) {
          setResult({ mode: 'bulk', data: await post('validate-bulk', { list: addresses }) });
        } else {
          throw new Error('Enter at least one IP address.');
        }
      } else {
        const subnet = await post('subnet', { ip: values.ip, mask: values.mask });
        let comparison = null;
        let split = null;
        if (compareEnabled && values.compareIp.trim()) {
          comparison = await post('same-network', { ip1: values.ip, ip2: values.compareIp.trim(), mask: values.mask });
        }
        if (splitEnabled && values.splitCount) {
          split = await post('split-subnet', {
            network: `${subnet.network}/${subnet.prefix}`,
            n: Number(values.splitCount),
          });
        }
        setResult({ mode: 'subnet', subnet, comparison, split });
      }
    } catch (err) {
      setError(err.message || 'Could not connect to the API');
    } finally {
      setBusy(false);
    }
  }

  function copy(text) {
    navigator.clipboard?.writeText(String(text));
  }

  function copyControl(text, label = 'COPY') {
    return <button className="copy-button" type="button" onClick={() => copy(text)} aria-label={`Copy ${text}`}>{label}</button>;
  }

  function valueWithCopy(value) {
    return <span className="value-copy"><span className="mono-value">{String(value ?? '—')}</span>{copyControl(value)}</span>;
  }

  function bitRow(binary, prefix, label) {
    const bits = String(binary ?? '').replaceAll('.', '').split('');
    return <div className="bit-row"><span className="bit-row-label">{label}</span><div className="bit-groups">{Array.from({ length: Math.ceil(bits.length / 8) }, (_, group) => <span className="bit-group" key={group}>{bits.slice(group * 8, group * 8 + 8).map((bit, i) => {
      const position = group * 8 + i;
      return <span className={position < prefix ? 'bit-cell network-bit' : 'bit-cell host-bit'} key={position}>{bit}</span>;
    })}</span>)}</div></div>;
  }

  function validationDetail(data) {
    return <>
      <div className="validation-stamp"><strong className={data.valid ? 'valid-stamp' : 'invalid-stamp'}>{data.valid ? 'VALID' : 'INVALID'}</strong>{copyControl(data.valid ? 'VALID' : 'INVALID')}{data.error && valueWithCopy(data.error)}</div>
      {Object.entries(data).filter(([key]) => !['valid', 'error'].includes(key)).map(([key, value]) => <div className="spec-row" key={key}><span className="spec-label">{key.replaceAll('_', ' ')}</span><span className="spec-value">{typeof value === 'object' && value !== null ? valueWithCopy(Object.entries(value).map(([k, v]) => `${k}: ${v}`).join(' / ')) : valueWithCopy(value)}</span></div>)}
    </>;
  }

  function bulkDetail(data) {
    return <>
      <p className="bulk-summary"><strong>{data.valid_count} VALID</strong><span>/</span><strong className={data.invalid_count ? 'invalid-text' : ''}>{data.invalid_count} INVALID</strong></p>
      <div className="list-scroll"><table className="data-table"><thead><tr><th>STATUS</th><th>ADDRESS</th><th>REASON</th></tr></thead><tbody>{(data.results || []).map((item, index) => <tr key={`${item.ip}-${index}`}><td><span className={item.valid ? 'valid-mark' : 'invalid-mark'}>{item.valid ? 'OK' : 'NO'}</span></td><td><span className="value-copy"><span className="mono-value">{item.ip}</span>{copyControl(item.ip)}</span></td><td className={item.error ? 'failure-reason' : ''}>{item.error || '—'}</td></tr>)}</tbody></table></div>
    </>;
  }

  function subnetDetail(data) {
    const subnet = data.subnet;
    return <>
      {Object.entries(subnet).map(([key, value]) => <div className="spec-row" key={key}><span className="spec-label">{key.replaceAll('_', ' ')}</span><span className="spec-value">{valueWithCopy(value)}</span></div>)}
      <section className="bit-visualizer"><div className="section-kicker">BIT VISUALIZER <span>IPv4 · {subnet.prefix} bit prefix</span></div>{bitRow(subnet.ip_binary, subnet.prefix, 'IP ADDRESS')}<div className="bit-legend"><span><i className="legend-network" /> NETWORK</span><span><i className="legend-host" /> HOST</span></div><div className="mask-row"><span className="spec-label">MASK BINARY</span>{valueWithCopy(subnet.mask_binary)}</div></section>
      {data.comparison && <section className="optional-result"><div className="section-kicker">NETWORK COMPARISON</div><div className="verdict"><span className="spec-label">SAME NETWORK</span><strong>{data.comparison.same_network ? 'YES · SAME NETWORK' : 'NO · DIFFERENT NETWORK'}</strong></div>{bitRow(subnet.ip_binary, subnet.prefix, values.ip)}{bitRow(ipv4Binary(values.compareIp), subnet.prefix, values.compareIp)}<div className="bit-legend"><span><i className="legend-network" /> NETWORK</span><span><i className="legend-host" /> HOST</span></div></section>}
      {data.split && <section className="optional-result"><div className="list-heading"><span className="section-kicker">SPLIT SUBNETS</span>{copyControl((data.split.subnets || []).map(item => item.cidr).join('\n'), 'COPY ALL')}</div><div className="list-scroll"><table className="data-table"><thead><tr><th>NO.</th><th>NETWORK</th><th>PREFIX</th></tr></thead><tbody>{(data.split.subnets || []).map((item, index) => <tr key={item.cidr}><td>{String(index + 1).padStart(2, '0')}</td><td>{valueWithCopy(item.network)}</td><td>{valueWithCopy(`/${item.prefix}`)}</td></tr>)}</tbody></table></div></section>}
    </>;
  }

  function ipv4Binary(address) {
    const parts = address.split('.');
    if (parts.length !== 4 || parts.some(part => !/^\d+$/.test(part) || Number(part) > 255)) return '';
    return parts.map(part => Number(part).toString(2).padStart(8, '0')).join('.');
  }

  function fillExample(example) {
    if (tab === 'Validate') set('addresses', example.split('/')[0]);
    else if (example.includes('/')) {
      const [ip, mask] = example.split('/');
      set('ip', ip);
      set('mask', `/${mask}`);
    } else set('ip', example);
  }

  return <div className="app-shell">
    <aside className="rail"><a className="wordmark" href="#top" onClick={event => event.preventDefault()}>IPLens<span>NETWORK TOOLS</span></a><nav className="tool-nav" aria-label="Network tools">{tabs.map((item, index) => <button key={item} className={tab === item ? 'active' : ''} onClick={() => changeTab(item)}><span>{String(index + 1).padStart(2, '0')}</span>{item}</button>)}</nav><div className="rail-foot">COMPUTER NETWORKS<br />UTILITY SHEET / 01</div></aside>
    <main className="main-area" id="top"><div className="page-head"><span className="eyebrow">IP ADDRESSING / TOOLSET</span><span className="sheet-number">SPEC NO. 01—02</span></div>
      <section className="panel"><div className="panel-title"><span className="section-kicker">{String(tabs.indexOf(tab) + 1).padStart(2, '0')} / INPUT</span><h1>{tab}</h1></div>
        <form onSubmit={submit}>
          <div className="form-fields">
            {tab === 'Validate' ? <label className="field field-wide"><span className="micro-label">IP address · one per line for bulk validation</span><textarea required rows="4" value={values.addresses} onChange={e => set('addresses', e.target.value)} placeholder={'192.168.1.1\n2001:db8::1'} /></label> : <>
              <label className="field"><span className="micro-label">IPv4 address</span><input required value={values.ip} onChange={e => set('ip', e.target.value)} placeholder="192.168.1.1" /></label>
              <label className="field"><span className="micro-label">Prefix or subnet mask</span><input required value={values.mask} onChange={e => set('mask', e.target.value)} placeholder="/24 or 255.255.255.0" /></label>
              <label className="option-toggle"><input type="checkbox" checked={compareEnabled} onChange={e => setCompareEnabled(e.target.checked)} /><span>COMPARE WITH ANOTHER IP</span></label>
              {compareEnabled && <label className="field"><span className="micro-label">Other IPv4 address</span><input required value={values.compareIp} onChange={e => set('compareIp', e.target.value)} placeholder="192.168.1.20" /></label>}
              <label className="option-toggle"><input type="checkbox" checked={splitEnabled} onChange={e => setSplitEnabled(e.target.checked)} /><span>SPLIT INTO N SUBNETS</span></label>
              {splitEnabled && <label className="field"><span className="micro-label">Number of subnets</span><input type="number" min="1" step="1" required value={values.splitCount} onChange={e => set('splitCount', e.target.value)} placeholder="4" /></label>}
            </>}
          </div>
          <button className="submit" disabled={busy}>{busy ? 'PROCESSING...' : 'RUN CHECK'}</button>
        </form>
        {error && <p className="error" role="alert">{error}</p>}
        {result ? <section className="results" aria-live="polite"><div className="section-kicker result-heading">OUTPUT / RESULT</div>{result.mode === 'single' ? validationDetail(result.data) : result.mode === 'bulk' ? bulkDetail(result.data) : subnetDetail(result)}</section> : !error && <section className="empty-state"><span className="section-kicker">QUICK INPUT</span><div className="examples">{(tab === 'Validate' ? ['192.168.1.1', '::1', '10.0.0.0/8'] : ['192.168.1.1', '10.0.0.0/8']).map(example => <button type="button" key={example} onClick={() => fillExample(example)}>{example}</button>)}</div></section>}
      </section><footer className="page-foot"><span>IPLens / NETWORK UTILITIES</span><span>MANUAL INPUT · LOCAL API</span></footer>
    </main>
  </div>;
}
