'use client';

import React, { useState, useEffect, useMemo } from 'react';
import ModelSelector from './ModelSelector';
import { apiClient } from '@/lib/api';

interface SidebarProps {
  isCollapsed?: boolean;
  onToggle?: () => void;
}

export default function Sidebar({ isCollapsed = false, onToggle }: SidebarProps) {
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const [lawsInfo, setLawsInfo] = useState<{ count: number; updated_at: string | null; laws: string[] } | null>(null);
  const [lawsExpanded, setLawsExpanded] = useState(false);
  const [lawsSearch, setLawsSearch] = useState('');

  // Use external state if provided, otherwise use internal state
  const collapsed = isCollapsed !== undefined ? isCollapsed : internalCollapsed;
  const toggle = useMemo(() => onToggle || (() => setInternalCollapsed(!internalCollapsed)), [onToggle]);

  useEffect(() => {
    apiClient.fetchLaws().then(data => {
      if (data.count > 0) setLawsInfo(data);
    });
  }, []);

  // Close sidebar on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !collapsed) {
        toggle();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [collapsed, toggle]);

  return (
    <>
      {/* Backdrop */}
      {!collapsed && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 transition-opacity duration-300"
          onClick={toggle}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed left-0 top-0 h-screen bg-white/95 
        backdrop-blur-md border-r border-slate-200/60 shadow-2xl z-50 
        transition-all duration-300 ease-in-out
        w-80 sm:w-96 lg:w-80
        
        /* Show sidebar only when clicked open */
        ${collapsed 
          ? '-translate-x-full' 
          : 'translate-x-0'
        }
      `}>
        
        {/* Close Button - different positioning for mobile vs desktop */}
        {/* Desktop: positioned to match hamburger menu height */}
        <div className="absolute top-0 right-0 h-16 items-center pr-4 hidden lg:flex">
          <button
            onClick={toggle}
            className="p-2.5 rounded-xl bg-slate-800/90 hover:bg-slate-700/90 
                       transition-all duration-200 flex items-center justify-center
                       text-white shadow-lg border border-slate-600/30"
            aria-label="Sidebar schließen"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Mobile: original top-right position */}
        <button
          onClick={toggle}
          className="absolute top-4 right-4 p-2 rounded-xl bg-slate-800/90 hover:bg-slate-700/90 
                     transition-all duration-200 z-10 lg:hidden flex items-center justify-center
                     text-white shadow-lg"
          aria-label="Sidebar schließen"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Sidebar Content */}
        <div className="h-full overflow-y-auto scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-transparent">
          <div className="p-4 sm:p-6 pt-20 space-y-6">
            {/* Spacer for close button - desktop only */}
            <div className="h-4 hidden lg:block"></div>
            {/* Model Selector */}
            <div className="space-y-4">
              <ModelSelector />
            </div>

            {/* Divider */}
            <div className="border-t border-slate-200/60"></div>

            {/* App Information */}
            {/* <div className="bg-gradient-to-br from-slate-50 to-slate-100/70 border border-slate-200/60
                           rounded-xl p-4 sm:p-6 shadow-sm hover:shadow-md transition-shadow duration-200">
              <div className="flex items-start mb-4">
                <span className="text-lg mr-3 mt-0.5 flex-shrink-0">ℹ️</span>
                <div className="min-w-0 flex-1">
                  <h2 className="text-lg font-semibold text-slate-800 mb-2">
                    Über diese Anwendung
                  </h2>
                  <p className="text-sm text-slate-600 leading-relaxed">
                    Die Anwendung befindet sich in einer sehr frühen Entwicklungsphase und
                    dient der Demonstration.
                  </p>
                </div>
              </div>
            </div> */}

            {/* Available Laws */}
            {lawsInfo && (
              <div className="bg-gradient-to-br from-slate-50 to-slate-100/70 border border-slate-200/60
                             rounded-xl shadow-sm hover:shadow-md transition-shadow duration-200">
                <button
                  onClick={() => setLawsExpanded(!lawsExpanded)}
                  className="w-full p-4 sm:p-6 flex items-start justify-between text-left"
                >
                  <div className="flex items-start min-w-0 flex-1">
                    <span className="text-lg mr-3 mt-0.5 flex-shrink-0">📚</span>
                    <div className="min-w-0">
                      <h2 className="text-lg font-semibold text-slate-800">Verfügbare Gesetze</h2>
                      <p className="text-sm text-slate-500 mt-0.5">
                        {lawsInfo.count.toLocaleString('de-DE')} Bundesgesetze
                        {lawsInfo.updated_at && (
                          <span className="block text-xs text-slate-400 mt-0.5">
                            Stand: {new Date(lawsInfo.updated_at).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' })}
                          </span>
                        )}
                      </p>
                    </div>
                  </div>
                  <svg
                    className={`w-4 h-4 text-slate-400 flex-shrink-0 mt-1.5 transition-transform duration-200 ${lawsExpanded ? 'rotate-180' : ''}`}
                    fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {lawsExpanded && (
                  <div className="px-4 sm:px-6 pb-4 sm:pb-6 space-y-3">
                    <input
                      type="text"
                      placeholder="Gesetz suchen…"
                      value={lawsSearch}
                      onChange={e => setLawsSearch(e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg
                                 bg-white text-slate-700 placeholder-slate-400
                                 focus:outline-none focus:ring-2 focus:ring-slate-300"
                    />
                    <div className="max-h-64 overflow-y-auto space-y-0.5 scrollbar-thin scrollbar-thumb-slate-300">
                      {lawsInfo.laws
                        .filter(l => l.toLowerCase().includes(lawsSearch.toLowerCase()))
                        .map(law => (
                          <div key={law} className="text-xs text-slate-600 py-1 px-2 rounded hover:bg-slate-200/60 font-mono">
                            {law}
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </div>
            )}
            {/* Footer */}
            <div className="pt-6 pb-4 text-center space-y-2">
              <p className="text-xs text-slate-400">
                LegisLLM - KI-gestützte Legistik
              </p>
              <div className="flex justify-center space-x-4">
                <a 
                  href="/impressum" 
                  className="text-xs text-slate-500 hover:text-slate-700 transition-colors duration-150"
                >
                  Impressum
                </a>
              </div>
            </div>
          </div>
        </div>

      </aside>
    </>
  );
}