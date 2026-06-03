'use client';

import React, { useState } from 'react';
import { useApp } from '@/contexts/AppContext';
import { apiClient } from '@/lib/api';
import { getApiKeyForModel } from '@/lib/apiKeyUtils';
import ThinkingIndicator from '@/components/ThinkingIndicator';
import { useThinkingSteps, THINKING_STEPS } from '@/hooks/useThinkingSteps';
import { getCustomRulesForStep } from '@/lib/customRules';

export default function ProposalDevelopmentTab() {
  const {
    state,
    setAmendmentProposals,
    setCurrentTab,
    addLog
  } = useApp();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [thinkingText, setThinkingText] = useState('');
  const thinking = useThinkingSteps();

  const getApiKey = (): string => {
    return getApiKeyForModel(state.selectedModel, state.availableModels);
  };

  const handleDevelopAlternatives = async () => {
    const apiKey = getApiKey();
    if (!apiKey) {
      alert('Bitte geben Sie einen API Key ein. Nutzen Sie hierfür die Seitenleiste.');
      return;
    }

    if (!state.relevantNorms) {
      alert('Bitte identifizieren Sie zuerst den Regelungskontext.');
      return;
    }

    setLoading(true);
    setError(null);
    setThinkingText('');
    addLog('==== STEP 3: DEVELOP AMENDMENT PROPOSALS ====');
    thinking.startThinking(THINKING_STEPS.generateProposals);

    try {
      const proposals = await apiClient.generateProposals(
        state.taskDescription,
        state.relevantNorms,
        apiKey,
        state.selectedModel,
        state.selectedGuidelines,
        state.excludedRuleIds,
        getCustomRulesForStep(state.customGuidelines, state.selectedGuidelines, state.excludedRuleIds, 'proposal_development'),
        { onThinking: (token: string) => setThinkingText(prev => prev + token) }
      );

      thinking.completeAll();
      setAmendmentProposals(proposals);
      addLog(`Successfully generated ${proposals.length} amendment proposals`);
    } catch (error) {
      thinking.completeAll();
      console.error('Error developing alternatives:', error);

      if (error instanceof Error && error.message === 'REQUEST_CANCELLED') {
        const errorMessage = 'Anfrage wurde abgebrochen.';
        setError(errorMessage);
        addLog(`Request cancelled: ${errorMessage}`);
      } else if (error instanceof Error && error.message === 'SERVER_ERROR') {
        const errorMessage = 'Serverfehler: Es ist ein interner Serverfehler aufgetreten. Bitte versuchen Sie es später erneut oder kontaktieren Sie den Support.';
        setError(errorMessage);
        addLog(`Error developing proposals: ${errorMessage}`);
      } else {
        const errorMessage = `Fehler beim Entwickeln der Vorschläge: ${error}`;
        setError(errorMessage);
        addLog(`Error developing proposals: ${errorMessage}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCancelRequest = () => {
    const cancelled = apiClient.cancelRequest('generate-proposals');
    if (cancelled) {
      setLoading(false);
      thinking.completeAll();
      setError('Anfrage wurde abgebrochen.');
      addLog('Request cancelled by user');
    }
  };

  const handleBack = () => {
    setCurrentTab(1);
  };

  const handleNext = () => {
    setCurrentTab(3);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">3. Entwicklung abstrakter Regelungsalternativen</h2>

      {/* Reference Section */}
      <details className="bg-gray-50 rounded-lg p-4">
        <summary className="cursor-pointer font-medium text-gray-700 hover:text-gray-900">
          Aufgabenstellung & Regelungskontext (Referenz)
        </summary>
        <div className="mt-2 space-y-2">
          <div>
            <p className="font-medium text-gray-700">Aufgabenstellung:</p>
            <p className="text-gray-600">{state.taskDescription}</p>
          </div>
          <div>
            <p className="font-medium text-gray-700">Identifizierte Rechtsnormen:</p>
            {state.relevantNorms ? (
              <ul className="text-gray-600 list-disc list-inside">
                {state.relevantNorms.map((norm, index) => (
                  <li key={index}>
                    {norm.enbez} {norm.jurabk}{norm.P ? ` Abs. ${norm.P}` : ''}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500">Keine Normen identifiziert</p>
            )}
          </div>
        </div>
      </details>

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
          onClick={handleDevelopAlternatives}
          disabled={loading || !state.relevantNorms}
          className="px-8 py-3 bg-orange-300 text-gray-800 rounded-xl hover:bg-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 transition-all duration-200 font-semibold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
              <span>Entwickle Regelungsalternativen...</span>
            </div>
          ) : (
            'Regelungsalternativen entwickeln'
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
      {state.amendmentProposals && state.amendmentProposals.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Vorgeschlagene Änderungen:</h3>

          {state.amendmentProposals.map((proposal, index) => (
            <details key={index} className="bg-white border border-gray-200 rounded-lg">
              <summary className="cursor-pointer p-4 font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50">
                Vorschlag {index + 1}: {proposal.proposalTitle}
              </summary>
              <div className="p-4 pt-0 space-y-3">
                <div>
                  <p className="font-medium text-gray-700">Alternative:</p>
                  <p className="text-gray-600">{proposal.proposalTitle}</p>
                </div>
                <div>
                  <p className="font-medium text-gray-700">Beschreibung:</p>
                  <p className="text-gray-600">{proposal.description}</p>
                </div>
                <div>
                  <p className="font-medium text-gray-700">Betroffene Rechtsnormen:</p>
                  <ul className="text-gray-600 list-disc list-inside">
                    {proposal.affectedNorms.map((norm, normIndex) => (
                      <li key={normIndex}>
                        {norm.enbez} {norm.jurabk}{norm.P ? ` Abs. ${norm.P}` : ''}
                        {norm.amendmentDescription && (
                          <div className="ml-4 mt-1 text-sm text-gray-500">
                              {norm.amendmentDescription}
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </details>
          ))}
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
          disabled={!state.amendmentProposals}
          className="px-8 py-3 bg-gradient-to-r from-slate-600 to-slate-700 text-white rounded-xl hover:from-slate-700 hover:to-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 transition-all duration-200 font-semibold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Weiter
        </button>
      </div>
    </div>
  );
}
