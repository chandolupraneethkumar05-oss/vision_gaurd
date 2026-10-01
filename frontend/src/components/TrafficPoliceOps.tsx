import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  FileText,
  Ambulance,
  Radio,
  CheckCircle2,
  Printer,
  X,
  CreditCard,
  Plus,
  RefreshCw,
  QrCode,
  MapPin,
  Sparkles
} from 'lucide-react';
import type { Camera, EChallan, GreenCorridor, PcrUnit } from '../types';
import { API_BASE } from '../config/api';

interface TrafficPoliceOpsProps {
  cameras: Camera[];
}

export const TrafficPoliceOps: React.FC<TrafficPoliceOpsProps> = ({ cameras }) => {
  const [activeSubTab, setActiveSubTab] = useState<'challans' | 'corridor' | 'pcr' | 'signals'>('challans');
  const [challans, setChallans] = useState<EChallan[]>([]);
  const [corridors, setCorridors] = useState<GreenCorridor[]>([]);
  const [pcrUnits, setPcrUnits] = useState<PcrUnit[]>([]);
  const [selectedChallan, setSelectedChallan] = useState<EChallan | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // New Challan Form State
  const [newPlate, setNewPlate] = useState('DL 01 AB 1234');
  const [newViolation, setNewViolation] = useState('OVERSPEEDING');
  const [newCameraId, setNewCameraId] = useState('CAM-01');
  const [newSpeed, setNewSpeed] = useState('74.5');

  // Green Corridor Form State
  const [corridorName, setCorridorName] = useState('AIIMS Trauma Emergency Corridor');
  const [corridorType, setCorridorType] = useState('AMBULANCE');
  const [corridorPlate, setCorridorPlate] = useState('DL 01 AM 9110');
  const [originCam, setOriginCam] = useState('CAM-01');
  const [destCam, setDestCam] = useState('CAM-06');

  // Load Initial Police Operational Data
  const fetchPoliceData = async () => {
    setIsLoading(true);
    try {
      const [chRes, gcRes, pcrRes] = await Promise.all([
        fetch(`${API_BASE}/api/police/challans`).then((r) => r.json()),
        fetch(`${API_BASE}/api/police/green-corridor`).then((r) => r.json()),
        fetch(`${API_BASE}/api/police/pcr-units`).then((r) => r.json()),
      ]);
      setChallans(chRes || []);
      setCorridors(gcRes || []);
      setPcrUnits(pcrRes || []);
    } catch (err) {
      console.error('Failed to fetch police ops data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPoliceData();
  }, []);

  const triggerSuccessAlert = (msg: string) => {
    setActionSuccess(msg);
    setTimeout(() => setActionSuccess(null), 4500);
  };

  // Issue New Challan
  const handleIssueChallan = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/police/challans/issue`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plate_number: newPlate,
          violation_type: newViolation,
          camera_id: newCameraId,
          recorded_speed: parseFloat(newSpeed) || 0.0,
          speed_limit: 50.0,
          officer_badge: 'DEL-TP-7429',
          evidence_notes: `Statutory e-challan recorded via AI Radar & ANPR system at ${newCameraId}`,
        }),
      });
      const data = await res.json();
      if (data.status === 'SUCCESS') {
        triggerSuccessAlert(`Official E-Challan ${data.challan.challan_no} issued for vehicle ${data.challan.plate_number}!`);
        fetchPoliceData();
      }
    } catch (err) {
      console.error('Failed to issue challan:', err);
    }
  };

  // Pay / Settle Challan
  const handlePayChallan = async (challanNo: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/police/challans/${challanNo}/pay`, { method: 'POST' });
      if (res.ok) {
        triggerSuccessAlert(`Challan ${challanNo} settled and recorded as PAID in National Parivahan Registry.`);
        fetchPoliceData();
        if (selectedChallan?.challan_no === challanNo) {
          setSelectedChallan((prev) => (prev ? { ...prev, status: 'PAID' } : null));
        }
      }
    } catch (err) {
      console.error('Failed to settle challan:', err);
    }
  };

  // Activate Green Corridor
  const handleActivateCorridor = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/police/green-corridor/activate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: corridorName,
          emergency_type: corridorType,
          vehicle_plate: corridorPlate,
          origin_cam: originCam,
          dest_cam: destCam,
        }),
      });
      const data = await res.json();
      if (data.status === 'ACTIVATED') {
        triggerSuccessAlert(`Emergency Green Corridor activated for ${corridorType} (${corridorPlate})! Traffic signals synchronized.`);
        fetchPoliceData();
      }
    } catch (err) {
      console.error('Failed to activate corridor:', err);
    }
  };

  // Deactivate Green Corridor
  const handleDeactivateCorridor = async (corridorId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/police/green-corridor/${corridorId}/deactivate`, { method: 'POST' });
      if (res.ok) {
        triggerSuccessAlert(`Corridor ${corridorId} closed. Signals reverted to dynamic network balance.`);
        fetchPoliceData();
      }
    } catch (err) {
      console.error('Failed to deactivate corridor:', err);
    }
  };

  // Dispatch PCR Intercept
  const handleDispatchPcr = async (unitId: string, targetPlate: string, targetJunction: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/police/pcr-units/${unitId}/dispatch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          unit_id: unitId,
          target_plate: targetPlate,
          target_junction: targetJunction,
          intercept_notes: 'Urgent tactical intercept instructed by Traffic Police Operations Command',
        }),
      });
      if (res.ok) {
        triggerSuccessAlert(`PCR Unit ${unitId} dispatched to intercept ${targetPlate} at ${targetJunction}!`);
        fetchPoliceData();
      }
    } catch (err) {
      console.error('Failed to dispatch PCR unit:', err);
    }
  };

  // Signal Flush Queue Override
  const handleSignalOverride = async (camId: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/police/signal-override`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          camera_id: camId,
          duration_sec: 45,
          reason: 'Manual Queue Flush by Traffic Controller Police',
        }),
      });
      if (res.ok) {
        triggerSuccessAlert(`Forced 45s Green Wave queue flush initiated on ${camId}!`);
      }
    } catch (err) {
      console.error('Failed to override signal:', err);
    }
  };

  const totalFines = challans.reduce((sum, c) => sum + c.fine_amount, 0);
  const activeCorridors = corridors.filter((c) => c.status === 'ACTIVE');

  return (
    <div className="space-y-6">
      {/* Top Police Ops Header */}
      <div className="classic-card p-5 bg-[var(--color-surface)] border border-[var(--color-border-subtle)] shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-lg bg-[var(--color-forest)] text-white flex items-center justify-center shadow-md">
              <ShieldAlert className="w-7 h-7 text-[#E5F5E8]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold font-serif text-[var(--color-forest)] tracking-wide">
                  TRAFFIC POLICE ENFORCEMENT & OPERATIONS CENTER
                </h2>
                <span className="badge-forest text-[10px] font-mono">DELHI TRAFFIC POLICE</span>
              </div>
              <p className="text-xs text-[var(--color-text-muted)]">
                Statutory E-Challan Issuance (Motor Vehicles Act 2019) • Emergency Green Corridor Dispatch • Tactical PCR Intercept
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={fetchPoliceData}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)] text-[var(--color-text-main)] hover:bg-[#EBE5D8]"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
              <span>Sync Ops State</span>
            </button>
          </div>
        </div>

        {/* Real-time KPI Stats Banner */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-4 border-t border-[var(--color-border-subtle)]">
          <div className="p-3 rounded bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)]">
            <span className="text-[10px] font-mono text-[var(--color-text-muted)] block">TOTAL E-CHALLANS ISSUED</span>
            <span className="text-xl font-bold font-serif text-[var(--color-forest)]">{challans.length}</span>
            <span className="text-[10px] text-[var(--color-text-muted)] block mt-0.5">₹{totalFines.toLocaleString('en-IN')} total penalties</span>
          </div>

          <div className="p-3 rounded bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)]">
            <span className="text-[10px] font-mono text-[var(--color-text-muted)] block">ACTIVE GREEN CORRIDORS</span>
            <div className="flex items-center gap-1.5">
              <span className={`w-2.5 h-2.5 rounded-full ${activeCorridors.length > 0 ? 'bg-emerald-600 animate-pulse' : 'bg-gray-400'}`}></span>
              <span className="text-xl font-bold font-serif text-emerald-800">{activeCorridors.length} ACTIVE</span>
            </div>
            <span className="text-[10px] text-[var(--color-text-muted)] block mt-0.5">Priority ambulance clearance</span>
          </div>

          <div className="p-3 rounded bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)]">
            <span className="text-[10px] font-mono text-[var(--color-text-muted)] block">PCR PATROL UNITS DEPLOYED</span>
            <span className="text-xl font-bold font-serif text-[var(--color-brown)]">{pcrUnits.length} UNITS</span>
            <span className="text-[10px] text-[var(--color-text-muted)] block mt-0.5">High-speed tactical intercept ready</span>
          </div>

          <div className="p-3 rounded bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)]">
            <span className="text-[10px] font-mono text-[var(--color-text-muted)] block">RADAR SPEED REGULATION</span>
            <span className="text-xl font-bold font-serif text-[var(--color-navy)]">50.0 km/h</span>
            <span className="text-[10px] text-[var(--color-text-muted)] block mt-0.5">Sec 183(1) MV Act Calibrated</span>
          </div>
        </div>
      </div>

      {/* Action Notification Alert */}
      {actionSuccess && (
        <div className="p-3 rounded-lg bg-[var(--color-forest-subtle)] border border-[#BCE2C4] text-[var(--color-forest)] text-xs flex items-center justify-between shadow-xs animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[var(--color-forest)] flex-shrink-0" />
            <span className="font-medium font-sans">{actionSuccess}</span>
          </div>
          <button onClick={() => setActionSuccess(null)} className="text-[var(--color-forest)] hover:opacity-75">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Sub-Tab Navigation Bar */}
      <div className="flex border-b border-[var(--color-border-subtle)] gap-2 overflow-x-auto">
        <button
          onClick={() => setActiveSubTab('challans')}
          className={`flex items-center gap-2 px-4 py-2 border-b-2 text-xs font-medium transition-colors whitespace-nowrap ${
            activeSubTab === 'challans'
              ? 'border-[var(--color-forest)] text-[var(--color-forest)] font-bold'
              : 'border-transparent text-[var(--color-text-muted)] hover:text-black'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>E-Challan Issuance Desk (MV Act 2019)</span>
        </button>

        <button
          onClick={() => setActiveSubTab('corridor')}
          className={`flex items-center gap-2 px-4 py-2 border-b-2 text-xs font-medium transition-colors whitespace-nowrap ${
            activeSubTab === 'corridor'
              ? 'border-[var(--color-forest)] text-[var(--color-forest)] font-bold'
              : 'border-transparent text-[var(--color-text-muted)] hover:text-black'
          }`}
        >
          <Ambulance className="w-4 h-4" />
          <span>Emergency Green Corridor Clearance</span>
        </button>

        <button
          onClick={() => setActiveSubTab('pcr')}
          className={`flex items-center gap-2 px-4 py-2 border-b-2 text-xs font-medium transition-colors whitespace-nowrap ${
            activeSubTab === 'pcr'
              ? 'border-[var(--color-forest)] text-[var(--color-forest)] font-bold'
              : 'border-transparent text-[var(--color-text-muted)] hover:text-black'
          }`}
        >
          <Radio className="w-4 h-4" />
          <span>PCR Patrol Units & Hotlist Intercept</span>
        </button>

        <button
          onClick={() => setActiveSubTab('signals')}
          className={`flex items-center gap-2 px-4 py-2 border-b-2 text-xs font-medium transition-colors whitespace-nowrap ${
            activeSubTab === 'signals'
              ? 'border-[var(--color-forest)] text-[var(--color-forest)] font-bold'
              : 'border-transparent text-[var(--color-text-muted)] hover:text-black'
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>Junction Signal Flush Override</span>
        </button>
      </div>

      {/* ========================================================================= */}
      {/* SUB-TAB 1: E-CHALLAN ISSUANCE DESK */}
      {/* ========================================================================= */}
      {activeSubTab === 'challans' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left 2 Cols: Challan Registry Table */}
          <div className="lg:col-span-2 space-y-4">
            <div className="classic-card overflow-hidden bg-[var(--color-surface)] border border-[var(--color-border-subtle)]">
              <div className="p-4 bg-[var(--color-canvas-alt)] border-b border-[var(--color-border-subtle)] flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-sm text-[var(--color-forest)] font-serif">
                    OFFICIAL E-CHALLAN REGISTRY
                  </h3>
                  <p className="text-xs text-[var(--color-text-muted)]">
                    Direct integration with MoRTH Parivahan National Portal and Court Adjudication Systems
                  </p>
                </div>
                <span className="text-xs font-mono text-[var(--color-text-muted)]">
                  {challans.length} Recorded
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#FAF7F0] border-b border-[var(--color-border-subtle)] font-mono text-[var(--color-text-muted)]">
                    <tr>
                      <th className="p-3">CHALLAN NO</th>
                      <th className="p-3">VEHICLE PLATE</th>
                      <th className="p-3">OFFENCE / SECTION</th>
                      <th className="p-3">FINE</th>
                      <th className="p-3">STATUS</th>
                      <th className="p-3 text-right">ACTION</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--color-border-subtle)] font-sans">
                    {challans.map((ch) => (
                      <tr key={ch.challan_no} className="hover:bg-[var(--color-canvas-alt)] transition-colors">
                        <td className="p-3 font-mono font-medium text-[var(--color-text-main)]">
                          {ch.challan_no}
                          <span className="block text-[10px] text-[var(--color-text-muted)]">{ch.camera_id} • {ch.intersection}</span>
                        </td>
                        <td className="p-3 font-mono font-bold">
                          <span className="inline-flex items-center px-2 py-0.5 rounded bg-amber-50 text-amber-900 border border-amber-300 font-mono text-xs">
                            <span className="text-[9px] mr-1 text-blue-700 font-bold">IND</span>
                            {ch.plate_number}
                          </span>
                        </td>
                        <td className="p-3">
                          <span className="font-semibold text-[var(--color-forest)] block">{ch.violation_type}</span>
                          <span className="text-[11px] text-[var(--color-text-muted)]">{ch.section_act}</span>
                        </td>
                        <td className="p-3 font-mono font-bold text-[var(--color-brown)]">
                          ₹{ch.fine_amount.toLocaleString('en-IN')}
                        </td>
                        <td className="p-3">
                          <span
                            className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                              ch.status === 'PAID'
                                ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                : 'bg-red-100 text-red-800 border border-red-300'
                            }`}
                          >
                            {ch.status}
                          </span>
                        </td>
                        <td className="p-3 text-right space-x-1.5 whitespace-nowrap">
                          <button
                            onClick={() => setSelectedChallan(ch)}
                            className="px-2.5 py-1 rounded bg-[var(--color-canvas-alt)] text-[var(--color-text-main)] hover:bg-[#E2DDD3] border border-[var(--color-border-subtle)] text-[11px] font-medium"
                          >
                            Notice
                          </button>
                          {ch.status !== 'PAID' && (
                            <button
                              onClick={() => handlePayChallan(ch.challan_no)}
                              className="px-2.5 py-1 rounded bg-emerald-700 text-white hover:bg-emerald-800 text-[11px] font-medium"
                            >
                              Settle
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Right Col: Instant E-Challan Issuance Form */}
          <div className="space-y-4">
            <div className="classic-card p-5 bg-[var(--color-surface)] border border-[var(--color-border-subtle)]">
              <div className="flex items-center gap-2 mb-3">
                <Plus className="w-4 h-4 text-[var(--color-forest)]" />
                <h3 className="font-bold text-sm text-[var(--color-forest)] font-serif">
                  ISSUE STATUTORY E-CHALLAN
                </h3>
              </div>
              <p className="text-xs text-[var(--color-text-muted)] mb-4 leading-relaxed">
                Empowered under Section 136A of Motor Vehicles (Amendment) Act 2019 for Electronic Monitoring & Enforcement.
              </p>

              <form onSubmit={handleIssueChallan} className="space-y-3 text-xs">
                <div>
                  <label className="block font-medium text-[var(--color-text-main)] mb-1">
                    Vehicle Number Plate:
                  </label>
                  <input
                    type="text"
                    value={newPlate}
                    onChange={(e) => setNewPlate(e.target.value.toUpperCase())}
                    placeholder="e.g. DL 01 AB 1234"
                    className="w-full px-3 py-1.5 rounded bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)] font-mono text-sm uppercase focus:outline-none focus:border-[var(--color-forest)]"
                    required
                  />
                </div>

                <div>
                  <label className="block font-medium text-[var(--color-text-main)] mb-1">
                    Offence / Violation Category:
                  </label>
                  <select
                    value={newViolation}
                    onChange={(e) => setNewViolation(e.target.value)}
                    className="w-full px-3 py-1.5 rounded bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)] text-xs focus:outline-none focus:border-[var(--color-forest)]"
                  >
                    <option value="OVERSPEEDING">Sec 183(1) - Overspeeding (Fine: ₹2,000)</option>
                    <option value="RED_LIGHT_JUMP">Sec 184 - Red Light Jump & Stop Line (Fine: ₹5,000)</option>
                    <option value="NO_HELMET">Sec 194D - No Helmet on Two-Wheeler (Fine: ₹1,000)</option>
                    <option value="WRONG_WAY">Sec 184 - Dangerous / Wrong-Way Driving (Fine: ₹5,000)</option>
                    <option value="DANGEROUS_DRIVING">Sec 184 - Reckless / Zigzag Maneuver (Fine: ₹5,000)</option>
                    <option value="TRIPLE_RIDING">Sec 194C - Triple Riding on Two-Wheeler (Fine: ₹1,000)</option>
                  </select>
                </div>

                <div>
                  <label className="block font-medium text-[var(--color-text-main)] mb-1">
                    Enforcement Camera Junction:
                  </label>
                  <select
                    value={newCameraId}
                    onChange={(e) => setNewCameraId(e.target.value)}
                    className="w-full px-3 py-1.5 rounded bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)] text-xs focus:outline-none focus:border-[var(--color-forest)]"
                  >
                    {cameras.map((c) => (
                      <option key={c.camera_id} value={c.camera_id}>
                        {c.camera_id}: {c.name} ({c.intersection})
                      </option>
                    ))}
                  </select>
                </div>

                {newViolation === 'OVERSPEEDING' && (
                  <div>
                    <label className="block font-medium text-[var(--color-text-main)] mb-1">
                      Recorded Radar Speed (km/h):
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      value={newSpeed}
                      onChange={(e) => setNewSpeed(e.target.value)}
                      className="w-full px-3 py-1.5 rounded bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)] font-mono text-xs focus:outline-none focus:border-[var(--color-forest)]"
                    />
                    <span className="text-[10px] text-[var(--color-text-muted)] mt-0.5 block">
                      Corridor Speed Limit: 50.0 km/h (Excess: +{Math.max(0, parseFloat(newSpeed) - 50).toFixed(1)} km/h)
                    </span>
                  </div>
                )}

                <div className="pt-2">
                  <button
                    type="submit"
                    className="w-full py-2 px-4 rounded bg-[var(--color-forest)] text-white font-medium hover:bg-opacity-90 transition-opacity shadow-xs flex items-center justify-center gap-2"
                  >
                    <ShieldAlert className="w-4 h-4 text-[#D8EEDC]" />
                    <span>Issue E-Challan & Send Notice</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* SUB-TAB 2: EMERGENCY GREEN CORRIDOR CLEARANCE */}
      {/* ========================================================================= */}
      {activeSubTab === 'corridor' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div className="classic-card p-5 bg-[var(--color-surface)] border border-[var(--color-border-subtle)]">
              <div className="flex items-center justify-between pb-3 border-b border-[var(--color-border-subtle)] mb-4">
                <div>
                  <h3 className="font-bold text-sm text-[var(--color-forest)] font-serif">
                    ACTIVE EMERGENCY CORRIDORS
                  </h3>
                  <p className="text-xs text-[var(--color-text-muted)]">
                    Dynamic continuous green wave signal coordination for hospital ambulances and emergency response vehicles
                  </p>
                </div>
                <span className="badge-forest text-xs">{activeCorridors.length} ACTIVE</span>
              </div>

              {activeCorridors.length === 0 ? (
                <div className="p-8 text-center text-xs text-[var(--color-text-muted)] bg-[var(--color-canvas-alt)] rounded border border-dashed border-[var(--color-border-subtle)]">
                  <Ambulance className="w-8 h-8 text-[var(--color-forest)] mx-auto mb-2 opacity-60" />
                  No emergency green corridors currently activated. All traffic signals are operating in adaptive equilibrium.
                </div>
              ) : (
                <div className="space-y-4">
                  {activeCorridors.map((c) => (
                    <div
                      key={c.corridor_id}
                      className="p-4 rounded-lg bg-emerald-50 border-2 border-emerald-500 shadow-sm"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-emerald-200 mb-3">
                        <div className="flex items-center gap-2">
                          <span className="w-3 h-3 rounded-full bg-emerald-600 animate-ping"></span>
                          <span className="font-bold text-sm text-emerald-900 font-serif">{c.name}</span>
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-200 text-emerald-900 font-bold">
                            {c.emergency_type}
                          </span>
                        </div>
                        <button
                          onClick={() => handleDeactivateCorridor(c.corridor_id)}
                          className="px-3 py-1 rounded bg-red-700 text-white text-xs font-medium hover:bg-red-800 transition-colors shadow-2xs"
                        >
                          Deactivate Corridor
                        </button>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs mb-3 font-mono">
                        <div>
                          <span className="text-[10px] text-emerald-700 block">VEHICLE PLATE</span>
                          <strong className="text-emerald-950">{c.vehicle_plate}</strong>
                        </div>
                        <div>
                          <span className="text-[10px] text-emerald-700 block">ORIGIN / DESTINATION</span>
                          <strong className="text-emerald-950">{c.origin_cam} ➔ {c.dest_cam}</strong>
                        </div>
                        <div>
                          <span className="text-[10px] text-emerald-700 block">STATUS</span>
                          <strong className="text-emerald-700">CONTINUOUS GREEN WAVE</strong>
                        </div>
                      </div>

                      <div className="p-2.5 rounded bg-emerald-100/70 border border-emerald-300 text-xs">
                        <span className="font-bold text-emerald-900 block mb-1">SYNCHRONIZED GREEN CORRIDOR ROUTE:</span>
                        <div className="flex flex-wrap items-center gap-2 text-xs font-mono text-emerald-950">
                          {c.route.map((node, i) => (
                            <React.Fragment key={node}>
                              <span className="px-2 py-1 rounded bg-white shadow-2xs border border-emerald-400 font-bold">
                                {node} (GREEN 🟢)
                              </span>
                              {i < c.route.length - 1 && <span className="font-bold text-emerald-700">➔</span>}
                            </React.Fragment>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Col: 1-Click Activate Corridor Form */}
          <div className="space-y-4">
            <div className="classic-card p-5 bg-[var(--color-surface)] border border-[var(--color-border-subtle)]">
              <div className="flex items-center gap-2 mb-3">
                <Ambulance className="w-5 h-5 text-[var(--color-forest)]" />
                <h3 className="font-bold text-sm text-[var(--color-forest)] font-serif">
                  CLEAR EMERGENCY CORRIDOR
                </h3>
              </div>
              <p className="text-xs text-[var(--color-text-muted)] mb-4 leading-relaxed">
                Immediately overrides automated signal timers to force all signals green along the selected corridor.
              </p>

              <form onSubmit={handleActivateCorridor} className="space-y-3 text-xs">
                <div>
                  <label className="block font-medium text-[var(--color-text-main)] mb-1">
                    Corridor Mission Name:
                  </label>
                  <input
                    type="text"
                    value={corridorName}
                    onChange={(e) => setCorridorName(e.target.value)}
                    className="w-full px-3 py-1.5 rounded bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)] text-xs focus:outline-none focus:border-[var(--color-forest)]"
                    required
                  />
                </div>

                <div>
                  <label className="block font-medium text-[var(--color-text-main)] mb-1">
                    Emergency Mission Type:
                  </label>
                  <select
                    value={corridorType}
                    onChange={(e) => setCorridorType(e.target.value)}
                    className="w-full px-3 py-1.5 rounded bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)] text-xs focus:outline-none focus:border-[var(--color-forest)]"
                  >
                    <option value="AMBULANCE">Ambulance (Life Support & ICU)</option>
                    <option value="ORGAN_TRANSPLANT">Live Human Organ Conveyance</option>
                    <option value="FIRE_BRIGADE">Fire & Rescue First Responder</option>
                    <option value="VIP_CONVOY">High Security VIP Movement</option>
                  </select>
                </div>

                <div>
                  <label className="block font-medium text-[var(--color-text-main)] mb-1">
                    Vehicle Number / Call Sign:
                  </label>
                  <input
                    type="text"
                    value={corridorPlate}
                    onChange={(e) => setCorridorPlate(e.target.value.toUpperCase())}
                    className="w-full px-3 py-1.5 rounded bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)] font-mono text-xs uppercase focus:outline-none focus:border-[var(--color-forest)]"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block font-medium text-[var(--color-text-main)] mb-1">
                      Origin Camera:
                    </label>
                    <select
                      value={originCam}
                      onChange={(e) => setOriginCam(e.target.value)}
                      className="w-full px-2 py-1.5 rounded bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)] text-xs font-mono"
                    >
                      {cameras.map((c) => (
                        <option key={c.camera_id} value={c.camera_id}>
                          {c.camera_id}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block font-medium text-[var(--color-text-main)] mb-1">
                      Destination Camera:
                    </label>
                    <select
                      value={destCam}
                      onChange={(e) => setDestCam(e.target.value)}
                      className="w-full px-2 py-1.5 rounded bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)] text-xs font-mono"
                    >
                      {cameras.map((c) => (
                        <option key={c.camera_id} value={c.camera_id}>
                          {c.camera_id}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    className="w-full py-2.5 px-4 rounded bg-emerald-800 text-white font-bold hover:bg-emerald-900 transition-colors shadow-sm flex items-center justify-center gap-2"
                  >
                    <Ambulance className="w-4 h-4 text-emerald-200" />
                    <span>FORCE ALL-GREEN CORRIDOR WAVE</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* SUB-TAB 3: PCR PATROL UNITS & HOTLIST INTERCEPT */}
      {/* ========================================================================= */}
      {activeSubTab === 'pcr' && (
        <div className="space-y-4">
          <div className="classic-card p-5 bg-[var(--color-surface)] border border-[var(--color-border-subtle)]">
            <div className="flex items-center justify-between pb-3 border-b border-[var(--color-border-subtle)] mb-4">
              <div>
                <h3 className="font-bold text-sm text-[var(--color-forest)] font-serif">
                  ACTIVE POLICE CONTROL ROOM (PCR) PATROL UNITS
                </h3>
                <p className="text-xs text-[var(--color-text-muted)]">
                  Tactical field deployment for hotlisted stolen vehicles and hit-and-run interdiction
                </p>
              </div>
              <span className="badge-forest text-xs">{pcrUnits.length} UNITS ONLINE</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {pcrUnits.map((u) => (
                <div
                  key={u.unit_id}
                  className="p-4 rounded-lg bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)] space-y-2 shadow-2xs"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 font-bold font-mono text-sm text-[var(--color-forest)]">
                      <Radio className="w-4 h-4 text-[var(--color-brown)]" />
                      <span>{u.call_sign}</span>
                    </div>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                        u.status === 'DISPATCHED_INTERCEPT'
                          ? 'bg-red-100 text-red-800 border border-red-300 animate-pulse'
                          : 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                      }`}
                    >
                      {u.status}
                    </span>
                  </div>

                  <div className="text-xs text-[var(--color-text-main)]">
                    <strong>Officer:</strong> {u.officer_in_charge}
                  </div>

                  <div className="text-xs text-[var(--color-text-muted)] font-mono flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-[var(--color-forest)]" />
                    <span>Sector: {u.current_junction}</span>
                  </div>

                  <div className="pt-2 border-t border-[var(--color-border-subtle)]">
                    <button
                      onClick={() => handleDispatchPcr(u.unit_id, 'DL 01 AB 1234', 'CAM-02')}
                      className="w-full py-1.5 px-2 rounded bg-[var(--color-forest)] text-white text-[11px] font-medium hover:bg-opacity-90 transition-opacity"
                    >
                      Dispatch Intercept ➔ CAM-02
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* SUB-TAB 4: JUNCTION SIGNAL QUEUE OVERRIDE */}
      {/* ========================================================================= */}
      {activeSubTab === 'signals' && (
        <div className="space-y-4">
          <div className="classic-card p-5 bg-[var(--color-surface)] border border-[var(--color-border-subtle)]">
            <div className="flex items-center justify-between pb-3 border-b border-[var(--color-border-subtle)] mb-4">
              <div>
                <h3 className="font-bold text-sm text-[var(--color-forest)] font-serif">
                  MANUAL SIGNAL QUEUE FLUSH CONTROLS
                </h3>
                <p className="text-xs text-[var(--color-text-muted)]">
                  When unexpected bottleneck surges or accidents occur, traffic police can trigger a manual 45-second queue flush
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {cameras.map((cam) => (
                <div
                  key={cam.camera_id}
                  className="p-4 rounded-lg bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)] space-y-2 shadow-2xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold font-mono text-sm text-[var(--color-forest)]">
                      {cam.camera_id}
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded font-bold bg-amber-100 text-amber-800 border border-amber-300">
                      LOS: {cam.metrics?.level_of_service || 'B'}
                    </span>
                  </div>

                  <h4 className="font-semibold text-xs text-[var(--color-text-main)]">
                    {cam.name}
                  </h4>
                  <p className="text-[11px] text-[var(--color-text-muted)]">
                    {cam.intersection} • Flow: {cam.metrics?.flow_rate_vph || 380} vph
                  </p>

                  <div className="pt-2 border-t border-[var(--color-border-subtle)]">
                    <button
                      onClick={() => handleSignalOverride(cam.camera_id)}
                      className="w-full py-1.5 px-3 rounded bg-emerald-800 text-white text-xs font-medium hover:bg-emerald-900 transition-colors shadow-2xs flex items-center justify-center gap-1.5"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-emerald-200" />
                      <span>Trigger 45s Green Wave Flush</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* OFFICIAL GOVERNMENT OF INDIA E-CHALLAN MODAL NOTICE */}
      {/* ========================================================================= */}
      {selectedChallan && (
        <div className="fixed inset-0 z-[9999] bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-2xl max-w-xl w-full border-2 border-[var(--color-forest)] overflow-hidden animate-in fade-in zoom-in-95">
            {/* Official Notice Header */}
            <div className="bg-[var(--color-forest)] text-white p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded bg-white text-[var(--color-forest)] flex items-center justify-center font-bold">
                  <ShieldAlert className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="font-serif font-bold text-base tracking-wide">
                    DELHI TRAFFIC POLICE
                  </h3>
                  <p className="text-[11px] text-[#C5E1CE] font-mono">
                    STATUTORY E-CHALLAN NOTICE (MV ACT 2019)
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedChallan(null)}
                className="text-white hover:text-red-200 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Official Document Body */}
            <div className="p-6 space-y-4 text-xs font-sans bg-[#FBF9F5]">
              <div className="flex items-center justify-between pb-3 border-b border-[var(--color-border-subtle)] font-mono text-[11px]">
                <div>
                  <span className="text-[var(--color-text-muted)] block text-[10px]">NOTICE REFERENCE NO.</span>
                  <strong>{selectedChallan.challan_no}</strong>
                </div>
                <div className="text-right">
                  <span className="text-[var(--color-text-muted)] block text-[10px]">DATE & TIME</span>
                  <strong>{new Date(selectedChallan.timestamp).toLocaleString()}</strong>
                </div>
              </div>

              {/* Vehicle & Location Identification */}
              <div className="grid grid-cols-2 gap-4 p-3 rounded bg-white border border-[var(--color-border-subtle)] font-mono">
                <div>
                  <span className="text-[10px] text-[var(--color-text-muted)] block">VEHICLE REGISTRATION</span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded bg-amber-50 text-amber-950 font-bold border border-amber-300 text-sm mt-0.5">
                    <span className="text-[10px] mr-1 text-blue-700 font-bold">IND</span>
                    {selectedChallan.plate_number}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-[var(--color-text-muted)] block">ENFORCEMENT LOCATION</span>
                  <strong className="text-[var(--color-forest)] text-xs block mt-1">
                    {selectedChallan.intersection} ({selectedChallan.camera_id})
                  </strong>
                </div>
              </div>

              {/* Violation Details & Legal Section */}
              <div className="p-3.5 rounded bg-red-50 border border-red-200 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-red-900 uppercase">
                    OFFENCE: {selectedChallan.violation_type}
                  </span>
                  <span className="font-bold text-red-900 font-mono text-sm">
                    STATUTORY PENALTY: ₹{selectedChallan.fine_amount.toLocaleString('en-IN')}
                  </span>
                </div>
                <div className="text-xs text-red-950 font-medium">
                  <strong>Section of Law:</strong> {selectedChallan.section_act}
                </div>
                <p className="text-[11px] text-red-800 leading-relaxed">
                  {selectedChallan.evidence_notes}
                </p>
              </div>

              {/* QR Code & Digital Verification */}
              <div className="flex items-center gap-4 p-3 rounded bg-white border border-[var(--color-border-subtle)]">
                <div className="w-16 h-16 bg-[var(--color-canvas-alt)] rounded border border-[var(--color-border-subtle)] flex items-center justify-center flex-shrink-0">
                  <QrCode className="w-12 h-12 text-[var(--color-forest)]" />
                </div>
                <div className="text-[11px] text-[var(--color-text-muted)] space-y-1">
                  <span className="font-bold text-[var(--color-text-main)] block">VERIFIED DIGITAL EVIDENCE</span>
                  <p>
                    Captured via high-definition calibrated camera tracking sensor. Certified under Indian Evidence Act 65B.
                  </p>
                  <p className="font-mono text-[10px]">
                    Pay online at: <span className="underline text-blue-700">echallan.parivahan.gov.in</span>
                  </p>
                </div>
              </div>

              {/* Footer Actions */}
              <div className="flex items-center justify-between pt-3 border-t border-[var(--color-border-subtle)]">
                <button
                  onClick={() => window.print()}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[var(--color-canvas-alt)] border border-[var(--color-border-subtle)] text-xs text-[var(--color-text-main)] hover:bg-[#EBE5D8]"
                >
                  <Printer className="w-3.5 h-3.5" />
                  <span>Print Official Notice</span>
                </button>

                <div className="flex items-center gap-2">
                  {selectedChallan.status !== 'PAID' ? (
                    <button
                      onClick={() => handlePayChallan(selectedChallan.challan_no)}
                      className="flex items-center gap-1.5 px-4 py-1.5 rounded bg-emerald-700 text-white text-xs font-bold hover:bg-emerald-800 transition-colors shadow-xs"
                    >
                      <CreditCard className="w-3.5 h-3.5" />
                      <span>Mark as Paid (Parivahan)</span>
                    </button>
                  ) : (
                    <span className="px-3 py-1 rounded bg-emerald-100 text-emerald-800 font-bold font-mono text-xs border border-emerald-300">
                      SETTLED & PAID
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
