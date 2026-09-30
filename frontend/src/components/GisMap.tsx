import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import type { Camera, Journey } from '../types';
import { Video } from 'lucide-react';

interface GisMapProps {
  cameras: Camera[];
  selectedCamera: Camera | null;
  onSelectCamera: (cam: Camera) => void;
  activeJourney: Journey | null;
}

export const GisMap: React.FC<GisMapProps> = ({
  cameras,
  selectedCamera,
  onSelectCamera,
  activeJourney,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);
  const trajectoryLayerRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      // Initialize map centered at New Delhi Urban Grid
      const map = L.map(mapContainerRef.current, {
        center: [28.6250, 77.2200],
        zoom: 14,
        zoomControl: true,
      });

      // Classic, clean OpenStreetMap tiles
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(map);

      mapInstanceRef.current = map;
      markersLayerRef.current = L.layerGroup().addTo(map);
      trajectoryLayerRef.current = L.layerGroup().addTo(map);
    }

    const map = mapInstanceRef.current;
    const markersLayer = markersLayerRef.current;
    const trajectoryLayer = trajectoryLayerRef.current;

    if (!map || !markersLayer || !trajectoryLayer) return;

    markersLayer.clearLayers();

    // Render Camera Markers
    cameras.forEach((cam) => {
      const isSelected = selectedCamera?.camera_id === cam.camera_id;
      
      const iconHtml = `
        <div style="
          background-color: ${isSelected ? '#C48B3F' : '#1E3F20'};
          color: white;
          width: 32px;
          height: 32px;
          border-radius: 50%;
          border: 2px solid white;
          box-shadow: 0 2px 6px rgba(0,0,0,0.35);
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          font-size: 11px;
          font-family: monospace;
          cursor: pointer;
        ">
          ${cam.camera_id.replace('CAM-0', '')}
        </div>
      `;

      const customIcon = L.divIcon({
        html: iconHtml,
        className: 'custom-cam-marker',
        iconSize: [32, 32],
        iconAnchor: [16, 16],
      });

      const marker = L.marker([cam.latitude, cam.longitude], { icon: customIcon });

      const popupContent = document.createElement('div');
      popupContent.style.fontFamily = 'system-ui, sans-serif';
      popupContent.innerHTML = `
        <div style="font-weight: bold; color: #1E3F20; font-size: 13px; margin-bottom: 4px;">
          ${cam.camera_id}: ${cam.name}
        </div>
        <div style="font-size: 11px; color: #555; margin-bottom: 6px;">
          ${cam.intersection} • ${cam.direction}
        </div>
        <div style="display: flex; gap: 8px; font-size: 11px; margin-bottom: 8px;">
          <span style="background: #EBF3EC; color: #1E3F20; padding: 2px 6px; border-radius: 4px;">
            ${cam.status}
          </span>
          <span style="background: #F6F0EB; color: #6E472A; padding: 2px 6px; border-radius: 4px;">
            Speed Limit: ${cam.speed_limit_kmh} km/h
          </span>
        </div>
      `;

      marker.bindPopup(popupContent);
      marker.on('click', () => {
        onSelectCamera(cam);
      });

      markersLayer.addLayer(marker);
    });

    // Draw active trajectory path if available
    trajectoryLayer.clearLayers();
    if (activeJourney && activeJourney.trajectory && activeJourney.trajectory.length > 1) {
      const latlngs = activeJourney.trajectory.map((w) => [w.latitude, w.longitude] as [number, number]);

      // Polylines representing journey corridor
      const polyline = L.polyline(latlngs, {
        color: '#6E472A',
        weight: 4,
        dashArray: '8, 8',
        opacity: 0.85,
      });

      trajectoryLayer.addLayer(polyline);

      // Trajectory Start and End pulsing markers
      const startWp = activeJourney.trajectory[0];
      const endWp = activeJourney.trajectory[activeJourney.trajectory.length - 1];

      const startIcon = L.divIcon({
        html: `<div style="background:#2D5831;color:white;padding:3px 6px;border-radius:4px;font-size:10px;font-weight:bold;border:1px solid white;">START</div>`,
        iconSize: [45, 20],
      });
      const endIcon = L.divIcon({
        html: `<div style="background:#8B5E3C;color:white;padding:3px 6px;border-radius:4px;font-size:10px;font-weight:bold;border:1px solid white;">DESTINATION</div>`,
        iconSize: [80, 20],
      });

      trajectoryLayer.addLayer(L.marker([startWp.latitude, startWp.longitude], { icon: startIcon }));
      trajectoryLayer.addLayer(L.marker([endWp.latitude, endWp.longitude], { icon: endIcon }));

      map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
    } else if (cameras.length > 0) {
      const bounds = L.latLngBounds(cameras.map((c) => [c.latitude, c.longitude]));
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [cameras, selectedCamera, activeJourney, onSelectCamera]);

  return (
    <div className="relative w-full h-[620px] rounded-lg overflow-hidden border border-[var(--color-border-subtle)] shadow-sm">
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Floating Camera Quick Info Overlay */}
      {selectedCamera && (
        <div className="absolute top-4 right-4 z-[1000] w-80 classic-card p-4 shadow-lg border border-[var(--color-border-subtle)] bg-[var(--color-surface)]">
          <div className="flex items-center justify-between pb-2 border-b border-[var(--color-border-subtle)] mb-3">
            <div className="flex items-center gap-2">
              <Video className="w-4 h-4 text-[var(--color-forest)]" />
              <span className="font-bold text-sm text-[var(--color-text-main)]">
                {selectedCamera.camera_id}
              </span>
            </div>
            <span className="badge-forest">{selectedCamera.status}</span>
          </div>

          <h3 className="font-semibold text-sm text-[var(--color-forest)] mb-1">
            {selectedCamera.name}
          </h3>
          <p className="text-xs text-[var(--color-text-muted)] mb-3">
            {selectedCamera.intersection} • {selectedCamera.road_segment}
          </p>

          <div className="grid grid-cols-2 gap-2 text-xs mb-3">
            <div className="p-2 rounded bg-[var(--color-canvas-alt)]">
              <span className="text-[var(--color-text-muted)] block text-[10px]">CURRENT FLOW</span>
              <span className="font-bold text-sm text-[var(--color-forest)]">
                {selectedCamera.metrics?.flow_rate_vph || 380} vph
              </span>
            </div>
            <div className="p-2 rounded bg-[var(--color-canvas-alt)]">
              <span className="text-[var(--color-text-muted)] block text-[10px]">AVG SPEED</span>
              <span className="font-bold text-sm text-[var(--color-brown)]">
                {selectedCamera.metrics?.average_speed_kmh || 42.0} km/h
              </span>
            </div>
          </div>

          {/* Mini Stream Preview Box */}
          <div className="relative w-full h-36 bg-black rounded overflow-hidden border border-[var(--color-border-subtle)] mb-3">
            <img
              src={`http://localhost:8000/api/cameras/${selectedCamera.camera_id}/stream`}
              alt="Live Camera Feed"
              className="w-full h-full object-cover"
              onError={(e) => {
                (e.target as HTMLElement).style.display = 'none';
              }}
            />
            <div className="absolute top-2 left-2 bg-black/70 px-2 py-0.5 rounded text-[10px] text-white font-mono flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
              LIVE FEED
            </div>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-[1000] classic-card px-3 py-2 text-xs bg-[var(--color-surface)]/95 backdrop-blur-sm border border-[var(--color-border-subtle)] flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-[var(--color-forest)]"></span>
          <span className="text-[var(--color-text-muted)]">Smart Camera Junction</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-[var(--color-gold)]"></span>
          <span className="text-[var(--color-text-muted)]">Selected Focus</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-0.5 bg-[var(--color-brown)]"></span>
          <span className="text-[var(--color-text-muted)]">Reconstructed Route</span>
        </div>
      </div>
    </div>
  );
};
