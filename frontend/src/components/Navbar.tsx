import React from 'react';
import { Shield, Radio, Activity, Eye, Navigation, BarChart3, Bot, Settings, AlertTriangle, Camera } from 'lucide-react';
import type { SystemHealth } from '../types';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  systemHealth: SystemHealth | null;
  alertCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, systemHealth, alertCount }) => {
  const tabs = [
    { id: 'gis', label: 'GIS Urban Map', icon: Navigation },
    { id: 'cameras', label: 'Live Camera Grid', icon: Eye },
    { id: 'studio', label: 'AI Video & Webcam Studio', icon: Camera },
    { id: 'journeys', label: 'Journey Reconstructor', icon: Radio },
    { id: 'anpr', label: 'Indian ANPR & Watchlist', icon: Shield },
    { id: 'analytics', label: 'Traffic Intelligence', icon: BarChart3 },
    { id: 'assistant', label: 'Grounded Assistant', icon: Bot },
    { id: 'system', label: 'System & Benchmarks', icon: Settings },
  ];

  return (
    <header className="border-b border-[var(--color-border-subtle)] bg-[var(--color-surface)] sticky top-0 z-50 shadow-sm">
      {/* Top Heritage Branding Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-md bg-[var(--color-forest)] flex items-center justify-center text-white shadow-inner">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-wider font-serif text-[var(--color-forest)]">
                VISIONGUARD
              </h1>
              <span className="text-[10px] px-1.5 py-0.5 rounded font-mono font-bold bg-[var(--color-brown-subtle)] text-[var(--color-brown)] border border-[var(--color-border-subtle)]">
                SIH26127
              </span>
            </div>
            <p className="text-xs text-[var(--color-text-muted)]">
              AI-Powered Multi-Camera Urban Traffic Intelligence & ANPR Platform
            </p>
          </div>
        </div>

        {/* Telemetry Status Indicators */}
        <div className="hidden md:flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[var(--color-forest-subtle)] text-[var(--color-forest)] border border-[#C4DCC8]">
            <span className="w-2 h-2 rounded-full bg-[var(--color-forest)] animate-pulse"></span>
            <span>{systemHealth?.status || 'HEALTHY'}</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[var(--color-canvas-alt)] text-[var(--color-text-main)] border border-[var(--color-border-subtle)]">
            <Activity className="w-3.5 h-3.5 text-[var(--color-brown)]" />
            <span>{systemHealth?.active_fps || 30.0} FPS • {systemHealth?.average_inference_latency_ms || 18}ms</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[var(--color-navy-subtle)] text-[var(--color-navy)] border border-[#C5D6E5]">
            <span>CAMERAS: {systemHealth?.online_cameras || 6}/{systemHealth?.total_cameras || 6} ONLINE</span>
          </div>

          {alertCount > 0 && (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#FDF2F2] text-[#9B2C2C] border border-[#F5C6C6]">
              <AlertTriangle className="w-3.5 h-3.5 text-[#9B2C2C]" />
              <span>{alertCount} ACTIVE ALERTS</span>
            </div>
          )}
        </div>
      </div>

      {/* Classic Tab Navigation */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 border-t border-[var(--color-border-subtle)]">
        <nav className="flex space-x-1 sm:space-x-4 overflow-x-auto py-2">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap transition-colors ${
                  isActive
                    ? 'bg-[var(--color-forest)] text-white shadow-sm'
                    : 'text-[var(--color-text-muted)] hover:bg-[var(--color-canvas-alt)] hover:text-[var(--color-text-main)]'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-[#C5E1CE]' : ''}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
};
