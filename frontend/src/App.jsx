import { useState, useEffect, useRef } from 'react';
import { ShieldAlert, Activity, MapPin, CheckCircle, XCircle, Loader2, ArrowRight } from 'lucide-react';
import { MapContainer, TileLayer, CircleMarker, Tooltip, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';

// Fix Leaflet's default marker icon path issue with bundlers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});



// Coordinate lookup for preset locations
const LOCATION_COORDS = {
  // US Locations
  'Sector 4':    { lat: 34.0522, lng: -118.2437, label: 'Los Angeles, CA' },
  'Downtown':    { lat: 40.7128, lng: -74.0060,  label: 'New York City, NY' },
  'North Ridge': { lat: 34.2364, lng: -118.5317, label: 'Northridge, CA' },
  // Zimbabwe
  'Harare':      { lat: -17.8292, lng: 31.0522,  label: 'Harare, Zimbabwe' },
  'Bulawayo':    { lat: -20.1325, lng: 28.6266,  label: 'Bulawayo, Zimbabwe' },
  'Chimanimani': { lat: -19.7994, lng: 32.8697,  label: 'Chimanimani, Zimbabwe' },
  'Mutare':      { lat: -18.9707, lng: 32.6709,  label: 'Mutare, Zimbabwe' },
  // Mozambique
  'Beira':       { lat: -19.8436, lng: 34.8389,  label: 'Beira, Mozambique' },
};

const DEFAULT_CENTER = [39.8283, -98.5795]; // Center of US
const DEFAULT_ZOOM = 4;
const INCIDENT_ZOOM = 12;

// Inner component that controls map fly-to behavior
function MapController({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.flyTo(center, zoom, { duration: 2 });
    }
  }, [center, zoom, map]);
  return null;
}

