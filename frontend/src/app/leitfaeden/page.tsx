'use client';

import { useState, useEffect } from 'react';
import Header from '@/components/Header';
import Sidebar from '@/components/Sidebar';
import { apiClient } from '@/lib/api';
import { useApp } from '@/contexts/AppContext';
import { GuidelineCatalog, GuidelineRule } from '@/types';

const STEP_LABELS: { key: string; label: string }[] = [
  { key: '', label: 'Alle Schritte' },
  { key: 'norm_identification', label: 'Normerkennung' },
  { key: 'proposal_development', label: 'Vorschläge' },
  { key: 'evaluation', label: 'Bewertung' },
  { key: 'amendment', label: 'Änderung' },
  { key: 'entwurf', label: 'Entwurf' },
];

const VERBINDLICHKEIT_LABEL: Record<string, { text: string; className: string }> = {
  muss: { text: 'MUSS', className: 'bg-red-100 text-red-700' },
  soll: { text: 'SOLL', className: 'bg-amber-100 text-amber-700' },
  kann: { text: 'KANN', className: 'bg-green-100 text-green-700' },
};

export default function LeitfaedenPage() {
  const { state, setSelectedGuidelines, setExcludedRuleIds } = useApp();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true);
  const [guidelines, setGuidelines] = useState<GuidelineCatalog[]>([]);
  const [stepFilter, setStepFilter] = useState('');

  useEffect(() => {
    apiClient.fetchGuidelines(true).then(data => {
      if (data.length > 0) setGuidelines(data);
    });
  }, []);

  const handleSidebarToggle = () => setIsSidebarCollapsed(!isSidebarCollapsed);

  const filterRulesByStep = (rules: GuidelineRule[]) => {
    if (!stepFilter) return rules;
    return rules.filter(r => r.applies_to.includes(stepFilter) || r.applies_to.length === 0);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50">
      <Header onSidebarToggle={handleSidebarToggle} />
      <Sidebar isCollapsed={isSidebarCollapsed} onToggle={handleSidebarToggle} />

      <div className="w-full">
        <main className="px-4 sm:px-6 lg:px-8 py-6 lg:py-8 space-y-6">
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Page header */}
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-slate-900">Leitfäden verwalten</h1>
                <p className="text-sm text-slate-500 mt-1">
                  {state.selectedGuidelines.length} von {guidelines.length} Leitfäden aktiv
                  {state.excludedRuleIds.length > 0 && ` \u00B7 ${state.excludedRuleIds.length} Regeln deaktiviert`}
                </p>
              </div>
            </div>

            {/* Step filter */}
            <div className="flex flex-wrap gap-2">
              {STEP_LABELS.map(s => (
                <button
                  key={s.key}
                  onClick={() => setStepFilter(s.key)}
                  className={`px-3 py-1.5 text-sm rounded-lg border transition-all duration-150 ${
                    stepFilter === s.key
                      ? 'bg-slate-800 text-white border-slate-800'
                      : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>

            {/* Guideline catalogs */}
            {guidelines.map(g => {
              const isSelected = state.selectedGuidelines.includes(g.id);
              const rules = g.rules || [];
              const filteredRules = filterRulesByStep(rules);
              const activeRuleCount = filteredRules.filter(r => !state.excludedRuleIds.includes(r.id)).length;

              return (
                <div
                  key={g.id}
                  className={`bg-white rounded-xl border shadow-sm transition-all duration-200 ${
                    isSelected ? 'border-slate-300 ring-1 ring-slate-200' : 'border-slate-200'
                  }`}
                >
                  {/* Catalog header */}
                  <div className="p-5 flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <h2 className="text-lg font-semibold text-slate-800 leading-snug">{g.name}</h2>
                      <p className="text-sm text-slate-500 mt-1">
                        {g.rule_count} Regeln gesamt
                        {isSelected && filteredRules.length > 0 && (
                          <span> &middot; {activeRuleCount}/{filteredRules.length} aktiv{stepFilter ? ' (gefiltert)' : ''}</span>
                        )}
                      </p>
                    </div>
                    <button
                      onClick={() => {
                        const next = isSelected
                          ? state.selectedGuidelines.filter(id => id !== g.id)
                          : [...state.selectedGuidelines, g.id];
                        setSelectedGuidelines(next);
                      }}
                      className={`flex-shrink-0 px-4 py-2 text-sm font-medium rounded-lg border transition-all duration-150 ${
                        isSelected
                          ? 'bg-slate-800 text-white border-slate-800 hover:bg-slate-700'
                          : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:border-slate-300'
                      }`}
                    >
                      {isSelected ? 'Deaktivieren' : 'Aktivieren'}
                    </button>
                  </div>

                  {/* Rules list (only when selected) */}
                  {isSelected && filteredRules.length > 0 && (
                    <div className="border-t border-slate-100 px-5 py-4 space-y-2">
                      {filteredRules.map(rule => {
                        const badge = VERBINDLICHKEIT_LABEL[rule.verbindlichkeit];
                        const isExcluded = state.excludedRuleIds.includes(rule.id);

                        return (
                          <button
                            key={rule.id}
                            onClick={() => {
                              const next = isExcluded
                                ? state.excludedRuleIds.filter(id => id !== rule.id)
                                : [...state.excludedRuleIds, rule.id];
                              setExcludedRuleIds(next);
                            }}
                            className={`w-full text-left rounded-lg px-3 py-2.5 text-sm transition-all duration-150 ${
                              isExcluded
                                ? 'bg-slate-50 text-slate-400'
                                : 'bg-slate-50 text-slate-700 hover:bg-slate-100'
                            }`}
                          >
                            <div className="flex items-start gap-2">
                              <span className={`flex-shrink-0 mt-0.5 w-4 h-4 rounded border flex items-center justify-center ${
                                isExcluded
                                  ? 'border-slate-300 bg-white'
                                  : 'border-slate-500 bg-slate-500'
                              }`}>
                                {!isExcluded && (
                                  <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                  </svg>
                                )}
                              </span>
                              {badge && (
                                <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold flex-shrink-0 mt-0.5 ${badge.className} ${isExcluded ? 'opacity-50' : ''}`}>
                                  {badge.text}
                                </span>
                              )}
                              <span className={isExcluded ? 'line-through' : ''}>{rule.rule}</span>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  )}

                  {isSelected && filteredRules.length === 0 && stepFilter && (
                    <div className="border-t border-slate-100 px-5 py-4">
                      <p className="text-sm text-slate-400 italic">Keine Regeln für diesen Schritt.</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </main>
      </div>
    </div>
  );
}
