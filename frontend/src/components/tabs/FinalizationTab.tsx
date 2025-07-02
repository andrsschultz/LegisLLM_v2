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
    setExpenditure,
    setCurrentTab,
    addLog 
  } = useApp();
  
  const [loading, setLoading] = useState(false);
  const [expenditureLoading, setExpenditureLoading] = useState(false);
  const [selectedProposalIndex, setSelectedProposalIndex] = useState(0);
  const [customAdjustments, setCustomAdjustments] = useState('');
  const [manualNorm, setManualNorm] = useState('');
  const [manualProposal, setManualProposal] = useState('');

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
      addLog(`Error generating final amendment: ${error}`);
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

  const handleCalculateExpenditure = async () => {
    const apiKey = getApiKey();
    if (!apiKey) {
      alert('Bitte geben Sie einen API Key ein. Nutzen Sie hierfür die Seitenleiste.');
      return;
    }

    if (!state.finalAmendment || !state.relevantNorms) {
      alert('Finaler Entwurf und relevante Normen sind erforderlich für die Erfüllungsaufwand-Berechnung.');
      return;
    }

    // Determine which proposal to use
    let selectedProposal: ProposalEntry | EvaluatedProposal;
    if (hasEvaluatedProposals) {
      selectedProposal = state.evaluatedProposals![selectedProposalIndex];
    } else if (hasAmendmentProposals) {
      selectedProposal = state.amendmentProposals![selectedProposalIndex];
    } else {
      // Manual proposal
      selectedProposal = {
        proposalTitle: manualNorm,
        description: manualProposal,
        affectedNorms: []
      };
    }

    setExpenditureLoading(true);
    addLog('==== CALCULATE ERFÜLLUNGSAUFWAND ====');
    
    try {
      const expenditureEntries = await apiClient.calculateExpenditure(
        state.taskDescription,
        state.relevantNorms,
        selectedProposal,
        state.finalAmendment,
        apiKey,
        state.selectedModel
      );
      
      setExpenditure(expenditureEntries);
      addLog(`Erfüllungsaufwand calculated. Found ${expenditureEntries.length} cost entries.`);
    } catch (error) {
      console.error('Error calculating expenditure:', error);
      addLog(`Error calculating expenditure: ${error}`);
    } finally {
      setExpenditureLoading(false);
    }
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

          <div className="flex flex-wrap gap-4">
            <button
              onClick={() => downloadText(state.finalAmendment!, 'aenderungsentwurf.txt')}
              className="px-8 py-3 bg-gradient-to-r from-slate-600 to-slate-700 text-white rounded-xl hover:from-slate-700 hover:to-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 transition-all duration-200 font-semibold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Als Textdatei speichern
            </button>
            
            <button
              onClick={handleCalculateExpenditure}
              disabled={expenditureLoading}
              className="px-8 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-700 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-200 font-semibold shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {expenditureLoading ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                  <span>Berechne Erfüllungsaufwand...</span>
                </div>
              ) : (
                'Erfüllungsaufwand berechnen'
              )}
            </button>
          </div>
        </div>
      )}

      {/* Expenditure Results */}
      {state.expenditure && state.expenditure.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Erfüllungsaufwand (Compliance Costs)</h3>
          <p className="text-sm text-gray-600">
            Berechnung der jährlichen Kosten durch die Änderung für verschiedene Adressatengruppen.
          </p>
          
          <div className="space-y-4">
            {state.expenditure.map((entry, index) => (
              <div key={index} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                <div className="flex items-start justify-between mb-4">
                  <h4 className="text-md font-semibold text-gray-900">{entry.title}</h4>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    entry.cost_category === 'high' 
                      ? 'bg-red-100 text-red-800' 
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {entry.cost_category === 'high' ? 'Hoch (>100.000 €/Jahr)' : 'Niedrig (≤100.000 €/Jahr)'}
                  </span>
                </div>
                
                <p className="text-gray-700 mb-4">{entry.description}</p>
                
                <details className="mb-4">
                  <summary className="cursor-pointer text-blue-600 hover:text-blue-800 font-medium text-sm">
                    Vollständige Analyse anzeigen
                  </summary>
                  <div className="mt-2 p-3 bg-gray-50 rounded-lg border border-gray-200">
                    <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                      {entry.full_text}
                    </pre>
                    <div className="mt-3 pt-3 border-t border-gray-300">
                      <button
                        onClick={() => downloadText(entry.full_text, `erfuellungsaufwand_${entry.title.replace(/[^a-zA-Z0-9]/g, '_')}.txt`)}
                        className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all duration-200 font-medium shadow-sm"
                      >
                        Vollständige Analyse als Datei speichern
                      </button>
                    </div>
                  </div>
                </details>
                
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-blue-50 p-3 rounded-lg">
                    <div className="text-sm font-medium text-blue-900">Bürgerinnen und Bürger</div>
                    <div className="text-lg font-bold text-blue-700">
                      {entry.citizens_cost_eur.toLocaleString('de-DE', {
                        style: 'currency',
                        currency: 'EUR',
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 0
                      })}
                    </div>
                    <div className="text-xs text-blue-600">pro Jahr</div>
                  </div>
                  
                  <div className="bg-green-50 p-3 rounded-lg">
                    <div className="text-sm font-medium text-green-900">Wirtschaft</div>
                    <div className="text-lg font-bold text-green-700">
                      {entry.business_cost_eur.toLocaleString('de-DE', {
                        style: 'currency',
                        currency: 'EUR',
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 0
                      })}
                    </div>
                    <div className="text-xs text-green-600">pro Jahr</div>
                  </div>
                  
                  <div className="bg-orange-50 p-3 rounded-lg">
                    <div className="text-sm font-medium text-orange-900">Verwaltung</div>
                    <div className="text-lg font-bold text-orange-700">
                      {entry.administration_cost_eur.toLocaleString('de-DE', {
                        style: 'currency',
                        currency: 'EUR',
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 0
                      })}
                    </div>
                    <div className="text-xs text-orange-600">pro Jahr</div>
                  </div>
                  
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <div className="text-sm font-medium text-gray-900">Gesamtkosten</div>
                    <div className="text-lg font-bold text-gray-700">
                      {entry.total_cost_eur.toLocaleString('de-DE', {
                        style: 'currency',
                        currency: 'EUR',
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 0
                      })}
                    </div>
                    <div className="text-xs text-gray-600">pro Jahr</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
        
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-blue-800 text-sm">
              <strong>Hinweis:</strong> Die Erfüllungsaufwand-Berechnung basiert auf geschätzten Werten und sollte 
              vor der finalen Entscheidung durch weitere Datenquellen validiert werden.
            </p>
          </div>
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