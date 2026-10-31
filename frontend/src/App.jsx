import { useState } from 'react';

const API = 'http://localhost:8000';

export default function App() {
  const [tab, setTab] = useState('Validate');
  const [ip, setIp] = useState('');
  const [mask, setMask] = useState('/24');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

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
    try {
      const response = await fetch(`${API}/api/${tab === 'Validate' ? 'validate' : 'subnet'}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(tab === 'Validate' ? { ip } : { ip, mask }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || data.error || 'Request failed');
      setResult(data);
    } catch (err) {
      setError(err.message || 'Could not connect to the API');
    } finally {
      setBusy(false);
    }
  }

  return <main className="shell">
    <header><div className="mark">IP</div><div><h1>IPLens</h1><p>Address validation &amp; subnet analysis</p></div></header>
    <nav aria-label="Tools">
      {['Validate', 'Subnet Calculator'].map(item => <button key={item} className={tab === item ? 'active' : ''} onClick={() => changeTab(item)}>{item}</button>)}
    </nav>
    <section className="panel">
      <h2>{tab === 'Validate' ? 'Validate an IP address' : 'Calculate an IPv4 subnet'}</h2>
      <form onSubmit={submit}>
        <label>IP address<input required value={ip} onChange={e => setIp(e.target.value)} placeholder={tab === 'Validate' ? '192.168.1.1 or 2001:db8::1' : '192.168.1.1'} /></label>
        {tab !== 'Validate' && <label>Prefix or subnet mask<input required value={mask} onChange={e => setMask(e.target.value)} placeholder="/24 or 255.255.255.0" /></label>}
        <button className="submit" disabled={busy}>{busy ? 'Working…' : tab === 'Validate' ? 'Validate address' : 'Calculate subnet'}</button>
      </form>
      {error && <p className="error" role="alert">{error}</p>}
      {result && <div className="results" aria-live="polite"><h3>Result</h3><table><tbody>{Object.entries(result).map(([key, value]) => <tr key={key}><th>{key.replaceAll('_', ' ')}</th><td>{typeof value === 'object' && value !== null ? Object.entries(value).map(([k, v]) => `${k}: ${v}`).join(' · ') : String(value ?? '—')}</td></tr>)}</tbody></table></div>}
    </section>
    <footer>IPLens · Computer Networks</footer>
  </main>;
}
