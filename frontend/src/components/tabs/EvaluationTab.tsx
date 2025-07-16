'use client';

import React, { useState } from 'react';
import { useApp } from '@/contexts/AppContext';
import { apiClient } from '@/lib/api';
import { DeepEvaluation, ProposalEntry } from '@/types';
import { getApiKeyForModel } from '@/lib/apiKeyUtils';

export default function EvaluationTab() {
  const { 
    state, 
    setEvaluatedProposals, 
    setCurrentTab,
    addLog 
  } = useApp();
  
  const [loading, setLoading] = useState(false);
  const [deepEvalLoading, setDeepEvalLoading] = useState(false);
  const [selectedProposalIndex, setSelectedProposalIndex] = useState(0);
  const [deepEvaluation, setDeepEvaluation] = useState<DeepEvaluation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deepEvalError, setDeepEvalError] = useState<string | null>(null);

  const getApiKey = (): string => {
    return getApiKeyForModel(state.selectedModel, state.availableModels);
  };

  const handleEvaluateProposals = async () => {
    const apiKey = getApiKey();
    if (!apiKey) {
      alert('Bitte geben Sie einen API Key ein. Nutzen Sie hierfür die Seitenleiste.');
      return;
    }

    if (!state.amendmentProposals || !state.relevantNorms) {
      alert('Bitte entwickeln Sie zuerst Regelungsalternativen.');
      return;
    }

    setLoading(true);
    setError(null);
    addLog('==== STEP 4: EVALUATE PROPOSALS ====');
    
    try {
      const evaluatedProposals = await apiClient.evaluateProposals(
        state.taskDescription,
        state.relevantNorms,
        state.amendmentProposals,
        apiKey,
        state.selectedModel
      );
      
      setEvaluatedProposals(evaluatedProposals);
      addLog(`Successfully evaluated ${evaluatedProposals.length} proposals`);
    } catch (error) {
      console.error('Error evaluating proposals:', error);
      
      if (error instanceof Error && error.message === 'SERVER_ERROR') {
        const errorMessage = 'Serverfehler: Es ist ein interner Serverfehler aufgetreten. Bitte versuchen Sie es später erneut oder kontaktieren Sie den Support.';
        setError(errorMessage);
        addLog(`Error evaluating proposals: ${errorMessage}`);
      } else {
        const errorMessage = `Fehler beim Evaluieren der Vorschläge: ${error}`;
        setError(errorMessage);
        addLog(`Error evaluating proposals: ${errorMessage}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDeepEvaluation = async () => {
    const apiKey = getApiKey();
    if (!apiKey || !state.evaluatedProposals || !state.amendmentProposals || !state.relevantNorms) {
      return;
    }

    const selectedProposal = state.amendmentProposals[selectedProposalIndex];
    if (!selectedProposal) return;

    setDeepEvalLoading(true);
    setDeepEvalError(null);
    addLog('==== PERFORM DEEP EVALUATION ====');
    
    try {
      const deepEval = await apiClient.deepEvaluateProposal(
        state.taskDescription,
        state.relevantNorms,
        selectedProposal,
        apiKey,
        state.selectedModel
      );
      
      setDeepEvaluation(deepEval);
      addLog('Successfully completed deep evaluation');
    } catch (error) {
      console.error('Error performing deep evaluation:', error);
      
      if (error instanceof Error && error.message === 'SERVER_ERROR') {
        const errorMessage = 'Serverfehler: Es ist ein interner Serverfehler aufgetreten. Bitte versuchen Sie es später erneut oder kontaktieren Sie den Support.';
        setDeepEvalError(errorMessage);
        addLog(`Error in deep evaluation: ${errorMessage}`);
      } else {
        const errorMessage = `Fehler bei der vertieften Evaluierung: ${error}`;
        setDeepEvalError(errorMessage);
        addLog(`Error in deep evaluation: ${errorMessage}`);
      }
    } finally {
      setDeepEvalLoading(false);
    }
  };

  const handleBack = () => {
    setCurrentTab(2);
  };

  const handleNext = () => {
    setCurrentTab(4);
  };

  const handleSkip = () => {
    setCurrentTab(4);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">4. Juristische und rechtstechnische Abwägung</h2>
      
      {/* Reference Section */}
      <details className="bg-gray-50 rounded-lg p-4">
        <summary className="cursor-pointer font-medium text-gray-700 hover:text-gray-900">
          Aufgabenstellung & Alternativen (Referenz)
        </summary>
        <div className="mt-2 space-y-2">
          <div>
            <p className="font-medium text-gray-700">Aufgabenstellung:</p>
            <p className="text-gray-600">{state.taskDescription}</p>
          </div>
          {state.amendmentProposals && (
            <div>
              <p className="font-medium text-gray-700">Vorgeschlagene Alternativen:</p>
              <ul className="text-gray-600 list-disc list-inside">
                {state.amendmentProposals.map((proposal, index) => (
                  <li key={index}>{proposal.proposalTitle}</li>
                ))}
              </ul>
            </div>
          )}
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

      {/* Action Button */}
      <button
        onClick={handleEvaluateProposals}
        disabled={loading || !state.amendmentProposals}
        className="px-8 py-3 bg-orange-300 text-gray-800 rounded-xl hover:bg-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 transition-all duration-200 font-semibold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? (
          <div className="flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
            <span>Evaluiere Vorschläge...</span>
          </div>
        ) : (
          'Vorschläge evaluieren'
        )}
      </button>

      {/* Evaluated Proposals Results */}
      {state.evaluatedProposals && state.evaluatedProposals.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Evaluierte Vorschläge (nach Eignung sortiert):</h3>
          
          {state.evaluatedProposals.map((proposal, index) => (
            <details key={index} className="bg-white border border-gray-200 rounded-lg">
              <summary className="cursor-pointer p-4 font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50">
                Vorschlag {index + 1}: {proposal.proposalTitle}
              </summary>
              <div className="p-4 pt-0 space-y-3">
                <div>
                  <p className="font-medium text-gray-700">Betroffene Rechtsnorm:</p>
                  <p className="text-gray-600">{proposal.proposalTitle}</p>
                </div>
                <div>
                  <p className="font-medium text-gray-700">Pro:</p>
                  <ul className="text-gray-600 list-disc list-inside">
                    {proposal.pro.map((point, pointIndex) => (
                      <li key={pointIndex}>{point}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="font-medium text-gray-700">Contra:</p>
                  <ul className="text-gray-600 list-disc list-inside">
                    {proposal.contra.map((point, pointIndex) => (
                      <li key={pointIndex}>{point}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </details>
          ))}

          {/* Deep Evaluation Section */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h4 className="text-lg font-semibold text-gray-900 mb-4">Vertiefte Evaluierung:</h4>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Wählen Sie einen Vorschlag für vertiefte Evaluierung:
              </label>
              <select
                value={selectedProposalIndex}
                onChange={(e) => setSelectedProposalIndex(parseInt(e.target.value))}
                className="block w-full max-w-md px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {state.evaluatedProposals.map((proposal, index) => (
                  <option key={index} value={index}>
                    Vorschlag {index + 1}: {proposal.proposalTitle}
                  </option>
                ))}
              </select>
            </div>

            {/* Deep Evaluation Error Display */}
            {deepEvalError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-red-600">{deepEvalError}</p>
                  </div>
                </div>
              </div>
            )}

            <button
              onClick={handleDeepEvaluation}
              disabled={deepEvalLoading}
              className="px-8 py-3 bg-orange-300 text-gray-800 rounded-xl hover:bg-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 transition-all duration-200 font-semibold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {deepEvalLoading ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  <span>Führe vertiefte Evaluierung durch...</span>
                </div>
              ) : (
                'Vertiefte Evaluierung durchführen'
              )}
            </button>

            {/* Deep Evaluation Results */}
            {deepEvaluation && (
              <div className="mt-6 space-y-4">
                <h5 className="text-lg font-semibold text-gray-900">Ergebnisse der vertieften Evaluierung:</h5>
                
                {/* Juristische Beurteilung */}
                <details className="bg-gray-50 rounded-lg" open>
                  <summary className="cursor-pointer p-4 font-medium text-gray-700 hover:text-gray-900">
                    Juristische Beurteilung
                  </summary>
                  <div className="p-4 pt-0 space-y-2">
                    <div>
                      <p className="font-medium text-gray-700">Bewertung:</p>
                      <p className="text-gray-600">{deepEvaluation.juristischeBeurteilung.Bewertung}</p>
                    </div>
                    <div>
                      <p className="font-medium text-gray-700">Potentielle Probleme:</p>
                      <p className="text-gray-600">{deepEvaluation.juristischeBeurteilung.PotentielleProbleme}</p>
                    </div>
                    <div>
                      <p className="font-medium text-gray-700">Querverweise:</p>
                      <ul className="text-gray-600 list-disc list-inside">
                        {deepEvaluation.juristischeBeurteilung.Querverweise.map((ref, index) => (
                          <li key={index}>{ref.jurabk} {ref.enbez}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </details>

                {/* Rechtstechnische Beurteilung */}
                <details className="bg-gray-50 rounded-lg" open>
                  <summary className="cursor-pointer p-4 font-medium text-gray-700 hover:text-gray-900">
                    Rechtstechnische Beurteilung
                  </summary>
                  <div className="p-4 pt-0 space-y-2">
                    <div>
                      <p className="font-medium text-gray-700">Klarheit:</p>
                      <p className="text-gray-600">{deepEvaluation.rechtstechnischeBeurteilung.Klarheit}</p>
                    </div>
                    <div>
                      <p className="font-medium text-gray-700">Formulierungsvorschlag:</p>
                      <p className="text-gray-600">{deepEvaluation.rechtstechnischeBeurteilung.Formulierungsvorschlag}</p>
                    </div>
                    <div>
                      <p className="font-medium text-gray-700">Risikopunkte:</p>
                      <ul className="text-gray-600 list-disc list-inside">
                        {deepEvaluation.rechtstechnischeBeurteilung.Risikopunkte.map((risk, index) => (
                          <li key={index}>{risk}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </details>

                {/* Continue with other sections... */}
                <details className="bg-gray-50 rounded-lg" open>
                  <summary className="cursor-pointer p-4 font-medium text-gray-700 hover:text-gray-900">
                    Fazit Pro/Contra
                  </summary>
                  <div className="p-4 pt-0 space-y-2">
                    <div>
                      <p className="font-medium text-gray-700">Pro:</p>
                      <ul className="text-gray-600 list-disc list-inside">
                        {deepEvaluation.fazitProContra.Pro.map((point, index) => (
                          <li key={index}>{point}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <p className="font-medium text-gray-700">Contra:</p>
                      <ul className="text-gray-600 list-disc list-inside">
                        {deepEvaluation.fazitProContra.Contra.map((point, index) => (
                          <li key={index}>{point}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <p className="font-medium text-gray-700">Offene Fragen:</p>
                      <ul className="text-gray-600 list-disc list-inside">
                        {deepEvaluation.fazitProContra.OffeneFragen.map((question, index) => (
                          <li key={index}>{question}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </details>
              </div>
            )}
          </div>
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
        <div className="space-x-3">
          <button
            onClick={handleSkip}
            className="px-8 py-3 bg-gray-300 text-gray-700 rounded-xl hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-all duration-200 font-semibold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Überspringen
          </button>
          <button
            onClick={handleNext}
            disabled={!state.evaluatedProposals}
            className="px-8 py-3 bg-gradient-to-r from-slate-600 to-slate-700 text-white rounded-xl hover:from-slate-700 hover:to-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 transition-all duration-200 font-semibold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Weiter
          </button>
        </div>
      </div>
    </div>
  );
}