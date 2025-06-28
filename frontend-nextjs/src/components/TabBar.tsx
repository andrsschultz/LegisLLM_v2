'use client';

import React from 'react';
import { useApp } from '@/contexts/AppContext';

const tabs = [
  { id: 0, label: 'Aufgabenstellung', icon: '📝', shortLabel: 'Aufgabe' },
  { id: 1, label: 'Regelungskontext', icon: '🔍', shortLabel: 'Kontext' },
  { id: 2, label: 'Regelungsalternativen', icon: '💡', shortLabel: 'Alternativen' },
  { id: 3, label: 'Evaluierung', icon: '⚖️', shortLabel: 'Evaluierung' },
  { id: 4, label: 'Finalisierung', icon: '✅', shortLabel: 'Finalisierung' },
];

export default function TabBar() {
  const { state, setCurrentTab } = useApp();

  const getTabStatus = (tabId: number) => {
    if (tabId === state.currentTab) return 'active';
    if (tabId < state.currentTab) return 'completed';
    
    // Check if tab is accessible based on progress
    switch (tabId) {
      case 0:
        return 'available';
      case 1:
        return state.taskDescription ? 'available' : 'disabled';
      case 2:
        return state.relevantNorms ? 'available' : 'disabled';
      case 3:
        return state.amendmentProposals ? 'available' : 'disabled';
      case 4:
        return state.amendmentProposals || state.evaluatedProposals ? 'available' : 'disabled';
      default:
        return 'disabled';
    }
  };

  const getTabClasses = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-gradient-to-r from-slate-600 to-slate-700 text-white border-slate-600 shadow-lg';
      case 'completed':
        return 'bg-slate-100 text-slate-700 border-slate-300 hover:bg-slate-200';
      case 'available':
        return 'bg-white/80 text-slate-700 border-slate-200 hover:bg-slate-50 hover:border-slate-300 backdrop-blur-sm';
      case 'disabled':
        return 'bg-slate-50 text-slate-400 border-slate-200 cursor-not-allowed';
      default:
        return 'bg-white text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="bg-white/90 backdrop-blur-md border-b border-slate-200/60 sticky top-0 z-20 shadow-sm">
      <div className="px-4 sm:px-6 lg:px-8">
        {/* Desktop Tab Bar */}
        <div className="hidden lg:flex space-x-1 overflow-x-auto py-4">
          {tabs.map((tab) => {
            const status = getTabStatus(tab.id);
            const isDisabled = status === 'disabled';
            
            return (
              <button
                key={tab.id}
                onClick={() => !isDisabled && setCurrentTab(tab.id)}
                disabled={isDisabled}
                className={`
                  flex items-center space-x-3 px-5 py-3 rounded-xl border transition-all duration-200 min-w-fit
                  ${getTabClasses(status)}
                  ${!isDisabled ? 'transform hover:scale-105 hover:shadow-md' : ''}
                `}
              >
                <span className="text-lg">{tab.icon}</span>
                <span className="font-semibold whitespace-nowrap">
                  {tab.id + 1}. {tab.label}
                </span>
              </button>
            );
          })}
        </div>

        {/* Mobile Tab Bar */}
        <div className="lg:hidden">
          <div className="flex space-x-1 overflow-x-auto py-3" style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
            {tabs.map((tab) => {
              const status = getTabStatus(tab.id);
              const isDisabled = status === 'disabled';
              
              return (
                <button
                  key={tab.id}
                  onClick={() => !isDisabled && setCurrentTab(tab.id)}
                  disabled={isDisabled}
                  className={`
                    flex flex-col items-center space-y-1 px-3 py-2 rounded-xl border transition-all duration-200 min-w-fit
                    ${getTabClasses(status)}
                  `}
                >
                  <span className="text-sm">{tab.icon}</span>
                  <span className="text-xs font-semibold text-center leading-tight">
                    {tab.shortLabel}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="pb-2">
          <div className="bg-slate-200 rounded-full h-1">
            <div 
              className="bg-gradient-to-r from-slate-600 to-slate-700 h-1 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${((state.currentTab + 1) / tabs.length) * 100}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}