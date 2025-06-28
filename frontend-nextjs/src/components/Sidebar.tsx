'use client';

import React, { useState } from 'react';
import ModelSelector from './ModelSelector';

interface SidebarProps {
  isCollapsed?: boolean;
  onToggle?: () => void;
}

export default function Sidebar({ isCollapsed = false, onToggle }: SidebarProps) {
  const [internalCollapsed, setInternalCollapsed] = useState(false);
  
  // Use external state if provided, otherwise use internal state
  const collapsed = isCollapsed !== undefined ? isCollapsed : internalCollapsed;
  const toggle = onToggle || (() => setInternalCollapsed(!internalCollapsed));

  return (
    <>
      {/* Sidebar */}
      <div className={`
        fixed left-0 top-16 h-[calc(100vh-4rem)] bg-white/95 backdrop-blur-md border-r border-slate-200/60 shadow-xl z-40 transition-all duration-300 ease-in-out
        ${collapsed ? 'w-12' : 'w-80'}
      `}>
        {/* Collapse Button */}
        <button
          onClick={toggle}
          className="absolute top-4 right-3 p-2 rounded-xl bg-slate-100/80 hover:bg-slate-200/80 transition-all duration-200 z-50 backdrop-blur-sm border border-slate-200/40"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <svg
            className={`w-4 h-4 text-slate-600 transition-transform duration-300 ${collapsed ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        {/* Sidebar Content */}
        <div className={`h-full overflow-y-auto transition-opacity duration-300 ${collapsed ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
          <div className="p-6 pt-16 space-y-6">
            {/* Model Selector */}
            <ModelSelector />

            {/* App Information */}
            <div className="bg-gradient-to-br from-slate-50 to-slate-100/70 border border-slate-200/60 rounded-xl p-6 shadow-sm">
              <div className="flex items-center mb-4">
                <span className="text-lg mr-3">ℹ️</span>
                <h2 className="text-lg font-semibold text-slate-800">
                  Über diese Anwendung
                </h2>
              </div>
              <p className="text-sm text-slate-600 leading-relaxed">
                Die Anwendung befindet sich in einer sehr frühen Entwicklungsphase und 
                dient der Demonstration. Getestet wurde die Anwendung bisher nur auf 
                Änderungen von Regelungen aus dem Einkommensteuergesetz.
              </p>
              <div className="mt-4 pt-4 border-t border-slate-200/60">
                <div className="flex items-center text-xs text-slate-500">
                  <span className="w-2 h-2 bg-emerald-400 rounded-full mr-2 animate-pulse"></span>
                  System bereit
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Sidebar Backdrop for Mobile */}
      {!collapsed && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-25 z-30 lg:hidden"
          onClick={toggle}
        />
      )}
    </>
  );
}