import React, { useState } from 'react';
import type { Camera } from '../types';
import { Maximize2, Minimize2, Activity, ShieldCheck, Gauge } from 'lucide-react';

interface MultiCameraGridProps {
  cameras: Camera[];
}

export const MultiCameraGrid: React.FC<MultiCameraGridProps> = ({ cameras }) => {
  const [fullscreenCam, setFullscreenCam] = useState<string | null>(null);

  const displayedCameras = fullscreenCam
    ? cameras.filter((c) => c.camera_id === fullscreenCam)
    : cameras;

  return (
    <div className="space-y-4">
      {/* Controls Bar */}
      <div className="flex items-center justify-between bg-[var(--color-surface)] p-3 rounded-lg border border-[var(--color-border-subtle)]">
        <div>
          <h2 className="text-sm font-bold text-[var(--color-forest)] font-serif">
            SYNCHRONIZED MULTI-CAMERA SURVEILLANCE
          </h2>
          <p className="text-xs text-[var(--color-text-muted)]">
            High-Definition Real-Time Video Feeds with Integrated AI Detection Overlays
          </p>
        </div>

        {fullscreenCam && (
          <button
            onClick={() => setFullscreenCam(null)}
            className="btn-classic-outline text-xs"
          >
            <Minimize2 className="w-3.5 h-3.5" />
            <span>Exit Fullscreen Grid</span>
          </button>
        )}
      </div>

      {/* Grid of Camera Feeds */}
      <div
        className={`grid gap-4 ${
          fullscreenCam ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
        }`}
      >
        {displayedCameras.map((cam) => {
          const streamUrl = `http://localhost:8000/api/cameras/${cam.camera_id}/stream`;
          const metrics = cam.metrics;

          return (
            <div
              key={cam.camera_id}
              className="classic-card overflow-hidden border border-[var(--color-border-subtle)] bg-[var(--color-surface)] flex flex-col"
            >
              {/* Header */}
              <div className="p-3 bg-[var(--color-canvas-alt)] border-b border-[var(--color-border-subtle)] flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-[var(--color-forest)] animate-pulse" />
                  <span className="font-mono font-bold text-xs text-[var(--color-forest)]">
                    {cam.camera_id}
                  </span>
                  <span className="text-xs text-[var(--color-text-main)] font-medium truncate max-w-[150px]">
                    {cam.name}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="badge-forest text-[10px]">{cam.status}</span>
                  <button
                    onClick={() =>
                      setFullscreenCam(fullscreenCam === cam.camera_id ? null : cam.camera_id)
                    }
                    className="p-1 hover:bg-[var(--color-border-subtle)] rounded text-[var(--color-text-muted)]"
                    title="Toggle Fullscreen"
                  >
                    <Maximize2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Video Stream Container */}
              <div className="relative aspect-video bg-[#1B1F1C] flex items-center justify-center overflow-hidden">
                <img
                  src={streamUrl}
                  alt={`Stream ${cam.camera_id}`}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLElement).style.display = 'none';
                  }}
                />

                {/* HUD Live Telemetry Overlay */}
                <div className="absolute top-2 left-2 bg-black/60 backdrop-blur-sm px-2 py-1 rounded text-[10px] text-white font-mono flex items-center gap-2">
                  <Activity className="w-3 h-3 text-[var(--color-gold)]" />
                  <span>30 FPS</span>
                  <span className="text-gray-400">|</span>
                  <span>1080p</span>
                </div>

                <div className="absolute top-2 right-2 bg-black/60 backdrop-blur-sm px-2 py-1 rounded text-[10px] text-white font-mono flex items-center gap-1.5">
                  <span className="text-gray-300">LIMIT:</span>
                  <span className="text-[var(--color-gold)] font-bold">{cam.speed_limit_kmh} KM/H</span>
                </div>

                {/* Live Detections Bar */}
                <div className="absolute bottom-2 left-2 right-2 bg-black/70 backdrop-blur-sm p-1.5 rounded text-[11px] text-white flex items-center justify-between font-mono">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                    <span>FLOW: {metrics?.flow_rate_vph || 420} VPH</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Gauge className="w-3.5 h-3.5 text-amber-400" />
                    <span>SPEED: {metrics?.average_speed_kmh || 43.5} KM/H</span>
                  </div>
                </div>
              </div>

              {/* Footer Metadata */}
              <div className="p-2.5 bg-[var(--color-surface)] text-xs flex items-center justify-between text-[var(--color-text-muted)]">
                <div>
                  <span className="font-medium text-[var(--color-text-main)]">
                    {cam.intersection}
                  </span>
                  <span className="text-[10px] block">{cam.direction} • {cam.road_segment}</span>
                </div>
                <div className="text-right">
                  <span className="badge-navy text-[10px]">
                    LOS {metrics?.level_of_service || 'B'} ({metrics?.congestion_status || 'Smooth Flow'})
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
