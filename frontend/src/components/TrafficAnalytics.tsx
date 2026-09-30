import React, { useEffect, useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { NetworkAnalytics, TrafficEvent } from '../types';
import { TrendingUp, AlertTriangle, CheckCircle, Gauge, Activity } from 'lucide-react';

interface TrafficAnalyticsProps {
  analytics: NetworkAnalytics | null;
  events: TrafficEvent[];
  onResolveEvent: (eventId: string) => Promise<void>;
}

export const TrafficAnalytics: React.FC<TrafficAnalyticsProps> = ({
  analytics,
  events,
  onResolveEvent,
}) => {
  const [odMatrix, setOdMatrix] = useState<any>(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/analytics/od-matrix')
      .then((res) => res.json())
      .then((data) => setOdMatrix(data))
      .catch((err) => console.error(err));
  }, []);

  const trends = analytics?.hourly_trends || [];

  return (
    <div className="space-y-6">
      {/* Top 4 Classic Heritage Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="classic-card p-4 bg-[var(--color-surface)]">
          <div className="flex items-center justify-between text-[var(--color-text-muted)] text-xs mb-2">
            <span>NETWORK FLOW RATE</span>
            <Activity className="w-4 h-4 text-[var(--color-forest)]" />
          </div>
          <div className="text-2xl font-bold font-serif text-[var(--color-forest)]">
            {analytics?.network_total_flow_vph || 2480} <span className="text-xs font-normal font-sans">vph</span>
          </div>
          <div className="text-[11px] text-[var(--color-text-muted)] mt-1">
            Corridor vehicular throughput across all registered junctions
          </div>
        </div>

        <div className="classic-card p-4 bg-[var(--color-surface)]">
          <div className="flex items-center justify-between text-[var(--color-text-muted)] text-xs mb-2">
            <span>CORRIDOR AVERAGE SPEED</span>
            <Gauge className="w-4 h-4 text-[var(--color-brown)]" />
          </div>
          <div className="text-2xl font-bold font-serif text-[var(--color-brown)]">
            {analytics?.network_average_speed || 41.5} <span className="text-xs font-normal font-sans">km/h</span>
          </div>
          <div className="text-[11px] text-[var(--color-text-muted)] mt-1">
            Network-wide speed index (Speed Limit: 50 km/h)
          </div>
        </div>

        <div className="classic-card p-4 bg-[var(--color-surface)]">
          <div className="flex items-center justify-between text-[var(--color-text-muted)] text-xs mb-2">
            <span>ACTIVE VEHICLES TRACKED</span>
            <TrendingUp className="w-4 h-4 text-[var(--color-navy)]" />
          </div>
          <div className="text-2xl font-bold font-serif text-[var(--color-navy)]">
            {analytics?.total_active_vehicles || 68} <span className="text-xs font-normal font-sans">active</span>
          </div>
          <div className="text-[11px] text-[var(--color-text-muted)] mt-1">
            Real-time tracked tracks across multi-camera network
          </div>
        </div>

        <div className="classic-card p-4 bg-[var(--color-surface)]">
          <div className="flex items-center justify-between text-[var(--color-text-muted)] text-xs mb-2">
            <span>INCIDENTS & VIOLATIONS</span>
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold font-serif text-[#9B2C2C]">
            {events.filter((e) => !e.resolved).length} <span className="text-xs font-normal font-sans">pending</span>
          </div>
          <div className="text-[11px] text-[var(--color-text-muted)] mt-1">
            Speeding, congestion alerts, and watchlist hits
          </div>
        </div>
      </div>

      {/* 24-Hour Trend Chart (Recharts) */}
      <div className="classic-card p-5 bg-[var(--color-surface)] border border-[var(--color-border-subtle)]">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-[var(--color-forest)] font-serif">
              24-HOUR HOURLY TRAFFIC FLOW & SPEED DISTRIBUTION
            </h3>
            <p className="text-xs text-[var(--color-text-muted)]">
              Historical baseline comparison of hourly volume (Vehicles/Hr) vs. average travel speed (km/h)
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-medium">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-[var(--color-forest)]" />
              <span>Volume (vph)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-[var(--color-brown)]" />
              <span>Speed (km/h)</span>
            </div>
          </div>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trends} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="flowGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#1E3F20" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#1E3F20" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="speedGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8B5E3C" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#8B5E3C" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#E3DBD0" />
              <XAxis dataKey="hour" stroke="#7E8880" fontSize={11} />
              <YAxis stroke="#7E8880" fontSize={11} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#FFFFFF',
                  borderColor: '#E3DBD0',
                  borderRadius: '6px',
                  fontSize: '12px',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                }}
              />
              <Area
                type="monotone"
                dataKey="flow"
                stroke="#1E3F20"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#flowGrad)"
                name="Traffic Flow (vph)"
              />
              <Area
                type="monotone"
                dataKey="avg_speed"
                stroke="#8B5E3C"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#speedGrad)"
                name="Avg Speed (km/h)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Origin-Destination (OD) Matrix & Incidents Table */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* OD Matrix Card */}
        <div className="classic-card p-5 bg-[var(--color-surface)] space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[var(--color-border-subtle)]">
            <h3 className="text-sm font-bold text-[var(--color-forest)] font-serif">
              ORIGIN-DESTINATION (OD) MOBILITY MATRIX
            </h3>
            <span className="badge-forest text-[10px]">CORRIDOR PAIRS</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-[var(--color-border-subtle)] text-[var(--color-text-muted)]">
                  <th className="py-2 px-3 font-semibold">Origin / Dest</th>
                  {odMatrix?.cameras?.map((cam: string) => (
                    <th key={cam} className="py-2 px-3 font-mono font-bold text-center">
                      {cam.replace('CAM-0', 'C')}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {odMatrix?.matrix?.map((row: any) => (
                  <tr
                    key={row.origin}
                    className="border-b border-[var(--color-canvas-alt)] hover:bg-[var(--color-surface-hover)]"
                  >
                    <td className="py-2 px-3 font-mono font-bold text-[var(--color-forest)]">
                      {row.origin}
                    </td>
                    {odMatrix?.cameras?.map((dst: string) => (
                      <td key={dst} className="py-2 px-3 text-center font-mono">
                        {row[dst] > 0 ? (
                          <span className="font-bold text-[var(--color-brown)]">{row[dst]}</span>
                        ) : (
                          <span className="text-[var(--color-text-faint)]">-</span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Live Traffic Incidents & Alerts Stream */}
        <div className="classic-card p-5 bg-[var(--color-surface)] space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[var(--color-border-subtle)]">
            <h3 className="text-sm font-bold text-[var(--color-brown)] font-serif flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              LIVE ANOMALIES & AUDIT ALERTS
            </h3>
            <span className="badge-navy text-[10px]">REAL-TIME AUDIT</span>
          </div>

          <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
            {events.map((evt) => (
              <div
                key={evt.event_id}
                className="p-3 rounded border border-[var(--color-border-subtle)] bg-[var(--color-surface-hover)] flex items-start justify-between"
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono font-bold text-xs text-[var(--color-text-main)]">
                      {evt.event_id}
                    </span>
                    <span
                      className={
                        evt.severity === 'CRITICAL'
                          ? 'badge-red'
                          : evt.severity === 'HIGH'
                          ? 'badge-gold'
                          : 'badge-navy'
                      }
                    >
                      {evt.event_type}
                    </span>
                    <span className="text-[10px] text-[var(--color-text-faint)] font-mono">
                      {new Date(evt.timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  <p className="text-xs text-[var(--color-text-main)]">
                    Camera: <strong className="font-mono">{evt.camera_id}</strong>
                    {evt.details?.speed_detected && (
                      <span> • Speed: <strong className="text-red-600">{evt.details.speed_detected} km/h</strong> (Limit: {evt.details.speed_limit} km/h)</span>
                    )}
                    {evt.details?.plate_number && (
                      <span> • Plate: <strong className="font-mono text-[var(--color-forest)]">{evt.details.plate_number}</strong></span>
                    )}
                  </p>

                  {evt.details?.reason && (
                    <p className="text-[11px] text-[var(--color-text-muted)] mt-0.5">
                      Reason: {evt.details.reason}
                    </p>
                  )}
                </div>

                {!evt.resolved && (
                  <button
                    onClick={() => onResolveEvent(evt.event_id)}
                    className="btn-classic-outline text-[11px] py-1 px-2.5"
                  >
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Resolve</span>
                  </button>
                )}
              </div>
            ))}

            {events.length === 0 && (
              <div className="text-center py-8 text-xs text-[var(--color-text-muted)]">
                No active traffic anomalies logged.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
