import React, { useState } from 'react';
import type { Observation, WatchlistItem } from '../types';
import { Shield, ShieldAlert, Plus, CheckCircle, AlertOctagon, Trash2 } from 'lucide-react';

interface AnprWatchlistProps {
  observations: Observation[];
  watchlist: WatchlistItem[];
  onAddToWatchlist: (plate: string, desc: string, reason: string, priority: string) => Promise<void>;
  onRemoveFromWatchlist: (plate: string) => Promise<void>;
}

export const AnprWatchlist: React.FC<AnprWatchlistProps> = ({
  observations,
  watchlist,
  onAddToWatchlist,
  onRemoveFromWatchlist,
}) => {
  // Validator state
  const [testPlate, setTestPlate] = useState('DL 01 AB 1234');
  const [validationResult, setValidationResult] = useState<any>(null);

  // New Watchlist Form
  const [newPlate, setNewPlate] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newReason, setNewReason] = useState('');
  const [newPriority, setNewPriority] = useState('HIGH');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleValidate = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/anpr/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: testPlate }),
      });
      const data = await res.json();
      setValidationResult(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPlate || !newReason) return;
    setIsSubmitting(true);
    try {
      await onAddToWatchlist(newPlate, newDesc, newReason, newPriority);
      setNewPlate('');
      setNewDesc('');
      setNewReason('');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner: Indian License Plate Validation Studio */}
      <div className="classic-card p-5 bg-[var(--color-surface)] border border-[var(--color-border-subtle)]">
        <div className="flex items-start justify-between flex-wrap gap-4 mb-4">
          <div>
            <h2 className="text-sm font-bold text-[var(--color-forest)] font-serif flex items-center gap-2">
              <Shield className="w-4 h-4 text-[var(--color-brown)]" />
              INDIAN ANPR ENGINE & HSRP FORMAT VALIDATOR
            </h2>
            <p className="text-xs text-[var(--color-text-muted)]">
              Strict regex & state-code validation for Standard HSRP, Bharat (BH) Series, Commercial Yellow, and EV Green plates.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="text"
              value={testPlate}
              onChange={(e) => setTestPlate(e.target.value)}
              placeholder="e.g. DL 01 AB 1234 or 22 BH 1234 AA"
              className="px-3 py-1.5 text-xs rounded border border-[var(--color-border-subtle)] font-mono bg-[var(--color-canvas-alt)] focus:outline-none focus:border-[var(--color-forest)] uppercase"
            />
            <button
              onClick={handleValidate}
              className="btn-classic-forest text-xs"
            >
              Verify Plate Rules
            </button>
          </div>
        </div>

        {validationResult && (
          <div className="p-3 rounded bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)] text-xs flex items-center justify-between">
            <div className="flex items-center gap-3">
              {validationResult.is_valid_format ? (
                <CheckCircle className="w-5 h-5 text-[var(--color-forest)]" />
              ) : (
                <AlertOctagon className="w-5 h-5 text-red-600" />
              )}
              <div>
                <span className="font-mono font-bold text-sm text-[var(--color-text-main)]">
                  {validationResult.standardized_plate || validationResult.raw_text}
                </span>
                <span className="text-[10px] text-[var(--color-text-muted)] block">
                  Category: <strong className="text-[var(--color-brown)]">{validationResult.category}</strong>
                </span>
              </div>
            </div>

            <span className={validationResult.is_valid_format ? 'badge-forest' : 'badge-red'}>
              {validationResult.is_valid_format ? 'MORTH COMPLIANT HSRP' : 'INVALID PATTERN'}
            </span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Live ANPR Feed */}
        <div className="classic-card p-5 bg-[var(--color-surface)] space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[var(--color-border-subtle)]">
            <h3 className="text-sm font-bold text-[var(--color-forest)] font-serif">
              LIVE ANPR OBSERVATION FEED
            </h3>
            <span className="text-xs font-mono text-[var(--color-text-muted)]">
              {observations.length} RECENT SCANS
            </span>
          </div>

          <div className="space-y-2.5 max-h-[500px] overflow-y-auto pr-1">
            {observations.slice(0, 15).map((obs) => {
              return (
                <div
                  key={obs.id}
                  className="p-3 rounded border border-[var(--color-border-subtle)] bg-[var(--color-surface-hover)] flex items-center justify-between"
                >
                  <div className="flex items-center gap-3">
                    {/* Simulated High-Security Registration Plate graphic */}
                    <div className="px-2.5 py-1 bg-white border-2 border-black rounded shadow-sm flex items-center gap-1.5">
                      <span className="text-[8px] font-bold text-blue-800 tracking-tighter">IND</span>
                      <span className="font-mono font-bold text-xs tracking-wider text-black">
                        {obs.plate_text || 'UNREAD'}
                      </span>
                    </div>

                    <div>
                      <div className="text-xs font-medium text-[var(--color-text-main)]">
                        {obs.camera_name || obs.camera_id}
                      </div>
                      <div className="text-[10px] text-[var(--color-text-muted)]">
                        {obs.vehicle_class} • {obs.color} • {obs.estimated_speed} km/h
                      </div>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="badge-forest text-[10px]">
                      {Math.round((obs.plate_confidence || 0.95) * 100)}% CONF
                    </span>
                    <span className="text-[10px] text-[var(--color-text-faint)] block mt-1 font-mono">
                      {new Date(obs.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Security Watchlist & Alert Trigger */}
        <div className="classic-card p-5 bg-[var(--color-surface)] space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[var(--color-border-subtle)]">
            <h3 className="text-sm font-bold text-[var(--color-brown)] font-serif flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-red-600" />
              HOT-LIST / SECURITY WATCHLIST
            </h3>
            <span className="badge-red text-[10px]">{watchlist.length} TARGETS</span>
          </div>

          {/* Add to Watchlist Form */}
          <form onSubmit={handleAddSubmit} className="p-3 rounded bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)] space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <input
                type="text"
                value={newPlate}
                onChange={(e) => setNewPlate(e.target.value)}
                placeholder="Target Plate (e.g. DL 01 AB 1234)"
                className="px-2.5 py-1.5 text-xs rounded border border-[var(--color-border-subtle)] uppercase font-mono bg-[var(--color-surface)] focus:outline-none"
                required
              />
              <input
                type="text"
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                placeholder="Vehicle Desc (e.g. White Fortuner)"
                className="px-2.5 py-1.5 text-xs rounded border border-[var(--color-border-subtle)] bg-[var(--color-surface)] focus:outline-none"
              />
            </div>

            <div className="grid grid-cols-3 gap-2">
              <input
                type="text"
                value={newReason}
                onChange={(e) => setNewReason(e.target.value)}
                placeholder="Alert Reason / FIR Case #"
                className="col-span-2 px-2.5 py-1.5 text-xs rounded border border-[var(--color-border-subtle)] bg-[var(--color-surface)] focus:outline-none"
                required
              />
              <select
                value={newPriority}
                onChange={(e) => setNewPriority(e.target.value)}
                className="px-2 py-1.5 text-xs rounded border border-[var(--color-border-subtle)] bg-[var(--color-surface)] focus:outline-none"
              >
                <option value="CRITICAL">CRITICAL</option>
                <option value="HIGH">HIGH</option>
                <option value="MEDIUM">MEDIUM</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-classic-brown w-full text-xs justify-center py-1.5"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Enroll Target in Watchlist</span>
            </button>
          </form>

          {/* Watchlist Table */}
          <div className="space-y-2 max-h-[340px] overflow-y-auto pr-1">
            {watchlist.map((item) => (
              <div
                key={item.plate_number}
                className="p-3 rounded border border-[var(--color-border-subtle)] bg-[var(--color-surface)] flex items-start justify-between"
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono font-bold text-xs text-[var(--color-forest)]">
                      {item.plate_number}
                    </span>
                    <span className={item.priority === 'CRITICAL' ? 'badge-red' : 'badge-gold'}>
                      {item.priority}
                    </span>
                  </div>
                  <p className="text-xs text-[var(--color-text-main)] font-medium">
                    {item.vehicle_desc}
                  </p>
                  <p className="text-[11px] text-[var(--color-text-muted)]">
                    {item.reason}
                  </p>
                </div>

                <button
                  onClick={() => onRemoveFromWatchlist(item.plate_number)}
                  className="p-1 text-[var(--color-text-faint)] hover:text-red-600 rounded transition-colors"
                  title="Remove from Watchlist"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
