import React, { useState } from 'react';
import type { Journey } from '../types';
import { Search, Clock, ArrowRight, Route } from 'lucide-react';

interface JourneyVisualizerProps {
  journeys: Journey[];
  onSelectJourney: (journey: Journey) => void;
  selectedJourney: Journey | null;
}

export const JourneyVisualizer: React.FC<JourneyVisualizerProps> = ({
  journeys,
  onSelectJourney,
  selectedJourney,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = journeys.filter((j) => {
    const term = searchTerm.toLowerCase();
    const plate = (j.primary_plate || '').toLowerCase();
    const vehId = (j.global_vehicle_id || '').toLowerCase();
    const vClass = (j.vehicle_class || '').toLowerCase();
    return plate.includes(term) || vehId.includes(term) || vClass.includes(term);
  });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left List of Reconstructed Vehicle Journeys */}
      <div className="lg:col-span-1 space-y-4">
        {/* Search Header */}
        <div className="classic-card p-4 bg-[var(--color-surface)]">
          <h2 className="text-sm font-bold text-[var(--color-forest)] font-serif mb-2 flex items-center gap-2">
            <Route className="w-4 h-4 text-[var(--color-brown)]" />
            CROSS-CAMERA JOURNEY RECONSTRUCTOR
          </h2>
          <p className="text-xs text-[var(--color-text-muted)] mb-3">
            Multi-target multi-camera (MTMC) trajectory stitching with spatio-temporal constraint verification.
          </p>

          <div className="relative">
            <Search className="w-4 h-4 text-[var(--color-text-faint)] absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search Plate (e.g. DL 01 AB 1234)..."
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded border border-[var(--color-border-subtle)] bg-[var(--color-canvas-alt)] focus:outline-none focus:border-[var(--color-forest)]"
            />
          </div>
        </div>

        {/* Journey Card List */}
        <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
          {filtered.map((j) => {
            const isSelected = selectedJourney?.journey_id === j.journey_id;
            return (
              <div
                key={j.journey_id}
                onClick={() => onSelectJourney(j)}
                className={`classic-card p-3 cursor-pointer transition-all ${
                  isSelected
                    ? 'border-2 border-[var(--color-forest)] bg-[var(--color-forest-subtle)]'
                    : 'classic-card-hover'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-xs text-[var(--color-forest)]">
                      {j.primary_plate || j.global_vehicle_id}
                    </span>
                    <span className="badge-brown text-[10px] uppercase">
                      {j.vehicle_class || 'Vehicle'}
                    </span>
                  </div>
                  <span className="badge-forest text-[10px]">
                    {j.status}
                  </span>
                </div>

                <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)] mb-2">
                  <span className="font-mono">{j.start_camera}</span>
                  <ArrowRight className="w-3 h-3 text-[var(--color-text-faint)]" />
                  <span className="font-mono">{j.end_camera}</span>
                  <span className="text-[10px] text-[var(--color-text-faint)]">
                    ({j.trajectory?.length || 0} nodes)
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] pt-2 border-t border-[var(--color-border-subtle)] text-[var(--color-text-muted)]">
                  <div>
                    <span>Dist: </span>
                    <strong className="text-[var(--color-text-main)]">{j.total_distance_km} km</strong>
                  </div>
                  <div className="text-right">
                    <span>Avg: </span>
                    <strong className="text-[var(--color-brown)]">{j.avg_speed_kmh} km/h</strong>
                  </div>
                </div>
              </div>
            );
          })}

          {filtered.length === 0 && (
            <div className="text-center py-8 text-xs text-[var(--color-text-muted)]">
              No matching vehicle journeys found.
            </div>
          )}
        </div>
      </div>

      {/* Right Trajectory Breakdown Pane */}
      <div className="lg:col-span-2">
        {selectedJourney ? (
          <div className="classic-card p-6 bg-[var(--color-surface)] space-y-6">
            {/* Header info */}
            <div className="flex items-start justify-between pb-4 border-b border-[var(--color-border-subtle)]">
              <div>
                <span className="text-xs font-mono text-[var(--color-brown)] block mb-1">
                  JOURNEY #{selectedJourney.journey_id}
                </span>
                <h3 className="text-lg font-bold text-[var(--color-forest)] font-serif">
                  {selectedJourney.primary_plate || selectedJourney.global_vehicle_id}
                </h3>
                <p className="text-xs text-[var(--color-text-muted)]">
                  Vehicle Type: <strong className="capitalize">{selectedJourney.vehicle_class}</strong> • Color: <strong className="capitalize">{selectedJourney.color || 'white'}</strong>
                </p>
              </div>

              <div className="text-right space-y-1">
                <span className="badge-navy text-xs block">
                  TRIP DISTANCE: {selectedJourney.total_distance_km} KM
                </span>
                <span className="badge-gold text-xs block">
                  CORRIDOR SPEED: {selectedJourney.avg_speed_kmh} KM/H
                </span>
              </div>
            </div>

            {/* Trajectory Timeline */}
            <div>
              <h4 className="text-xs font-bold text-[var(--color-forest)] uppercase tracking-wider mb-4">
                Spatio-Temporal Camera Sequence & Verifications
              </h4>

              <div className="relative border-l-2 border-[var(--color-forest)] ml-3 pl-6 space-y-6">
                {selectedJourney.trajectory?.map((wp, idx) => {
                  return (
                    <div key={idx} className="relative">
                      {/* Node Bullet */}
                      <div className="absolute -left-[31px] top-1 w-4 h-4 rounded-full bg-[var(--color-surface)] border-2 border-[var(--color-forest)] flex items-center justify-center">
                        <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-forest)]" />
                      </div>

                      <div className="classic-card p-3 bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)]">
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-xs text-[var(--color-forest)]">
                              {wp.camera_id}
                            </span>
                            <span className="text-xs font-semibold text-[var(--color-text-main)]">
                              {wp.camera_name}
                            </span>
                          </div>
                          <span className="text-[11px] font-mono text-[var(--color-text-muted)] flex items-center gap-1">
                            <Clock className="w-3 h-3 text-[var(--color-brown)]" />
                            {new Date(wp.timestamp).toLocaleTimeString()}
                          </span>
                        </div>

                        <p className="text-xs text-[var(--color-text-muted)] mb-2">
                          {wp.intersection}
                        </p>

                        <div className="flex items-center gap-4 text-xs font-mono text-[var(--color-text-muted)]">
                          <span>Speed: <strong className="text-[var(--color-brown)]">{wp.speed_kmh} km/h</strong></span>
                          <span>Plate Conf: <strong className="text-[var(--color-forest)]">{Math.round(wp.plate_confidence * 100)}%</strong></span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ) : (
          <div className="classic-card h-96 flex flex-col items-center justify-center p-8 text-center text-[var(--color-text-muted)] bg-[var(--color-surface)]">
            <Route className="w-12 h-12 text-[var(--color-border-medium)] mb-3" />
            <h3 className="font-serif font-bold text-sm text-[var(--color-forest)] mb-1">
              Select a Vehicle Journey
            </h3>
            <p className="text-xs max-w-sm">
              Click any journey from the catalog to review its multi-camera transit verification, trajectory coordinates, and speeds.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
