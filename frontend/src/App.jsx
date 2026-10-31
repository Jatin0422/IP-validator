import { useState } from 'react';

const API = 'http://localhost:8000';
const tabs = ['Validate', 'Subnet Calculator', 'Same Network', 'Split Subnet', 'Bulk Validate', 'IP Range'];

export default function App() {
  const [tab, setTab] = useState(tabs[0]);
  const [values, setValues] = useState({ ip: '', mask: '/24', ip1: '', ip2: '', network: '192.168.1.0/24', n: '4', list: '', start: '', end: '' });
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const set = (key, value) => setValues(old => ({ ...old, [key]: value }));

  function changeTab(next) {
    setTab(next);
    setResult(null);
    setError('');
  }

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError('');
    setResult(null);
    let path;
    let body;
    switch (tab) {
      case 'Validate': path = 'validate'; body = { ip: values.ip }; break;
      case 'Subnet Calculator': path = 'subnet'; body = { ip: values.ip, mask: values.mask }; break;
      case 'Same Network': path = 'same-network'; body = { ip1: values.ip1, ip2: values.ip2, mask: values.mask }; break;
      case 'Split Subnet': path = 'split-subnet'; body = { network: values.network, n: Number(values.n) }; break;
      case 'Bulk Validate': path = 'validate-bulk'; body = { list: values.list.split(/[\s,;]+/).filter(Boolean) }; break;
      default: path = 'ip-range'; body = { start: values.start, end: values.end };
    }
    try {
      const response = await fetch(`${API}/api/${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      const data = await response.json();
      if (!response.ok) {
        const detail = Array.isArray(data.detail) ? data.detail[0]?.msg : data.detail;
        throw new Error(detail || data.error || 'Request failed');
      }
      setResult(data);
    } catch (err) {
      setError(err.message || 'Could not connect to the API');
    } finally {
      setBusy(false);
    }
  }

  const field = (label, key, placeholder, required = true, type = 'text') => <label key={key}>{label}<input type={type} min={key === 'n' ? 1 : undefined} step={key === 'n' ? 1 : undefined} required={required} value={values[key]} onChange={e => set(key, e.target.value)} placeholder={placeholder} /></label>;
  const fields = {
    Validate: [field('IP address', 'ip', '192.168.1.1 or 2001:db8::1')],
    'Subnet Calculator': [field('IPv4 address', 'ip', '192.168.1.1'), field('Prefix or subnet mask', 'mask', '/24 or 255.255.255.0')],
    'Same Network': [field('First IPv4 address', 'ip1', '192.168.1.10'), field('Second IPv4 address', 'ip2', '192.168.1.20'), field('Prefix or subnet mask', 'mask', '/24')],
    'Split Subnet': [field('Network with prefix', 'network', '192.168.1.0/24'), field('Number of subnets (power of 2)', 'n', '4', true, 'number')],
    'Bulk Validate': [<label key="list">IP addresses (one per line or comma separated)<textarea required rows="5" value={values.list} onChange={e => set('list', e.target.value)} placeholder={'192.168.1.1\n2001:db8::1'} /></label>],
    'IP Range': [field('Start IPv4 address', 'start', '192.168.1.1'), field('End IPv4 address', 'end', '192.168.1.10')],
  };

  function renderValue(value) {
    if (!Array.isArray(value)) return value && typeof value === 'object' ? JSON.stringify(value) : String(value ?? '—');
    if (value.length && value.every(item => item && typeof item === 'object')) {
      const columns = [...new Set(value.flatMap(item => Object.keys(item)))];
      return <table className="nested"><thead><tr>{columns.map(column => <th key={column}>{column.replaceAll('_', ' ')}</th>)}</tr></thead><tbody>{value.map((item, index) => <tr key={index}>{columns.map(column => <td key={column}>{renderValue(item[column])}</td>)}</tr>)}</tbody></table>;
    }
    return <ul className="value-list">{value.map((item, index) => <li key={index}>{renderValue(item)}</li>)}</ul>;
  }

  return <main className="shell">
    <header><div className="mark">IP</div><div><h1>IPLens</h1><p>Address validation &amp; subnet analysis</p></div></header>
    <nav aria-label="Tools">{tabs.map(item => <button key={item} className={tab === item ? 'active' : ''} onClick={() => changeTab(item)}>{item}</button>)}</nav>
    <section className="panel">
      <h2>{tab}</h2>
      <form onSubmit={submit}>{fields[tab]}<button className="submit" disabled={busy}>{busy ? 'Working...' : 'Run'}</button></form>
      {error && <p className="error" role="alert">{error}</p>}
      {result && <div className="results" aria-live="polite"><h3>Result</h3><table><tbody>{Object.entries(result).map(([key, value]) => <tr key={key}><th>{key.replaceAll('_', ' ')}</th><td>{renderValue(value)}</td></tr>)}</tbody></table></div>}
    </section>
    <footer>IPLens - Computer Networks</footer>
  </main>;
}
