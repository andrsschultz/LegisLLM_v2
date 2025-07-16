'use client';

import React, { useState } from 'react';
import { useApp } from '@/contexts/AppContext';
import { apiClient } from '@/lib/api';
import { ProposalEntry, EvaluatedProposal } from '@/types';
import { getApiKeyForModel } from '@/lib/apiKeyUtils';

export default function FinalizationTab() {
  const { 
    state, 
    setFinalAmendment,
    setCurrentTab,
    addLog 
  } = useApp();
  
  const [loading, setLoading] = useState(false);
  const [selectedProposalIndex, setSelectedProposalIndex] = useState(0);
  const [customAdjustments, setCustomAdjustments] = useState('');
  const [manualNorm, setManualNorm] = useState('');
  const [manualProposal, setManualProposal] = useState('');
  const [error, setError] = useState<string | null>(null);

  const getApiKey = (): string => {
    return getApiKeyForModel(state.selectedModel, state.availableModels);
  };

  const handleGenerateFinalAmendment = async (selectedProposal: ProposalEntry | EvaluatedProposal) => {
    const apiKey = getApiKey();
    if (!apiKey) {
      alert('Bitte geben Sie einen API Key ein. Nutzen Sie hierfür die Seitenleiste.');
      return;
    }

    setLoading(true);
    setError(null);
    addLog('==== GENERATE FINAL AMENDMENT ====');
    
    try {
      const finalText = await apiClient.generateFinalAmendment(
        state.taskDescription,
        selectedProposal,
        state.relevantNorms || [],
        apiKey,
        state.selectedModel,
        customAdjustments || undefined
      );
      
      setFinalAmendment(finalText);
      addLog(`Final amendment generated. Length: ${finalText.length} characters`);
    } catch (error) {
      console.error('Error generating final amendment:', error);
      
      if (error instanceof Error && error.message === 'SERVER_ERROR') {
        const errorMessage = 'Serverfehler: Es ist ein interner Serverfehler aufgetreten. Bitte versuchen Sie es später erneut oder kontaktieren Sie den Support.';
        setError(errorMessage);
        addLog(`Error generating final amendment: ${errorMessage}`);
      } else {
        const errorMessage = `Fehler beim Generieren des finalen Entwurfs: ${error}`;
        setError(errorMessage);
        addLog(`Error generating final amendment: ${errorMessage}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateFromManual = async () => {
    if (!manualNorm || !manualProposal) {
      alert('Bitte geben Sie sowohl die betroffene Rechtsnorm als auch einen Änderungsvorschlag ein.');
      return;
    }

    const manualProposalEntry: ProposalEntry = {
      proposalTitle: manualNorm,
      description: manualProposal,
      affectedNorms: []
    };

    await handleGenerateFinalAmendment(manualProposalEntry);
  };

  const downloadText = (text: string, filename: string) => {
    const element = document.createElement('a');
    const file = new Blob([text], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = filename;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const handleBack = () => {
    setCurrentTab(3);
  };

  // Determine what proposals are available
  const hasEvaluatedProposals = state.evaluatedProposals && state.evaluatedProposals.length > 0;
  const hasAmendmentProposals = state.amendmentProposals && state.amendmentProposals.length > 0;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">5. Entscheidung und Finalisierung</h2>
      
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

      {/* Evaluated Proposals Path */}
      {hasEvaluatedProposals && (
        <div className="space-y-4">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Wählen Sie einen Vorschlag aus:
            </label>
            <select
              value={selectedProposalIndex}
              onChange={(e) => setSelectedProposalIndex(parseInt(e.target.value))}
              className="block w-full max-w-md px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {state.evaluatedProposals!.map((proposal, index) => (
                <option key={index} value={index}>
                  Vorschlag {index + 1}: {proposal.proposalTitle}
                </option>
              ))}
            </select>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Ausgewählter Vorschlag:</h3>
            <p className="text-gray-600">
              <strong>Betroffene Rechtsnorm:</strong> {state.evaluatedProposals![selectedProposalIndex]?.proposalTitle}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Optionale Anpassungen:
            </label>
            <textarea
              value={customAdjustments}
              onChange={(e) => setCustomAdjustments(e.target.value)}
              rows={4}
              placeholder="Geben Sie weitere Anpassungswünsche ein (optional):"
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <button
            onClick={() => handleGenerateFinalAmendment(state.evaluatedProposals![selectedProposalIndex])}
            disabled={loading}
            className="px-8 py-3 bg-orange-300 text-gray-800 rounded-xl hover:bg-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 transition-all duration-200 font-semibold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                <span>Generiere finalen Entwurf...</span>
              </div>
            ) : (
              'Finalen Entwurf generieren'
            )}
          </button>
        </div>
      )}

      {/* Amendment Proposals Path (skipped evaluation) */}
      {!hasEvaluatedProposals && hasAmendmentProposals && (
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-blue-800">
              Sie haben die Evaluierung übersprungen. Wählen Sie eine der entwickelten Alternativen aus.
            </p>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Wählen Sie einen Vorschlag aus:
            </label>
            <select
              value={selectedProposalIndex}
              onChange={(e) => setSelectedProposalIndex(parseInt(e.target.value))}
              className="block w-full max-w-md px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {state.amendmentProposals!.map((proposal, index) => (
                <option key={index} value={index}>
                  Alternative {index + 1}: {proposal.proposalTitle}
                </option>
              ))}
            </select>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Ausgewählter Vorschlag:</h3>
            <p className="text-gray-600 mb-2">
              <strong>Alternative:</strong> {state.amendmentProposals![selectedProposalIndex]?.proposalTitle}
            </p>
            <p className="text-gray-600 mb-2">
              <strong>Beschreibung:</strong> {state.amendmentProposals![selectedProposalIndex]?.description}
            </p>
            <p className="text-gray-600">
              <strong>Betroffene Rechtsnormen:</strong> {
                state.amendmentProposals![selectedProposalIndex]?.affectedNorms.map(norm => 
                  `${norm.jurabk} ${norm.enbez}`
                ).join(', ')
              }
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Optionale Anpassungen:
            </label>
            <textarea
              value={customAdjustments}
              onChange={(e) => setCustomAdjustments(e.target.value)}
              rows={4}
              placeholder="Geben Sie weitere Anpassungswünsche ein (optional):"
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <button
            onClick={() => handleGenerateFinalAmendment(state.amendmentProposals![selectedProposalIndex])}
            disabled={loading}
            className="px-8 py-3 bg-orange-300 text-gray-800 rounded-xl hover:bg-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 transition-all duration-200 font-semibold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                <span>Generiere finalen Entwurf...</span>
              </div>
            ) : (
              'Finalen Entwurf generieren'
            )}
          </button>
        </div>
      )}

      {/* Manual Input Path (skipped everything) */}
      {!hasEvaluatedProposals && !hasAmendmentProposals && (
        <div className="space-y-4">
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <p className="text-orange-800">
              Sie haben alle vorherigen Schritte übersprungen. Bitte geben Sie die Informationen manuell ein.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Betroffene Rechtsnorm:
            </label>
            <input
              type="text"
              value={manualNorm}
              onChange={(e) => setManualNorm(e.target.value)}
              placeholder="z.B. EStG § 21"
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Änderungsvorschlag:
            </label>
            <textarea
              value={manualProposal}
              onChange={(e) => setManualProposal(e.target.value)}
              rows={6}
              placeholder="Beschreiben Sie den gewünschten Änderungsvorschlag..."
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Optionale Anpassungen:
            </label>
            <textarea
              value={customAdjustments}
              onChange={(e) => setCustomAdjustments(e.target.value)}
              rows={4}
              placeholder="Geben Sie weitere Anpassungswünsche ein (optional):"
              className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <button
            onClick={handleGenerateFromManual}
            disabled={loading || !manualNorm || !manualProposal}
            className="px-8 py-3 bg-orange-300 text-gray-800 rounded-xl hover:bg-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 transition-all duration-200 font-semibold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                <span>Generiere finalen Entwurf...</span>
              </div>
            ) : (
              'Finalen Entwurf generieren'
            )}
          </button>
        </div>
      )}

      {/* Final Amendment Result */}
      {state.finalAmendment && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Finaler Änderungsentwurf:</h3>
          <p className="text-sm text-gray-600">Änderungen sind mit [] hervorgehoben.</p>
          
          <div className="bg-gray-50 border border-gray-300 rounded-lg p-4">
            <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono">
              {state.finalAmendment}
            </pre>
          </div>

          <button
            onClick={() => downloadText(state.finalAmendment!, 'aenderungsentwurf.txt')}
            className="px-8 py-3 bg-gradient-to-r from-slate-600 to-slate-700 text-white rounded-xl hover:from-slate-700 hover:to-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 transition-all duration-200 font-semibold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Als Textdatei speichern
          </button>
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-start pt-4">
        <button
          onClick={handleBack}
          className="px-8 py-3 bg-gradient-to-r from-slate-600 to-slate-700 text-white rounded-xl hover:from-slate-700 hover:to-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 transition-all duration-200 font-semibold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Zurück
        </button>
      </div>
    </div>
  );
}