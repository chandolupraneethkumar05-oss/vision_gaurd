import { useState, useEffect } from 'react';
import './styles/classic-theme.css';
import { Navbar } from './components/Navbar';
import { GisMap } from './components/GisMap';
import { MultiCameraGrid } from './components/MultiCameraGrid';
import { JourneyVisualizer } from './components/JourneyVisualizer';
import { AnprWatchlist } from './components/AnprWatchlist';
import { TrafficAnalytics } from './components/TrafficAnalytics';
import { GroundedAssistant } from './components/GroundedAssistant';
import { SystemTelemetry } from './components/SystemTelemetry';
import type { Camera, Observation, Journey, TrafficEvent, WatchlistItem, NetworkAnalytics, SystemHealth } from './types';

const API_BASE = 'http://localhost:8000';

export function App() {
  const [activeTab, setActiveTab] = useState<string>('gis');
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);
  const [journeys, setJourneys] = useState<Journey[]>([]);
  const [selectedJourney, setSelectedJourney] = useState<Journey | null>(null);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [analytics, setAnalytics] = useState<NetworkAnalytics | null>(null);
  const [events, setEvents] = useState<TrafficEvent[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);

  // Fetch initial data
  const fetchData = async () => {
    try {
      const [camsRes, jrnRes, obsRes, wchRes, netRes, evtRes, hltRes] = await Promise.all([
        fetch(`${API_BASE}/api/cameras`).then((r) => r.json()),
        fetch(`${API_BASE}/api/journeys`).then((r) => r.json()),
        fetch(`${API_BASE}/api/anpr/observations`).then((r) => r.json()),
        fetch(`${API_BASE}/api/anpr/watchlist`).then((r) => r.json()),
        fetch(`${API_BASE}/api/analytics/network`).then((r) => r.json()),
        fetch(`${API_BASE}/api/analytics/events`).then((r) => r.json()),
        fetch(`${API_BASE}/api/system/health`).then((r) => r.json()),
      ]);

      setCameras(camsRes || []);
      if (camsRes && camsRes.length > 0 && !selectedCamera) {
        setSelectedCamera(camsRes[0]);
      }
      setJourneys(jrnRes || []);
      if (jrnRes && jrnRes.length > 0 && !selectedJourney) {
        setSelectedJourney(jrnRes[0]);
      }
      setObservations(obsRes || []);
      setWatchlist(wchRes || []);
      setAnalytics(netRes || null);
      setEvents(evtRes || []);
      setSystemHealth(hltRes || null);
    } catch (err) {
      console.error('Error fetching data from VisionGuard API:', err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000); // Polling baseline
    return () => clearInterval(interval);
  }, []);

  // Real-time WebSocket connection for live telemetry & observations
  useEffect(() => {
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket('ws://localhost:8000/ws');
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'NEW_OBSERVATION') {
            const newObs = msg.data;
            setObservations((prev) => [newObs, ...prev.slice(0, 49)]);

            if (msg.alerts && msg.alerts.length > 0) {
              setEvents((prev) => [...msg.alerts, ...prev]);
            }
          }
        } catch (e) {
          console.error('WebSocket parse error:', e);
        }
      };
    } catch (e) {
      console.warn('WebSocket connection not available:', e);
    }

    return () => {
      if (ws) ws.close();
    };
  }, []);

  // Handlers
  const handleAddToWatchlist = async (plate: string, desc: string, reason: string, priority: string) => {
    await fetch(`${API_BASE}/api/anpr/watchlist`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plate_number: plate, vehicle_desc: desc, reason, priority }),
    });
    const updated = await fetch(`${API_BASE}/api/anpr/watchlist`).then((r) => r.json());
    setWatchlist(updated);
  };

  const handleRemoveFromWatchlist = async (plate: string) => {
    await fetch(`${API_BASE}/api/anpr/watchlist/${encodeURIComponent(plate)}`, {
      method: 'DELETE',
    });
    setWatchlist((prev) => prev.filter((w) => w.plate_number !== plate));
  };

  const handleResolveEvent = async (eventId: string) => {
    await fetch(`${API_BASE}/api/analytics/events/${eventId}/resolve`, {
      method: 'POST',
    });
    setEvents((prev) =>
      prev.map((e) => (e.event_id === eventId ? { ...e, resolved: 1 } : e))
    );
  };

  const pendingAlertCount = events.filter((e) => !e.resolved).length;

  return (
    <div className="min-h-screen flex flex-col bg-[var(--color-canvas)] text-[var(--color-text-main)]">
      {/* Heritage Classic Navigation Bar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        systemHealth={systemHealth}
        alertCount={pendingAlertCount}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'gis' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-[var(--color-forest)] font-serif">
                  URBAN ROAD NETWORK GIS MAPPING
                </h2>
                <p className="text-xs text-[var(--color-text-muted)]">
                  Geospatial visualization of smart intersections, active vehicle trajectories, and corridor flows.
                </p>
              </div>
              {selectedJourney && (
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-[var(--color-text-muted)]">Replaying Journey:</span>
                  <span className="font-mono font-bold text-[var(--color-brown)]">
                    {selectedJourney.primary_plate || selectedJourney.journey_id}
                  </span>
                  <button
                    onClick={() => setSelectedJourney(null)}
                    className="text-[11px] underline text-[var(--color-text-muted)] hover:text-black ml-1"
                  >
                    Clear Path
                  </button>
                </div>
              )}
            </div>

            <GisMap
              cameras={cameras}
              selectedCamera={selectedCamera}
              onSelectCamera={(cam) => setSelectedCamera(cam)}
              activeJourney={selectedJourney}
            />
          </div>
        )}

        {activeTab === 'cameras' && <MultiCameraGrid cameras={cameras} />}

        {activeTab === 'journeys' && (
          <JourneyVisualizer
            journeys={journeys}
            selectedJourney={selectedJourney}
            onSelectJourney={(j) => {
              setSelectedJourney(j);
            }}
          />
        )}

        {activeTab === 'anpr' && (
          <AnprWatchlist
            observations={observations}
            watchlist={watchlist}
            onAddToWatchlist={handleAddToWatchlist}
            onRemoveFromWatchlist={handleRemoveFromWatchlist}
          />
        )}

        {activeTab === 'analytics' && (
          <TrafficAnalytics
            analytics={analytics}
            events={events}
            onResolveEvent={handleResolveEvent}
          />
        )}

        {activeTab === 'assistant' && <GroundedAssistant />}

        {activeTab === 'system' && <SystemTelemetry health={systemHealth} />}
      </main>

      {/* Classic Elegant Footer */}
      <footer className="border-t border-[var(--color-border-subtle)] bg-[var(--color-surface)] py-4 text-xs text-[var(--color-text-muted)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="font-serif">
            <strong>VISIONGUARD</strong> • AI Urban Traffic Intelligence Platform (SIH26127)
          </div>
          <div className="text-[11px] font-mono">
            Full Target Stack: CV • YOLO Detector • ByteTrack • Indian ANPR • Re-ID • GIS • Grounded AI
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
