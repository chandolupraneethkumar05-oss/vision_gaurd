import React, { useEffect, useRef, useState, useCallback } from 'react';
import L from 'leaflet';
import type { Camera, Journey } from '../types';
import { Video, Layers, RotateCcw, Crosshair, MapPin } from 'lucide-react';
import { API_BASE } from '../config/api';

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

const createMarkerIcon = (camera_id: string, isSelected: boolean) => {
  const numLabel = camera_id.replace('CAM-0', '').replace('CAM-', '');
  const iconHtml = `
    <div style="position: relative; width: ${isSelected ? '44px' : '34px'}; height: ${isSelected ? '44px' : '34px'};">
      ${isSelected ? `
        <div style="
          position: absolute;
          inset: -6px;
          border-radius: 50%;
          border: 2px solid #C48B3F;
          animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
          opacity: 0.75;
        "></div>
      ` : ''}
      <div style="
        background-color: ${isSelected ? '#C48B3F' : '#1E3F20'};
        color: white;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: ${isSelected ? '3px solid white' : '2px solid white'};
        box-shadow: 0 4px 10px rgba(0,0,0,0.35);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: ${isSelected ? '14px' : '11px'};
        font-family: monospace;
        cursor: pointer;
        transition: transform 0.2s ease;
      ">
        ${numLabel}
      </div>
    </div>
  `;

  return L.divIcon({
    html: iconHtml,
    className: 'custom-cam-marker',
    iconSize: [isSelected ? 44 : 34, isSelected ? 44 : 34],
    iconAnchor: [isSelected ? 22 : 17, isSelected ? 22 : 17],
  });
};

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
  const markersMapRef = useRef<Map<string, L.Marker>>(new Map());

  // Guard to ensure auto fitBounds runs ONLY on first data load
  const hasInitialFittedRef = useRef<boolean>(false);

  const [showCorridors, setShowCorridors] = useState<boolean>(true);
  const [currentZoom, setCurrentZoom] = useState<number>(14);

  // Initialize Map Once
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [28.6245, 77.2215],
        zoom: 14,
        zoomControl: true,
        scrollWheelZoom: true,
      });

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(map);

      map.on('zoomend', () => {
        setCurrentZoom(map.getZoom());
      });

      mapInstanceRef.current = map;
      corridorsLayerRef.current = L.layerGroup().addTo(map);
      trajectoryLayerRef.current = L.layerGroup().addTo(map);
      markersLayerRef.current = L.layerGroup().addTo(map);
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
        hasInitialFittedRef.current = false;
        markersMapRef.current.clear();
      }
    };
  }, []);

  // Update Road Corridors Layer
  useEffect(() => {
    const corridorsLayer = corridorsLayerRef.current;
    if (!corridorsLayer) return;

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
            color: '#1E3F20',
            weight: 3.5,
            opacity: 0.65,
            dashArray: '8, 8',
          });

          line.bindTooltip(
            `<strong>${corridor.name}</strong><br/>Distance: ${corridor.distance} • Flow Time: ${corridor.minTime}`,
            { sticky: true, className: 'classic-map-tooltip' }
          );

          corridorsLayer.addLayer(line);
        }
      });
    }
  }, [cameras, showCorridors]);

  // Persistent Camera Markers: never wipe during zoom or selection!
  useEffect(() => {
    const map = mapInstanceRef.current;
    const markersLayer = markersLayerRef.current;
    if (!map || !markersLayer || cameras.length === 0) return;

    cameras.forEach((cam) => {
      const isSelected = selectedCamera?.camera_id === cam.camera_id;
      let marker = markersMapRef.current.get(cam.camera_id);

      if (!marker) {
        // Create marker once
        marker = L.marker([cam.latitude, cam.longitude], {
          icon: createMarkerIcon(cam.camera_id, isSelected),
        });

        const popupHtml = `
          <div style="font-family: system-ui, sans-serif; min-width: 220px;">
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
                Speed Limit: ${cam.speed_limit_kmh} km/h
              </span>
            </div>
            <div style="font-size: 11px; color: #444; border-top: 1px solid #eee; padding-top: 4px;">
              Flow: <strong>${cam.metrics?.flow_rate_vph || 380} vph</strong> | LOS: <strong>${cam.metrics?.level_of_service || 'B'}</strong>
            </div>
          </div>
        `;
        marker.bindPopup(popupHtml);

        marker.on('click', () => {
          onSelectCamera(cam);
        });

        markersLayer.addLayer(marker);
        markersMapRef.current.set(cam.camera_id, marker);
      } else {
        // Update existing marker's icon to reflect selected state without re-creating
        marker.setIcon(createMarkerIcon(cam.camera_id, isSelected));
      }
    });

    // Initial fit bounds ONCE only on initial data load
    if (!hasInitialFittedRef.current && cameras.length > 0) {
      const bounds = L.latLngBounds(cameras.map((c) => [c.latitude, c.longitude]));
      map.fitBounds(bounds, { padding: [50, 50] });
      hasInitialFittedRef.current = true;
    }
  }, [cameras, selectedCamera?.camera_id, onSelectCamera]);

  // Smoothly Pan to Selected Camera without altering user's manual zoom level
  useEffect(() => {
    if (mapInstanceRef.current && selectedCamera && hasInitialFittedRef.current) {
      mapInstanceRef.current.panTo([selectedCamera.latitude, selectedCamera.longitude], {
        animate: true,
        duration: 0.5,
      });

      // Also ensure marker popup is open
      const marker = markersMapRef.current.get(selectedCamera.camera_id);
      if (marker && !marker.isPopupOpen()) {
        marker.openPopup();
      }
    }
  }, [selectedCamera]);

  // Update Trajectory Path
  useEffect(() => {
    const map = mapInstanceRef.current;
    const trajectoryLayer = trajectoryLayerRef.current;
    if (!map || !trajectoryLayer) return;

    trajectoryLayer.clearLayers();
    if (activeJourney && activeJourney.trajectory && activeJourney.trajectory.length > 1) {
      const latlngs = activeJourney.trajectory.map((w) => [w.latitude, w.longitude] as [number, number]);

      const polyline = L.polyline(latlngs, {
        color: '#6E472A',
        weight: 5,
        opacity: 0.9,
      }).addTo(trajectoryLayer);

      const startWp = activeJourney.trajectory[0];
      const endWp = activeJourney.trajectory[activeJourney.trajectory.length - 1];

      const startIcon = L.divIcon({
        html: `<div style="background: #1E3F20; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);">A</div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      });

      const endIcon = L.divIcon({
        html: `<div style="background: #9B2C2C; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);">B</div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      });

      trajectoryLayer.addLayer(L.marker([startWp.latitude, startWp.longitude], { icon: startIcon }));
      trajectoryLayer.addLayer(L.marker([endWp.latitude, endWp.longitude], { icon: endIcon }));

      map.fitBounds(polyline.getBounds(), { padding: [70, 70] });
    }
  }, [activeJourney]);

  // Reset to City Grid view
  const resetMapView = useCallback(() => {
    if (mapInstanceRef.current && cameras.length > 0) {
      const bounds = L.latLngBounds(cameras.map((c) => [c.latitude, c.longitude]));
      mapInstanceRef.current.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [cameras]);

  return (
    <div className="space-y-3">
      {/* Interactive Camera Quick Switcher Chip Bar */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs font-mono">
        <span className="text-[var(--color-text-muted)] flex items-center gap-1 font-sans font-medium whitespace-nowrap">
          <MapPin className="w-3.5 h-3.5 text-[var(--color-forest)]" />
          <span>Select Junction Point:</span>
        </span>
        {cameras.map((cam) => {
          const isSelected = selectedCamera?.camera_id === cam.camera_id;
          return (
            <button
              key={cam.camera_id}
              onClick={() => onSelectCamera(cam)}
              className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-all flex items-center gap-1.5 ${
                isSelected
                  ? 'bg-[var(--color-forest)] text-white shadow-sm ring-2 ring-[#C48B3F]'
                  : 'bg-[var(--color-surface)] text-[var(--color-text-main)] hover:bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)]'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${isSelected ? 'bg-[#C48B3F]' : 'bg-[var(--color-forest)]'}`}></span>
              <span>{cam.camera_id}: {cam.name.split(' ')[0]}</span>
            </button>
          );
        })}
      </div>

      {/* Main Map Box */}
      <div className="relative w-full h-[620px] rounded-lg overflow-hidden border border-[var(--color-border-subtle)] shadow-xs bg-[#E8ECE9]">
        <div ref={mapContainerRef} className="w-full h-full" />

        {/* Map Control Tools Bar (Top Left) */}
        <div className="absolute top-4 left-4 z-[1000] flex items-center gap-3 bg-[var(--color-surface)]/95 backdrop-blur-sm px-3.5 py-2 rounded-lg border border-[var(--color-border-subtle)] shadow-md text-xs font-mono">
          <label className="flex items-center gap-1.5 cursor-pointer text-[var(--color-text-main)] hover:text-[var(--color-forest)] transition-colors">
            <input
              type="checkbox"
              checked={showCorridors}
              onChange={(e) => setShowCorridors(e.target.checked)}
              className="rounded text-[var(--color-forest)] focus:ring-0 cursor-pointer"
            />
            <Layers className="w-3.5 h-3.5 text-[var(--color-forest)]" />
            <span>Road Corridors</span>
          </label>

          <span className="text-[var(--color-border-subtle)]">|</span>

          <button
            onClick={resetMapView}
            className="flex items-center gap-1.5 text-[var(--color-text-muted)] hover:text-[var(--color-forest)] font-medium transition-colors"
            title="Reset zoom to fit all city camera nodes"
          >
            <RotateCcw className="w-3.5 h-3.5 text-[var(--color-brown)]" />
            <span>Fit Grid</span>
          </button>

          <span className="text-[var(--color-border-subtle)]">|</span>

          <div className="flex items-center gap-1 text-[11px] text-[var(--color-text-faint)]">
            <Crosshair className="w-3 h-3 text-[var(--color-forest)]" />
            <span>Zoom: {currentZoom}x</span>
          </div>
        </div>

        {/* Floating Camera Detail Pane (Top Right) */}
        {selectedCamera && (
          <div className="absolute top-4 right-4 z-[1000] w-84 classic-card p-4 shadow-xl border border-[var(--color-border-subtle)] bg-[var(--color-surface)]">
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
                src={`${API_BASE}/api/cameras/${selectedCamera.camera_id}/stream`}
                alt="Live Camera Feed"
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
              <div className="absolute top-2 left-2 bg-black/75 px-2 py-0.5 rounded text-[10px] text-white font-mono flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
                <span>LIVE AI STREAM</span>
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
            <span className="w-3.5 h-0.5 bg-[#1E3F20] border-dashed"></span>
            <span className="text-[var(--color-text-muted)]">Road Corridor</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-4 h-1 bg-[#8B5E3C] rounded"></span>
            <span className="text-[var(--color-text-muted)]">Active Trajectory</span>
          </div>
        </div>
      </div>
    </div>
  );
};
