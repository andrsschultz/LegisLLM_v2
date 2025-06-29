'use client';

import React, { useState } from 'react';

interface HeaderProps {
  onSidebarToggle: () => void;
}

export default function Header({ onSidebarToggle }: HeaderProps) {
  const [showMenu, setShowMenu] = useState(false);

  return (
    <header className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-700 shadow-xl border-b border-slate-600/50 backdrop-blur-sm">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Left Section - Logo and Title */}
          <div className="flex items-center space-x-4">
            {/* Sidebar Toggle Button - Now visible on all screen sizes */}
            <button
              onClick={onSidebarToggle}
              className="p-2.5 rounded-xl bg-slate-800/50 hover:bg-slate-700/60 active:bg-slate-600/70 
                         transition-all duration-200 backdrop-blur-sm border border-slate-600/30
                         focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-opacity-50"
              aria-label="Menü öffnen"
            >
              <svg className="w-5 h-5 text-slate-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>

            {/* Logo and Title */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-white to-slate-50 rounded-xl shadow-lg border border-slate-200/20">
                <span className="text-2xl filter drop-shadow-sm">⚖️</span>
              </div>
              <div>
                <h1 className="text-xl lg:text-2xl font-bold text-white tracking-tight">
                  LegisLLM
                </h1>
                <p className="text-slate-300 text-sm hidden sm:block font-medium">
                  KI-gestützte Legistik
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Close menu when clicking outside */}
      {showMenu && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setShowMenu(false)}
        />
      )}
    </header>
  );
}