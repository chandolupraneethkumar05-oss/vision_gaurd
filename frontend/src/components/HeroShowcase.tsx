import React, { useState } from 'react';
import {
  ShieldAlert,
  Navigation,
  Eye,
  Camera,
  Radio,
  BarChart3,
  Bot,
  Ambulance,
  Activity,
  Zap,
  ChevronDown,
  ChevronUp,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  Gauge
} from 'lucide-react';
import type { SystemHealth, NetworkAnalytics } from '../types';

interface HeroShowcaseProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  systemHealth: SystemHealth | null;
  analytics: NetworkAnalytics | null;
  alertCount: number;
}

export const HeroShowcase: React.FC<HeroShowcaseProps> = ({
  activeTab,
  setActiveTab,
  systemHealth,
  analytics,
  alertCount,
}) => {
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);

  const featurePills = [
    {
      id: 'gis',
      title: 'GIS Urban Map',
      desc: 'Interactive New Delhi Grid & Corridors',
      icon: Navigation,
      color: 'from-emerald-700 to-emerald-950',
      border: 'border-emerald-500/40',
      badge: 'GIS-Active',
      tag: 'Spatial Network',
    },
    {
      id: 'police',
      title: 'Police Ops & Challan',
      desc: 'MV Act 2019 Fines & Emergency Clearance',
      icon: ShieldAlert,
      color: 'from-amber-700 to-amber-950',
      border: 'border-amber-500/50',
      badge: 'Enforcement Desk',
      tag: 'Statutory Law',
    },
    {
      id: 'cameras',
      title: 'Live Camera Grid',
      desc: 'Synchronized 6-Intersection Surveillance',
      icon: Eye,
      color: 'from-sky-800 to-sky-950',
      border: 'border-sky-500/40',
      badge: '6 Cameras HD',
      tag: 'Multi-Stream',
    },
    {
      id: 'studio',
      title: 'AI Video & ANPR Studio',
      desc: 'YOLOv8 Detection, Video Scrubber & Webcam',
      icon: Camera,
      color: 'from-teal-800 to-teal-950',
      border: 'border-teal-500/40',
      badge: 'Deep Learning',
      tag: 'CV Studio',
    },
    {
      id: 'journeys',
      title: 'Journey Reconstructor',
      desc: 'Cross-Camera Spatial-Temporal Re-ID',
      icon: Radio,
      color: 'from-stone-700 to-stone-900',
      border: 'border-amber-400/30',
      badge: 'Multi-Hop Tracks',
      tag: 'Global Identity',
    },
    {
      id: 'analytics',
      title: 'Traffic Intelligence',
      desc: '24-Hour Trends, O-D Matrix & Congestion',
      icon: BarChart3,
      color: 'from-blue-900 to-indigo-950',
      border: 'border-blue-500/40',
      badge: 'O-D Flow Matrix',
      tag: 'Predictive ML',
    },
    {
      id: 'assistant',
      title: 'Grounded AI Assistant',
      desc: 'Zero-Hallucination Query Engine',
      icon: Bot,
      color: 'from-indigo-900 to-slate-950',
      border: 'border-indigo-500/40',
      badge: '100% Factual',
      tag: 'Database NLP',
    },
  ];

  return (
    <div className="relative mb-6 rounded-2xl overflow-hidden border border-[var(--color-border-subtle)] shadow-xl transition-all duration-300">
      {/* Background Cinematic Visual with High-Tech Light Trails */}
      <div
        className="absolute inset-0 bg-cover bg-center transition-transform duration-700 scale-100 hover:scale-102"
        style={{ backgroundImage: "url('/hero-traffic.jpg')" }}
      >
        {/* Layered Gradient Glass Overlay for Perfect Text Readability and Glowing Aesthetic */}
        <div className="absolute inset-0 bg-gradient-to-r from-[#07131E]/95 via-[#0A1F13]/90 to-[#0A1526]/85 backdrop-blur-[1.5px]"></div>
      </div>

      {/* Decorative Neon Grid Lines & Ambient Lighting Glow */}
      <div className="absolute -top-24 -left-24 w-96 h-96 bg-emerald-500/15 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-amber-500/15 rounded-full blur-3xl pointer-events-none"></div>

      {/* Content Container */}
      <div className="relative z-10 p-6 md:p-8 text-white">
        {/* Top Header Status & Collapse Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-white/15">
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-400/40 shadow-inner">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              <span>LIVE URBAN COMMAND ENGINE ACTIVE</span>
            </span>

            <span className="hidden sm:inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-mono bg-white/10 text-neutral-300 border border-white/10">
              <Sparkles className="w-3 h-3 text-amber-400" />
              <span>SIH26127 ARCHITECTURE</span>
            </span>

            <span className="hidden md:inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-mono bg-white/10 text-neutral-300 border border-white/10">
              <span>NEW DELHI URBAN CORRIDOR</span>
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-mono bg-white/10 hover:bg-white/20 text-neutral-200 border border-white/20 transition-colors"
            >
              {isCollapsed ? (
                <>
                  <span>Expand Overview</span>
                  <ChevronDown className="w-3.5 h-3.5" />
                </>
              ) : (
                <>
                  <span>Compact View</span>
                  <ChevronUp className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </div>

        {/* Hero Title & Sub-headline */}
        <div className="mt-6 max-w-4xl space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold tracking-widest uppercase text-emerald-400">
              Autonomous Smart City Traffic Operations
            </span>
          </div>

          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight font-serif text-white leading-tight drop-shadow-md">
            Next-Generation Multi-Camera Traffic Intelligence & Enforcement Command
          </h2>

          <p className="text-xs sm:text-sm text-neutral-300 leading-relaxed max-w-3xl font-sans">
            Grounded in rigorous spatio-temporal road graph topology to eliminate cross-camera false hops. 
            Real-time YOLOv8 vehicle detection, high-accuracy Indian HSRP ANPR, automated statutory E-Challan generation under the Motor Vehicles Act 2019, and 1-click Emergency Green Corridor clearance.
          </p>
        </div>

        {/* Expandable Command Center Showcase & Fast Launchpad */}
        {!isCollapsed && (
          <div className="mt-8 space-y-6 animate-in fade-in duration-300">
            {/* Live KPI Telemetry Strip */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3.5 rounded-xl bg-black/40 backdrop-blur-md border border-white/15 shadow-inner">
                <div className="flex items-center justify-between text-neutral-400 text-xs font-mono mb-1">
                  <span>CORRIDOR FLOW</span>
                  <Activity className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="text-xl sm:text-2xl font-bold font-serif text-white">
                  {analytics?.network_total_flow_vph || 2480}{' '}
                  <span className="text-xs font-normal text-emerald-400 font-sans">vph</span>
                </div>
                <div className="text-[10px] text-neutral-400 mt-1">Across 6 Smart Camera Intersections</div>
              </div>

              <div className="p-3.5 rounded-xl bg-black/40 backdrop-blur-md border border-white/15 shadow-inner">
                <div className="flex items-center justify-between text-neutral-400 text-xs font-mono mb-1">
                  <span>AVG ARTERIAL SPEED</span>
                  <Gauge className="w-4 h-4 text-amber-400" />
                </div>
                <div className="text-xl sm:text-2xl font-bold font-serif text-white">
                  {analytics?.network_average_speed || 41.5}{' '}
                  <span className="text-xs font-normal text-amber-400 font-sans">km/h</span>
                </div>
                <div className="text-[10px] text-neutral-400 mt-1">Speed Limit: 50.0 km/h Calibrated</div>
              </div>

              <div className="p-3.5 rounded-xl bg-black/40 backdrop-blur-md border border-white/15 shadow-inner">
                <div className="flex items-center justify-between text-neutral-400 text-xs font-mono mb-1">
                  <span>AI INFERENCE SPEED</span>
                  <Zap className="w-4 h-4 text-sky-400" />
                </div>
                <div className="text-xl sm:text-2xl font-bold font-serif text-white">
                  {systemHealth?.active_fps || 30.0}{' '}
                  <span className="text-xs font-normal text-sky-400 font-sans">FPS</span>
                </div>
                <div className="text-[10px] text-neutral-400 mt-1">
                  Latency: {systemHealth?.average_inference_latency_ms || 18}ms (Edge CPU Ready)
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-black/40 backdrop-blur-md border border-white/15 shadow-inner">
                <div className="flex items-center justify-between text-neutral-400 text-xs font-mono mb-1">
                  <span>ENFORCEMENT ALERTS</span>
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="text-xl sm:text-2xl font-bold font-serif text-amber-400">
                  {alertCount || 3}{' '}
                  <span className="text-xs font-normal text-neutral-300 font-sans">Infractions</span>
                </div>
                <div className="text-[10px] text-neutral-400 mt-1">Statutory Citations (MV Act 2019)</div>
              </div>
            </div>

            {/* Interactive Feature Launch Cards */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-mono uppercase tracking-wider text-neutral-300 font-bold flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  <span>Direct Command Launchpad (Click to Explore)</span>
                </span>
                <span className="text-[11px] font-mono text-neutral-400 hidden sm:inline">
                  Interactive Module Switcher
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {featurePills.map((p) => {
                  const Icon = p.icon;
                  const isCurrent = activeTab === p.id;
                  return (
                    <button
                      key={p.id}
                      onClick={() => setActiveTab(p.id)}
                      className={`text-left p-3.5 rounded-xl border transition-all duration-200 group relative overflow-hidden ${
                        isCurrent
                          ? `bg-gradient-to-br ${p.color} ${p.border} ring-2 ring-emerald-400/80 shadow-lg -translate-y-0.5`
                          : 'bg-black/40 hover:bg-black/60 border-white/15 hover:border-white/30'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div
                          className={`w-9 h-9 rounded-lg flex items-center justify-center transition-transform group-hover:scale-110 ${
                            isCurrent
                              ? 'bg-white text-emerald-950 font-bold shadow-md'
                              : 'bg-white/10 text-white border border-white/15'
                          }`}
                        >
                          <Icon className="w-5 h-5" />
                        </div>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/10 text-neutral-200 border border-white/10">
                          {p.badge}
                        </span>
                      </div>

                      <div className="font-serif font-bold text-sm text-white group-hover:text-emerald-300 transition-colors">
                        {p.title}
                      </div>
                      <div className="text-[11px] text-neutral-300 mt-1 line-clamp-1">
                        {p.desc}
                      </div>

                      {isCurrent && (
                        <div className="mt-2.5 flex items-center gap-1 text-[10px] font-mono text-emerald-300 font-bold">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>CURRENT ACTIVE WORKSPACE</span>
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Quick Emergency Action Banner */}
            <div className="p-3 rounded-xl bg-gradient-to-r from-emerald-950/80 via-emerald-900/60 to-black/80 border border-emerald-500/40 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center flex-shrink-0 border border-emerald-400/30">
                  <Ambulance className="w-4 h-4 animate-pulse" />
                </div>
                <div>
                  <span className="font-bold text-emerald-300 block font-serif">
                    EMERGENCY VEHICLE TRANSIT ACTIVE
                  </span>
                  <span className="text-[11px] text-neutral-300">
                    Ambulance clearance protocol ready. Route signals synchronize automatically along the corridor.
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2 whitespace-nowrap">
                <button
                  onClick={() => setActiveTab('police')}
                  className="px-3 py-1.5 rounded-md bg-emerald-700 hover:bg-emerald-600 text-white font-semibold text-xs transition-colors shadow-xs"
                >
                  Manage Corridors & Challans ➔
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