function App() {
  const [eventLocation, setEventLocation] = useState('Sector 4');
  const [eventType, setEventType] = useState('Flood');
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [vibeDiff, setVibeDiff] = useState(null);
  const [status, setStatus] = useState('idle');
  const [mapCenter, setMapCenter] = useState(DEFAULT_CENTER);
  const [mapZoom, setMapZoom] = useState(DEFAULT_ZOOM);
  const [incidentCoords, setIncidentCoords] = useState(null);
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
    setIncidentCoords(null);
    setStatus('running');

    // Immediately fly to the approximate location from our lookup
    const presetCoords = LOCATION_COORDS[eventLocation];
    if (presetCoords) {
      setMapCenter([presetCoords.lat, presetCoords.lng]);
      setMapZoom(INCIDENT_ZOOM);
    }

    try {
      const response = await fetch('http://localhost:8000/api/report-disaster', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_type: eventType, location: eventLocation })
      });
      const data = await response.json();
      
      // Use backend-geocoded coordinates if available, otherwise use preset
      const coords = data.plan.vibe_diff?.coordinates;
      if (coords && coords.lat !== 0 && coords.lng !== 0) {
        setMapCenter([coords.lat, coords.lng]);
        setIncidentCoords([coords.lat, coords.lng]);
      } else if (presetCoords) {
        setIncidentCoords([presetCoords.lat, presetCoords.lng]);
      }

      // Simulate real-time log streaming
      for (let log of data.plan.logs) {
        await new Promise(r => setTimeout(r, 600));
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

  const handleReset = () => {
    setIsRunning(false);
    setStatus('idle');
    setLogs([]);
    setVibeDiff(null);
    setIncidentCoords(null);
    setMapCenter(DEFAULT_CENTER);
    setMapZoom(DEFAULT_ZOOM);
  };

  const isLocked = isRunning && status !== 'approved' && status !== 'rejected';

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
            <select value={eventType} onChange={e => setEventType(e.target.value)} disabled={isLocked}>
              <option>Flood</option>
              <option>Earthquake</option>
              <option>Wildfire</option>
              <option>Cyclone</option>
              <option>Tropical Storm</option>
            </select>
          </div>
          <div className="input-group">
            <label>Location</label>
            <select value={eventLocation} onChange={e => setEventLocation(e.target.value)} disabled={isLocked}>
              <optgroup label="United States">
                <option>Sector 4</option>
                <option>Downtown</option>
                <option>North Ridge</option>
              </optgroup>
              <optgroup label="Zimbabwe">
                <option>Harare</option>
                <option>Bulawayo</option>
                <option>Chimanimani</option>
                <option>Mutare</option>
              </optgroup>
              <optgroup label="Mozambique">
                <option>Beira</option>
              </optgroup>
            </select>
          </div>
          <button 
            className={`btn-primary ${isLocked ? 'disabled' : ''}`}
            onClick={status === 'approved' || status === 'rejected' ? handleReset : handleStart}
            disabled={isLocked}
          >
            {status === 'running' ? <><Loader2 className="spin inline-icon" /> Processing...</> 
              : status === 'approved' || status === 'rejected' ? 'Reset & Run Again'
              : 'Trigger Response Orchestrator'}
          </button>
        </div>

        <div className="panel map-panel glass">
           <h2><MapPin className="inline-icon" /> Live Incident Map</h2>
           <div className="map-wrapper">
             <MapContainer
               center={DEFAULT_CENTER}
               zoom={DEFAULT_ZOOM}
               scrollWheelZoom={true}
               style={{ height: '100%', width: '100%' }}
             >
               <TileLayer
                 attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                 url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
               />
               <MapController center={mapCenter} zoom={mapZoom} />
               
               {incidentCoords && (
                 <>
                   <CircleMarker 
                     center={incidentCoords} 
                     radius={8}
                     pathOptions={{ color: '#ef4444', fillColor: '#ef4444', fillOpacity: 1, weight: 2 }}
                   >
                     <Tooltip permanent direction="top" offset={[0, -10]} className="map-tooltip">
                       {LOCATION_COORDS[eventLocation]?.label || eventLocation} - {eventType}
                     </Tooltip>
                   </CircleMarker>
                   <Circle
                     center={incidentCoords}
                     radius={1500}
                     pathOptions={{
                       color: '#ef4444',
                       fillColor: '#ef4444',
                       fillOpacity: 0.15,
                       weight: 2,
                       dashArray: '8 4',
                     }}
                   />
                   <Circle
                     center={incidentCoords}
                     radius={500}
                     pathOptions={{
                       color: '#ef4444',
                       fillColor: '#ef4444',
                       fillOpacity: 0.3,
                       weight: 1,
                     }}
                   />
                 </>
               )}
             </MapContainer>

             <div className={`map-status-overlay ${incidentCoords ? 'alert' : ''}`}>
               <div className="status-indicator"></div>
               {status === 'idle'
                 ? 'STANDBY — Awaiting Input'
                 : status === 'running'
                 ? `TRACKING — ${eventLocation}`
                 : `INCIDENT — ${eventType} @ ${eventLocation}`}
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

            {vibeDiff.resource_manifest && (
              <div className="diff-card">
                <h3>Resource Manifest — {vibeDiff.resource_manifest.disaster_type}</h3>
                <div className="resource-grid">
                  <div className="resource-col">
                    <p className="resource-label">Medical Supplies</p>
                    <ul>
                      {vibeDiff.resource_manifest.medical_supplies.map((s, i) => (
                        <li key={i}><ArrowRight className="inline-icon small"/> {s}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="resource-col">
                    <p className="resource-label">Heavy Equipment</p>
                    <ul>
                      {vibeDiff.resource_manifest.heavy_equipment.map((e, i) => (
                        <li key={i}><ArrowRight className="inline-icon small"/> {e}</li>
                      ))}
                    </ul>
                  </div>
                </div>
                <p className="resource-label" style={{marginTop: '0.75rem'}}>Personnel Required</p>
                <p style={{fontSize: '0.85rem'}}>{vibeDiff.resource_manifest.personnel_types.join(' • ')}</p>
              </div>
            )}

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
