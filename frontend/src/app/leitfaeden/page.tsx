'use client';

import { useState, useEffect, useRef, useMemo } from 'react';
import Header from '@/components/Header';
import Sidebar from '@/components/Sidebar';
import { apiClient } from '@/lib/api';
import { useApp } from '@/contexts/AppContext';
import { getApiKeyForModel } from '@/lib/apiKeyUtils';
import { GuidelineCatalog, GuidelineRule } from '@/types';

const STEP_LABELS: { key: string; label: string }[] = [
  { key: '', label: 'Alle Schritte' },
  { key: 'norm_identification', label: 'Regelungskontext' },
  { key: 'proposal_development', label: 'Regelungsalternativen' },
  { key: 'evaluation', label: 'Evaluierung' },
  { key: 'amendment', label: 'Umsetzung' },
  { key: 'entwurf', label: 'Gesetzesentwurf' },
];

const VERBINDLICHKEIT_LABEL: Record<string, { text: string; className: string }> = {
  muss: { text: 'MUSS', className: 'bg-red-100 text-red-700' },
  soll: { text: 'SOLL', className: 'bg-amber-100 text-amber-700' },
  kann: { text: 'KANN', className: 'bg-green-100 text-green-700' },
};

export default function LeitfaedenPage() {
  const { state, setSelectedGuidelines, setExcludedRuleIds, setCustomGuidelines } = useApp();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true);
  const [serverGuidelines, setServerGuidelines] = useState<GuidelineCatalog[]>([]);
  const [stepFilter, setStepFilter] = useState('');

  // Upload state
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [customName, setCustomName] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // IDs of custom (local) catalogs for quick lookup
  const customIds = useMemo(
    () => new Set(state.customGuidelines.map(g => g.id)),
    [state.customGuidelines],
  );

  // Merge server guidelines + custom (localStorage) guidelines
  const allGuidelines = useMemo(
    () => [...serverGuidelines, ...state.customGuidelines],
    [serverGuidelines, state.customGuidelines],
  );

  useEffect(() => {
    apiClient.fetchGuidelines(true).then(data => setServerGuidelines(data));
  }, []);

  const handleSidebarToggle = () => setIsSidebarCollapsed(!isSidebarCollapsed);

  const filterRulesByStep = (rules: GuidelineRule[]) => {
    if (!stepFilter) return rules;
    return rules.filter(r => r.applies_to.includes(stepFilter) || r.applies_to.length === 0);
  };

  const getApiKey = () => getApiKeyForModel(state.selectedModel, state.availableModels);

  const handleUpload = async (file: File) => {
    const apiKey = getApiKey();
    if (!apiKey || !state.selectedModel) {
      setUploadError('Bitte zuerst API-Key und Modell in der Sidebar konfigurieren.');
      return;
    }

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const catalog = await apiClient.extractGuideline(
        file,
        apiKey,
        state.selectedModel,
        customName || undefined,
      );

      // Ensure unique ID among all existing guidelines
      const existingIds = new Set(allGuidelines.map(g => g.id));
      if (existingIds.has(catalog.id)) {
        let i = 2;
        while (existingIds.has(`${catalog.id}_${i}`)) i++;
        catalog.id = `${catalog.id}_${i}`;
      }

      // Store locally
      setCustomGuidelines([...state.customGuidelines, catalog]);
      setUploadSuccess(`"${catalog.name}" wurde erfolgreich hinzugefügt (${catalog.rule_count} Regeln extrahiert). Gespeichert in Ihrem Browser.`);
      setCustomName('');
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err: any) {
      setUploadError(err.message || 'Upload fehlgeschlagen.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = (catalogId: string, catalogName: string) => {
    if (!confirm(`"${catalogName}" wirklich löschen?`)) return;
    setCustomGuidelines(state.customGuidelines.filter(g => g.id !== catalogId));
    setSelectedGuidelines(state.selectedGuidelines.filter(id => id !== catalogId));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50">
      <Header onSidebarToggle={handleSidebarToggle} />
      <Sidebar isCollapsed={isSidebarCollapsed} onToggle={handleSidebarToggle} />

      <div className="w-full">
        <main className="px-4 sm:px-6 lg:px-8 py-6 lg:py-8 space-y-6">
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Page header */}
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Leitfäden verwalten</h1>
              <p className="text-sm text-slate-500 mt-1">
                {state.selectedGuidelines.length} von {allGuidelines.length} Leitfäden aktiv
                {state.excludedRuleIds.length > 0 && ` \u00B7 ${state.excludedRuleIds.length} Regeln deaktiviert`}
              </p>
            </div>

            {/* Upload section */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
              <h2 className="text-lg font-semibold text-slate-800">Eigenen Leitfaden hochladen</h2>
              <p className="text-sm text-slate-500">
                Laden Sie eine PDF-Datei hoch. Die Regeln werden per LLM extrahiert und lokal in Ihrem Browser gespeichert.
              </p>

              <div className="space-y-3">
                <input
                  type="text"
                  placeholder="Name des Leitfadens (optional)"
                  value={customName}
                  onChange={e => setCustomName(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg
                             bg-white text-slate-700 placeholder-slate-400
                             focus:outline-none focus:ring-2 focus:ring-slate-300"
                />

                <div className="flex items-center gap-3">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf"
                    disabled={uploading}
                    onChange={e => {
                      const file = e.target.files?.[0];
                      if (file) handleUpload(file);
                    }}
                    className="text-sm text-slate-600 file:mr-3 file:py-2 file:px-4
                               file:rounded-lg file:border file:border-slate-200
                               file:text-sm file:font-medium file:bg-white file:text-slate-700
                               hover:file:bg-slate-50 file:cursor-pointer file:transition-all"
                  />
                </div>

                {uploading && (
                  <div className="flex items-center gap-2 text-sm text-slate-500">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    PDF wird analysiert und Regeln werden extrahiert...
                  </div>
                )}

                {uploadError && (
                  <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                    {uploadError}
                  </p>
                )}

                {uploadSuccess && (
                  <p className="text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2">
                    {uploadSuccess}
                  </p>
                )}
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
            {allGuidelines.map(g => {
              const isSelected = state.selectedGuidelines.includes(g.id);
              const rules = g.rules || [];
              const filteredRules = filterRulesByStep(rules);
              const activeRuleCount = filteredRules.filter(r => !state.excludedRuleIds.includes(r.id)).length;
              const isCustom = customIds.has(g.id);

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
                      <div className="flex items-center gap-2">
                        <h2 className="text-lg font-semibold text-slate-800 leading-snug">{g.name}</h2>
                        {isCustom && (
                          <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-blue-50 text-blue-600 flex-shrink-0">
                            Lokal
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-slate-500 mt-1">
                        {g.rule_count} Regeln gesamt
                        {isSelected && filteredRules.length > 0 && (
                          <span> &middot; {activeRuleCount}/{filteredRules.length} aktiv{stepFilter ? ' (gefiltert)' : ''}</span>
                        )}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {isCustom && (
                        <button
                          onClick={() => handleDelete(g.id, g.name)}
                          className="p-2 text-slate-400 hover:text-red-500 transition-colors rounded-lg hover:bg-red-50"
                          title="Leitfaden löschen"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      )}
                      <button
                        onClick={() => {
                          const next = isSelected
                            ? state.selectedGuidelines.filter(id => id !== g.id)
                            : [...state.selectedGuidelines, g.id];
                          setSelectedGuidelines(next);
                        }}
                        className={`px-4 py-2 text-sm font-medium rounded-lg border transition-all duration-150 ${
                          isSelected
                            ? 'bg-slate-800 text-white border-slate-800 hover:bg-slate-700'
                            : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:border-slate-300'
                        }`}
                      >
                        {isSelected ? 'Deaktivieren' : 'Aktivieren'}
                      </button>
                    </div>
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
