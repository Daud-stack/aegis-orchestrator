import { useState, useEffect, useRef } from 'react';
import { ShieldAlert, Activity, MapPin, CheckCircle, XCircle, Loader2, ArrowRight } from 'lucide-react';
import './App.css';

function App() {
  const [eventLocation, setEventLocation] = useState('Sector 4');
  const [eventType, setEventType] = useState('Flood');
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [vibeDiff, setVibeDiff] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, running, approval_needed, approved, rejected
  const logsEndRef = useRef(null);

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [logs]);

  const handleStart = async () => {
    setIsRunning(true);
    setLogs([]);
    setVibeDiff(null);
    setStatus('running');

    try {
      const response = await fetch('http://localhost:8000/api/report-disaster', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_type: eventType, location: eventLocation })
      });
      const data = await response.json();
      
      // Simulate real-time logs streaming
      for (let log of data.plan.logs) {
        await new Promise(r => setTimeout(r, 600)); // Delay for visual effect
        setLogs(prev => [...prev, log]);
      }
      
      setVibeDiff(data.plan.vibe_diff);
      setStatus('approval_needed');
    } catch (error) {
      console.error("Error connecting to backend", error);
      setStatus('idle');
      setIsRunning(false);
    }
  };

  const handleApprove = () => {
    setStatus('approved');
    setLogs(prev => [...prev, { source: "System", message: "Vibe Diff Approved via Cryptographic MFA. Resources Dispatched." }]);
  };

  const handleReject = () => {
    setStatus('rejected');
    setLogs(prev => [...prev, { source: "System", message: "Vibe Diff Rejected. Aborting dispatch." }]);
  };

  return (
    <div className="app-container">
      <header className="header">
        <div className="logo">
          <Activity className="icon pulse" />
          <h1>Orchestrator<span className="accent">ADK</span></h1>
        </div>
        <div className="status-badge">
          <div className={`status-dot ${status}`}></div>
          {status === 'idle' ? 'System Ready' : status === 'running' ? 'Agent Active' : status === 'approval_needed' ? 'MFA Required' : 'Completed'}
        </div>
      </header>

      <main className="main-grid">
        <div className="panel control-panel glass">
          <h2><MapPin className="inline-icon"/> Disaster Input</h2>
          <div className="input-group">
            <label>Event Type</label>
            <select value={eventType} onChange={e => setEventType(e.target.value)} disabled={isRunning && status !== 'approved' && status !== 'rejected'}>
              <option>Flood</option>
              <option>Earthquake</option>
              <option>Wildfire</option>
            </select>
          </div>
          <div className="input-group">
            <label>Location</label>
            <select value={eventLocation} onChange={e => setEventLocation(e.target.value)} disabled={isRunning && status !== 'approved' && status !== 'rejected'}>
              <option>Sector 4</option>
              <option>Downtown</option>
              <option>North Ridge</option>
            </select>
          </div>
          <button 
            className={`btn-primary ${isRunning && status !== 'approved' && status !== 'rejected' ? 'disabled' : ''}`}
            onClick={handleStart}
            disabled={isRunning && status !== 'approved' && status !== 'rejected'}
          >
            {status === 'running' ? <><Loader2 className="spin inline-icon" /> Processing...</> : 'Trigger Response Orchestrator'}
          </button>
        </div>

        <div className="panel map-panel glass">
           <h2>Live Radar</h2>
           <div className="map-placeholder">
              <div className="radar-sweep"></div>
              {status !== 'idle' && <div className="ping" style={{top: '40%', left: '50%'}}></div>}
              <div className="map-overlay">
                 {status === 'idle' ? 'Awaiting Input...' : `Monitoring ${eventLocation}`}
              </div>
           </div>
        </div>

        <div className="panel logs-panel glass">
          <h2>A2A Communication Logs</h2>
          <div className="logs-container">
            {logs.length === 0 && <p className="text-muted">Waiting for agent activity...</p>}
            {logs.map((log, idx) => (
              <div key={idx} className={`log-entry ${log.source.includes('Orchestrator') ? 'orchestrator' : 'domain-agent'}`}>
                <span className="log-source">[{log.source}]</span>
                <span className="log-message">{log.message}</span>
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        </div>
      </main>

      {status === 'approval_needed' && vibeDiff && (
        <div className="modal-backdrop">
          <div className="modal glass glow">
            <h2><ShieldAlert className="inline-icon text-warning" /> Vibe Diff Approval Required</h2>
            <p className="text-muted">The Orchestrator has proposed the following action plan. Cryptographic MFA is required to authorize.</p>
            
            <div className="diff-card">
               <h3>Context Retrieved (via MCP)</h3>
               <p><strong>Weather:</strong> {vibeDiff.context.weather}</p>
               <p><strong>Traffic:</strong> {vibeDiff.context.traffic}</p>
            </div>

            <div className="diff-card">
               <h3>Proposed Actions</h3>
               <ul>
                 {vibeDiff.actions.map((act, i) => <li key={i}><ArrowRight className="inline-icon small"/> {act}</li>)}
               </ul>
            </div>

            <div className="modal-actions">
              <button className="btn-reject" onClick={handleReject}><XCircle className="inline-icon"/> Reject</button>
              <button className="btn-approve" onClick={handleApprove}><CheckCircle className="inline-icon"/> Approve (MFA)</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
