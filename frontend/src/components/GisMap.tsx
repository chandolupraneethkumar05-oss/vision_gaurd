import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import type { Camera, Journey } from '../types';
import { Video, Layers, RotateCcw } from 'lucide-react';

interface GisMapProps {
  cameras: Camera[];
  selectedCamera: Camera | null;
  onSelectCamera: (cam: Camera) => void;
  activeJourney: Journey | null;
}

// Canonical road corridors connecting smart city camera nodes (New Delhi Grid)
const ROAD_CORRIDORS = [
  { from: 'CAM-01', to: 'CAM-02', name: 'Barakhamba Radial Corridor', distance: '0.75 km', minTime: '40s' },
  { from: 'CAM-02', to: 'CAM-04', name: 'Barakhamba-Tolstoy Connector', distance: '0.55 km', minTime: '30s' },
  { from: 'CAM-01', to: 'CAM-04', name: 'Outer Radial Link', distance: '0.80 km', minTime: '45s' },
  { from: 'CAM-04', to: 'CAM-03', name: 'Tolstoy-Janpath Crossing', distance: '0.65 km', minTime: '35s' },
  { from: 'CAM-03', to: 'CAM-05', name: 'Janpath-Sansad Expressway', distance: '0.90 km', minTime: '50s' },
  { from: 'CAM-04', to: 'CAM-06', name: 'Tolstoy-Hexagon Radial', distance: '1.60 km', minTime: '90s' },
  { from: 'CAM-03', to: 'CAM-06', name: 'Janpath-India Gate Boulevard', distance: '1.40 km', minTime: '80s' },
];

