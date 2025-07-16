'use client';

import React, { useState } from 'react';
import { useApp } from '@/contexts/AppContext';
import { apiClient } from '@/lib/api';
import { getApiKeyForModel } from '@/lib/apiKeyUtils';

export default function ContextIdentificationTab() {
  const { 
    state, 
    setRelevantNorms, 
    setCurrentTab, 
    setMultistepReasoning,
    addLog 
  } = useApp();
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    addLog('==== STEP 2: IDENTIFY RELEVANT NORMS ====');
    
    try {
      const norms = await apiClient.identifyRelevantNorms(
        state.taskDescription,
        apiKey,
        state.selectedModel,
        state.multistepReasoning
      );
      
      setRelevantNorms(norms);
      addLog(`Successfully identified ${norms.length} relevant norms`);
    } catch (error) {
      console.error('Error identifying context:', error);
      
      if (error instanceof Error && error.message === 'SERVER_ERROR') {
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

      {/* Action Button */}
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

      {/* Results */}
      {state.relevantNorms && state.relevantNorms.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Identifizierte Rechtsnormen:</h3>
          
          {/* Norm Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {state.relevantNorms.map((norm, index) => (
              <div key={index} className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="font-medium text-blue-900">
                  {norm.jurabk} {norm.enbez} {norm.P ? `Abs. ${norm.P}` : ''}
                </p>
              </div>
            ))}
          </div>

          {/* Full Text */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Volltext der relevanten Rechtsnormen
            </label>
            <textarea
              value={state.relevantNorms.map(norm => 
                `${norm.jurabk} ${norm.enbez}${norm.P ? ` Abs. ${norm.P}` : ''}:\n${norm.wording || ''}\n\n`
              ).join('')}
              readOnly
              rows={8}
              className="block w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-sm font-mono"
            />
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