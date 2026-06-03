'use client';

import React, { useState, useEffect } from 'react';
import { useApp } from '@/contexts/AppContext';
import { apiClient } from '@/lib/api';
import { getApiKeyForModel } from '@/lib/apiKeyUtils';
import ThinkingIndicator from '@/components/ThinkingIndicator';
import { useThinkingSteps, THINKING_STEPS } from '@/hooks/useThinkingSteps';

export default function ContextIdentificationTab() {
  const {
    state,
    setRelevantNorms,
    setCurrentTab,
    setMultistepReasoning,
    setSelectedLaws,
    addLog
  } = useApp();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedNorm, setExpandedNorm] = useState<number | null>(null);
  const [availableLaws, setAvailableLaws] = useState<string[]>([]);
  const [lawsExpanded, setLawsExpanded] = useState(false);
  const [lawsSearch, setLawsSearch] = useState('');
  const [thinkingText, setThinkingText] = useState('');
  const thinking = useThinkingSteps();

  useEffect(() => {
    apiClient.fetchLaws().then(data => {
      if (data.laws) setAvailableLaws(data.laws);
    });
  }, []);

  const getApiKey = (): string => {
    return getApiKeyForModel(state.selectedModel, state.availableModels);
  };

  const handleIdentifyContext = async () => {
    const apiKey = getApiKey();
    if (!apiKey) {
      alert('Bitte geben Sie einen API Key ein. Nutzen Sie hierfür die Seitenleiste.');
      return;
    }

    setLoading(true);
    setError(null);
    setThinkingText('');
    addLog('==== STEP 2: IDENTIFY RELEVANT NORMS ====');

    const stepDefs = state.multistepReasoning
      ? THINKING_STEPS.identifyNormsMultistep
      : THINKING_STEPS.identifyNorms;
    thinking.startThinking(stepDefs);

    try {
      const callbacks = {
        onThinking: (token: string) => setThinkingText(prev => prev + token),
        ...(state.multistepReasoning && {
          onStep: (stepIndex: number, _message: string) => {
            thinking.setActiveStep(stepIndex);
          },
        }),
      };

      const norms = await apiClient.identifyRelevantNorms(
        state.taskDescription,
        apiKey,
        state.selectedModel,
        state.multistepReasoning,
        state.selectedLaws,
        state.selectedGuidelines,
        state.excludedRuleIds,
        callbacks
      );

      thinking.completeAll();
      setRelevantNorms(norms);
      addLog(`Successfully identified ${norms.length} relevant norms`);
    } catch (error) {
      thinking.completeAll();
      console.error('Error identifying context:', error);

      if (error instanceof Error && error.message === 'REQUEST_CANCELLED') {
        const errorMessage = 'Anfrage wurde abgebrochen.';
        setError(errorMessage);
        addLog(`Request cancelled: ${errorMessage}`);
      } else if (error instanceof Error && error.message === 'SERVER_ERROR') {
        const errorMessage = 'Serverfehler: Es ist ein interner Serverfehler aufgetreten. Bitte versuchen Sie es später erneut oder kontaktieren Sie den Support.';
        setError(errorMessage);
        addLog(`Error identifying norms: ${errorMessage}`);
      } else {
        const errorMessage = `Fehler beim Identifizieren der Normen: ${error}`;
        setError(errorMessage);
        addLog(`Error identifying norms: ${errorMessage}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCancelRequest = () => {
    const cancelled = apiClient.cancelRequest('identify-norms');
    if (cancelled) {
      setLoading(false);
      setError('Anfrage wurde abgebrochen.');
      addLog('Request cancelled by user');
    }
  };

  const handleBack = () => {
    setCurrentTab(0);
  };

  const handleNext = () => {
    setCurrentTab(2);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">2. Ermittlung des maßgeblichen Regelungskontexts</h2>
      
      {/* Task Description Reference */}
      <details className="bg-gray-50 rounded-lg p-4">
        <summary className="cursor-pointer font-medium text-gray-700 hover:text-gray-900">
          Aufgabenstellung (Referenz)
        </summary>
        <div className="mt-2 text-gray-600">
          {state.taskDescription}
        </div>
      </details>

      {/* Law Pre-Selection */}
      {availableLaws.length > 0 && (
        <div className="bg-gray-50 rounded-lg border border-gray-200">
          <button
            onClick={() => setLawsExpanded(!lawsExpanded)}
            className="w-full p-4 flex items-center justify-between text-left"
          >
            <div>
              <span className="font-medium text-gray-700">Vorauswahl der Gesetze</span>
              <span className="ml-2 text-sm text-gray-500">
                {state.selectedLaws.length > 0
                  ? `(${state.selectedLaws.length} ausgewählt)`
                  : `(alle ${availableLaws.length.toLocaleString('de-DE')} Gesetze)`}
              </span>
            </div>
            <svg
              className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${lawsExpanded ? 'rotate-180' : ''}`}
              fill="none" stroke="currentColor" viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {lawsExpanded && (
            <div className="px-4 pb-4 space-y-3">
              <div className="flex items-center gap-3">
                <input
                  type="text"
                  placeholder="Gesetz suchen…"
                  value={lawsSearch}
                  onChange={e => setLawsSearch(e.target.value)}
                  className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white text-gray-700 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-300"
                />
                {state.selectedLaws.length > 0 && (
                  <button
                    onClick={() => setSelectedLaws([])}
                    className="text-xs text-gray-500 hover:text-gray-700 whitespace-nowrap"
                  >
                    Auswahl aufheben
                  </button>
                )}
              </div>
              <div className="max-h-48 overflow-y-auto space-y-0.5 scrollbar-thin scrollbar-thumb-gray-300">
                {availableLaws
                  .filter(l => l.toLowerCase().includes(lawsSearch.toLowerCase()))
                  .map(law => (
                    <label
                      key={law}
                      className="flex items-center gap-2 text-sm text-gray-700 py-1 px-2 rounded hover:bg-gray-100 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={state.selectedLaws.includes(law)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedLaws([...state.selectedLaws, law]);
                          } else {
                            setSelectedLaws(state.selectedLaws.filter(l => l !== law));
                          }
                        }}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="font-mono text-xs">{law}</span>
                    </label>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Warning when no pre-selection with large law set */}
      {state.selectedLaws.length === 0 && availableLaws.length > 50 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
          <p className="text-sm text-amber-700">
            <strong>Hinweis:</strong> Ohne Vorauswahl werden alle {availableLaws.length.toLocaleString('de-DE')} Gesetze an das Sprachmodell übergeben.
            Dies kann zu höheren Kosten, längeren Antwortzeiten und ungenaueren Ergebnissen führen.
            Eine Vorauswahl der relevanten Gesetze wird empfohlen.
          </p>
        </div>
      )}

      {/* Multistep Reasoning Option */}
      <div className="space-y-2">
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={state.multistepReasoning}
            onChange={(e) => setMultistepReasoning(e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm font-medium text-gray-700">
            Multistep reasoning aktivieren
          </span>
        </label>
        {state.multistepReasoning && (
          <p className="text-sm text-orange-600">
            ⚠️ <strong>Experimentelles Feature:</strong> Diese Funktion befindet sich in der Testphase. 
            Bei der Auswahl von Reasoning-Modellen kann diese Funktion zu sehr langen Antwortzeiten (&gt; 10 min) führen.
          </p>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={handleIdentifyContext}
          disabled={loading || !state.taskDescription}
          className="px-8 py-3 bg-orange-300 text-gray-800 rounded-xl hover:bg-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 transition-all duration-200 font-semibold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
              <span>Ermittle maßgeblichen Regelungskontext...</span>
            </div>
          ) : (
            'Regelungskontext ermitteln'
          )}
        </button>
        {loading && (
          <button
            onClick={handleCancelRequest}
            className="px-6 py-3 bg-red-500 text-white rounded-xl hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-all duration-200 font-semibold shadow-lg"
          >
            Abbrechen
          </button>
        )}
      </div>

      {/* Thinking Indicator */}
      <ThinkingIndicator
        steps={thinking.steps}
        isActive={thinking.isActive}
        startedAt={thinking.startedAt}
        thinkingText={thinkingText}
      />

      {/* Results */}
      {state.relevantNorms && state.relevantNorms.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Identifizierte Rechtsnormen:</h3>
          
          {/* Norm Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {state.relevantNorms.map((norm, index) => (
              <div
                key={index}
                onClick={() => setExpandedNorm(expandedNorm === index ? null : index)}
                className="bg-blue-50 border border-blue-200 rounded-lg p-3 cursor-pointer hover:bg-blue-100 transition-colors duration-150"
              >
                <p className="font-medium text-blue-900">
                  {norm.enbez} {norm.jurabk} {norm.P ? `Abs. ${norm.P}` : ''}
                </p>
              </div>
            ))}
          </div>

          {/* Expanded Norm Full Text */}
          {expandedNorm !== null && state.relevantNorms[expandedNorm] && (
            <div className="bg-gray-50 border border-gray-300 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-2">
                {state.relevantNorms[expandedNorm].enbez} {state.relevantNorms[expandedNorm].jurabk}
                {state.relevantNorms[expandedNorm].P ? ` Abs. ${state.relevantNorms[expandedNorm].P}` : ''}
              </h4>
              <pre className="whitespace-pre-wrap text-sm font-mono text-gray-700">
                {state.relevantNorms[expandedNorm].wording || 'Kein Volltext verfügbar.'}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={handleBack}
          className="px-8 py-3 bg-gradient-to-r from-slate-600 to-slate-700 text-white rounded-xl hover:from-slate-700 hover:to-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 transition-all duration-200 font-semibold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Zurück
        </button>
        <button
          onClick={handleNext}
          disabled={!state.relevantNorms}
          className="px-8 py-3 bg-gradient-to-r from-slate-600 to-slate-700 text-white rounded-xl hover:from-slate-700 hover:to-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 transition-all duration-200 font-semibold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Weiter
        </button>
      </div>
    </div>
  );
}