export const GisMap: React.FC<GisMapProps> = ({
  cameras,
  selectedCamera,
  onSelectCamera,
  activeJourney,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);
  const corridorsLayerRef = useRef<L.LayerGroup | null>(null);
  const trajectoryLayerRef = useRef<L.LayerGroup | null>(null);

  const [showCorridors, setShowCorridors] = useState<boolean>(true);

  // Initialize Map Once
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [28.6245, 77.2215],
        zoom: 14,
        zoomControl: true,
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(map);

      mapInstanceRef.current = map;
      corridorsLayerRef.current = L.layerGroup().addTo(map);
      trajectoryLayerRef.current = L.layerGroup().addTo(map);
      markersLayerRef.current = L.layerGroup().addTo(map);
    }
  }, []);

  // Update Layers & Corridors
  useEffect(() => {
    const map = mapInstanceRef.current;
    const markersLayer = markersLayerRef.current;
    const corridorsLayer = corridorsLayerRef.current;
    const trajectoryLayer = trajectoryLayerRef.current;

    if (!map || !markersLayer || !corridorsLayer || !trajectoryLayer) return;

    // 1. Draw Road Network Corridors
    corridorsLayer.clearLayers();
    if (showCorridors && cameras.length > 0) {
      const camMap = new Map(cameras.map((c) => [c.camera_id, c]));

      ROAD_CORRIDORS.forEach((corridor) => {
        const c1 = camMap.get(corridor.from);
        const c2 = camMap.get(corridor.to);
        if (c1 && c2) {
          const latlngs: [number, number][] = [
            [c1.latitude, c1.longitude],
            [c2.latitude, c2.longitude],
          ];

          const line = L.polyline(latlngs, {
            color: '#2D5831',
            weight: 3,
            opacity: 0.55,
            dashArray: '6, 6',
          });

          line.bindTooltip(
            `<strong>${corridor.name}</strong><br/>Length: ${corridor.distance} • Min Time: ${corridor.minTime}`,
            { sticky: true, className: 'classic-map-tooltip' }
          );

          corridorsLayer.addLayer(line);
        }
      });
    }

    // 2. Draw Camera Markers
    markersLayer.clearLayers();
    cameras.forEach((cam) => {
      const isSelected = selectedCamera?.camera_id === cam.camera_id;
      const numLabel = cam.camera_id.replace('CAM-0', '').replace('CAM-', '');

      const iconHtml = `
        <div style="
          background-color: ${isSelected ? '#C48B3F' : '#1E3F20'};
          color: white;
          width: 34px;
          height: 34px;
          border-radius: 50%;
          border: 2.5px solid white;
          box-shadow: 0 3px 8px rgba(0,0,0,0.35);
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          font-size: 11px;
          font-family: monospace;
          cursor: pointer;
          transition: transform 0.15s ease;
        ">
          ${numLabel}
        </div>
      `;

      const customIcon = L.divIcon({
        html: iconHtml,
        className: 'custom-cam-marker',
        iconSize: [34, 34],
        iconAnchor: [17, 17],
      });

      const marker = L.marker([cam.latitude, cam.longitude], { icon: customIcon });

      const popupHtml = `
        <div style="font-family: system-ui, sans-serif; min-width: 180px;">
          <div style="font-weight: bold; color: #1E3F20; font-size: 13px; margin-bottom: 2px;">
            ${cam.camera_id}: ${cam.name}
          </div>
          <div style="font-size: 11px; color: #666; margin-bottom: 6px;">
            ${cam.intersection} • ${cam.direction}
          </div>
          <div style="display: flex; gap: 6px; font-size: 10px; margin-bottom: 6px;">
            <span style="background: #EBF3EC; color: #1E3F20; padding: 2px 6px; border-radius: 4px; font-weight: bold;">
              ${cam.status}
            </span>
            <span style="background: #F6F0EB; color: #6E472A; padding: 2px 6px; border-radius: 4px;">
              Limit: ${cam.speed_limit_kmh} km/h
            </span>
          </div>
        </div>
      `;

      marker.bindPopup(popupHtml);
      marker.on('click', () => {
        onSelectCamera(cam);
      });

      markersLayer.addLayer(marker);
    });

    // 3. Draw Active Trajectory Path
    trajectoryLayer.clearLayers();
    if (activeJourney && activeJourney.trajectory && activeJourney.trajectory.length > 1) {
      const latlngs = activeJourney.trajectory.map((w) => [w.latitude, w.longitude] as [number, number]);

      const polyline = L.polyline(latlngs, {
        color: '#8B5E3C',
        weight: 5,
        opacity: 0.95,
      });
      trajectoryLayer.addLayer(polyline);

      // Trajectory Start and End Markers
      const startWp = activeJourney.trajectory[0];
      const endWp = activeJourney.trajectory[activeJourney.trajectory.length - 1];

      const startIcon = L.divIcon({
        html: `<div style="background:#1E3F20;color:white;padding:3px 7px;border-radius:4px;font-size:10px;font-weight:bold;border:1.5px solid white;box-shadow:0 2px 5px rgba(0,0,0,0.3);">START</div>`,
        iconSize: [48, 22],
        iconAnchor: [24, 11],
      });
      const endIcon = L.divIcon({
        html: `<div style="background:#8B5E3C;color:white;padding:3px 7px;border-radius:4px;font-size:10px;font-weight:bold;border:1.5px solid white;box-shadow:0 2px 5px rgba(0,0,0,0.3);">DESTINATION</div>`,
        iconSize: [84, 22],
        iconAnchor: [42, 11],
      });

      trajectoryLayer.addLayer(L.marker([startWp.latitude, startWp.longitude], { icon: startIcon }));
      trajectoryLayer.addLayer(L.marker([endWp.latitude, endWp.longitude], { icon: endIcon }));

      map.fitBounds(polyline.getBounds(), { padding: [60, 60] });
    }
  }, [cameras, selectedCamera, activeJourney, showCorridors, onSelectCamera]);

  const resetMapView = () => {
    if (mapInstanceRef.current && cameras.length > 0) {
      const bounds = L.latLngBounds(cameras.map((c) => [c.latitude, c.longitude]));
      mapInstanceRef.current.fitBounds(bounds, { padding: [50, 50] });
    }
  };

  return (
    <div className="relative w-full h-[620px] rounded-lg overflow-hidden border border-[var(--color-border-subtle)] shadow-xs">
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Map Control Tools Bar (Top Left) */}
      <div className="absolute top-4 left-4 z-[1000] flex items-center gap-2 bg-[var(--color-surface)]/95 backdrop-blur-sm px-3 py-1.5 rounded-lg border border-[var(--color-border-subtle)] shadow-sm text-xs font-mono">
        <label className="flex items-center gap-1.5 cursor-pointer text-[var(--color-text-main)]">
          <input
            type="checkbox"
            checked={showCorridors}
            onChange={(e) => setShowCorridors(e.target.checked)}
            className="rounded text-[var(--color-forest)] focus:ring-0"
          />
          <Layers className="w-3.5 h-3.5 text-[var(--color-forest)]" />
          <span>Road Corridors</span>
        </label>

        <span className="text-[var(--color-border-subtle)]">|</span>

        <button
          onClick={resetMapView}
          className="flex items-center gap-1 text-[var(--color-text-muted)] hover:text-black transition-colors"
          title="Reset map zoom"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Fit Grid</span>
        </button>
      </div>

      {/* Floating Camera Detail Pane (Top Right) */}
      {selectedCamera && (
        <div className="absolute top-4 right-4 z-[1000] w-84 classic-card p-4 shadow-lg border border-[var(--color-border-subtle)] bg-[var(--color-surface)]">
          <div className="flex items-center justify-between pb-2 border-b border-[var(--color-border-subtle)] mb-3">
            <div className="flex items-center gap-2">
              <Video className="w-4 h-4 text-[var(--color-forest)]" />
              <span className="font-bold text-sm text-[var(--color-text-main)] font-mono">
                {selectedCamera.camera_id}
              </span>
            </div>
            <span className="badge-forest text-[10px]">{selectedCamera.status}</span>
          </div>

          <h3 className="font-semibold text-sm text-[var(--color-forest)] mb-1">
            {selectedCamera.name}
          </h3>
          <p className="text-xs text-[var(--color-text-muted)] mb-3">
            {selectedCamera.intersection} • {selectedCamera.road_segment}
          </p>

          <div className="grid grid-cols-2 gap-2 text-xs mb-3 font-mono">
            <div className="p-2 rounded bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)]">
              <span className="text-[var(--color-text-muted)] block text-[10px]">CURRENT FLOW</span>
              <span className="font-bold text-sm text-[var(--color-forest)]">
                {selectedCamera.metrics?.flow_rate_vph || 380} vph
              </span>
            </div>
            <div className="p-2 rounded bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)]">
              <span className="text-[var(--color-text-muted)] block text-[10px]">AVG SPEED</span>
              <span className="font-bold text-sm text-[var(--color-brown)]">
                {selectedCamera.metrics?.average_speed_kmh || 42.0} km/h
              </span>
            </div>
          </div>

          {/* Mini Live Stream Preview */}
          <div className="relative w-full h-36 bg-black rounded overflow-hidden border border-[var(--color-border-subtle)] mb-2">
            <img
              src={`http://localhost:8000/api/cameras/${selectedCamera.camera_id}/stream`}
              alt="Live Camera Feed"
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.target as HTMLElement).style.display = 'none';
              }}
            />
            <div className="absolute top-2 left-2 bg-black/75 px-2 py-0.5 rounded text-[10px] text-white font-mono flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
              <span>LIVE AI FEED</span>
            </div>
          </div>
        </div>
      )}

      {/* Map Legend */}
      <div className="absolute bottom-4 left-4 z-[1000] classic-card px-3.5 py-2 text-xs bg-[var(--color-surface)]/95 backdrop-blur-sm border border-[var(--color-border-subtle)] flex items-center gap-4 shadow-sm">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-[var(--color-forest)]"></span>
          <span className="text-[var(--color-text-muted)]">Camera Junction</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3.5 h-0.5 bg-[#2D5831] border-dashed"></span>
          <span className="text-[var(--color-text-muted)]">Road Corridor</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-1 bg-[#8B5E3C] rounded"></span>
          <span className="text-[var(--color-text-muted)]">Active Trajectory</span>
        </div>
      </div>
    </div>
  );
};
