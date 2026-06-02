'use client';

import React, { useState } from 'react';
import { useApp } from '@/contexts/AppContext';
import { apiClient } from '@/lib/api';
import { getApiKeyForModel } from '@/lib/apiKeyUtils';

export default function EntwurfTab() {
  const { state, setGeneratedEntwurf, addLog } = useApp();
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aenderungsbefehle, setAenderungsbefehle] = useState<string>('');
  const [isGeneratingAenderungsbefehle, setIsGeneratingAenderungsbefehle] = useState(false);
  const [isGeneratingEntwurf, setIsGeneratingEntwurf] = useState(false);

  const downloadGesetzesentwurf = () => {
    if (!state.generatedEntwurf) return;
    
    const content = state.generatedEntwurf;
    const element = document.createElement('a');
    const file = new Blob([content], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = 'gesetzesentwurf.txt';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const generateAenderungsbefehle = async () => {
    if (!state.finalAmendment || !state.selectedModel || !state.taskDescription) {
      setError('Finalamendment, Modell und Aufgabenbeschreibung sind erforderlich');
      return;
    }

    const apiKey = getApiKeyForModel(state.selectedModel, state.availableModels);
    if (!apiKey) {
      setError('API-Schlüssel erforderlich');
      return;
    }

    setIsGeneratingAenderungsbefehle(true);
    setError(null);

    try {
      addLog('Generiere Änderungsbefehle...');

      const aenderungsbefehlResponse = await apiClient.generateAenderungsbefehle(
        state.taskDescription,
        state.finalAmendment,
        apiKey,
        state.selectedModel
      );

      if (!aenderungsbefehlResponse.response) {
        throw new Error('Keine Änderungsbefehle vom Server erhalten');
      }

      const generatedAenderungsbefehle = aenderungsbefehlResponse.response;
      setAenderungsbefehle(generatedAenderungsbefehle);
      addLog('Änderungsbefehle erfolgreich generiert');

    } catch (err: any) {
      if (err.message === 'REQUEST_CANCELLED') {
        const errorMessage = 'Anfrage wurde abgebrochen.';
        setError(errorMessage);
        addLog(`Request cancelled: ${errorMessage}`);
      } else {
        const errorMessage = err instanceof Error ? err.message : 'Unbekannter Fehler beim Generieren der Änderungsbefehle';
        setError(errorMessage);
        addLog(`Fehler: ${errorMessage}`);
      }
    } finally {
      setIsGeneratingAenderungsbefehle(false);
    }
  };

  const generateGesetzesentwurf = async () => {
    if (!aenderungsbefehle || !state.selectedModel || !state.taskDescription) {
      setError('Änderungsbefehle, Modell und Aufgabenbeschreibung sind erforderlich');
      return;
    }

    const apiKey = getApiKeyForModel(state.selectedModel, state.availableModels);
    if (!apiKey) {
      setError('API-Schlüssel erforderlich');
      return;
    }

    setIsGeneratingEntwurf(true);
    setError(null);

    try {
      addLog('Erstelle Gesetzesentwurf...');

      const entwurfResponse = await apiClient.generateEntwurfContent(
        state.taskDescription,
        aenderungsbefehle,
        apiKey,
        state.selectedModel,
        state.finalAmendment || undefined
      );

      if (entwurfResponse.response) {
        setGeneratedEntwurf(entwurfResponse.response);
        addLog('Gesetzesentwurf erfolgreich generiert');
      } else {
        throw new Error('Keine Antwort vom Server für Gesetzesentwurf erhalten');
      }

    } catch (err: any) {
      if (err.message === 'REQUEST_CANCELLED') {
        const errorMessage = 'Anfrage wurde abgebrochen.';
        setError(errorMessage);
        addLog(`Request cancelled: ${errorMessage}`);
      } else {
        const errorMessage = err instanceof Error ? err.message : 'Unbekannter Fehler beim Generieren des Gesetzesentwurfs';
        setError(errorMessage);
        addLog(`Fehler: ${errorMessage}`);
      }
    } finally {
      setIsGeneratingEntwurf(false);
    }
  };

  const handleCancelAenderungsbefehle = () => {
    const cancelled = apiClient.cancelRequest('aenderungsbefehle');
    if (cancelled) {
      setIsGeneratingAenderungsbefehle(false);
      setError('Anfrage wurde abgebrochen.');
      addLog('Änderungsbefehle request cancelled by user');
    }
  };

  const handleCancelEntwurf = () => {
    const cancelled = apiClient.cancelRequest('entwurf');
    if (cancelled) {
      setIsGeneratingEntwurf(false);
      setError('Anfrage wurde abgebrochen.');
      addLog('Entwurf request cancelled by user');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-slate-800 mb-2">
              Gesetzesentwurf generieren
            </h2>
            <p className="text-slate-600">
              Erstelle einen vollständigen deutschen Gesetzesentwurf basierend auf den finalisierten Änderungen.
            </p>
          </div>
          <div className="text-4xl">📋</div>
        </div>
      </div>

      {/* Amendment Summary */}
      {state.finalAmendment && (
        <div className="bg-slate-50 rounded-xl border border-slate-200 p-6">
          <h3 className="text-lg font-semibold text-slate-800 mb-4">
            Zu verarbeitende Änderungen ({state.finalAmendment.length})
          </h3>
          <div className="space-y-3">
            {state.finalAmendment.map((amendment, index) => (
              <div key={index} className="bg-white rounded-lg p-4 border border-slate-200">
                <div className="font-medium text-slate-800">
                  {amendment.originalNorm.enbez} {amendment.originalNorm.jurabk}
                  {amendment.originalNorm.P && ` Absatz ${amendment.originalNorm.P}`}
                </div>
                <div className="text-sm text-slate-600 mt-1">
                  {amendment.amendedNorm.amendmentDescription || 'Ersetzung'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Step 1: Generate Änderungsbefehle */}
      <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-800 mb-2">
              Schritt 1: Änderungsbefehle generieren
            </h3>
            <p className="text-slate-600">
              Erstelle strukturierte Änderungsbefehle basierend auf den finalisierten Änderungen.
            </p>
          </div>
          <div className="flex gap-4">
            <button
              onClick={generateAenderungsbefehle}
              disabled={isGeneratingAenderungsbefehle || !state.finalAmendment || !state.selectedModel || !state.taskDescription}
              className="px-6 py-3 bg-slate-600 text-white rounded-lg hover:bg-slate-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {isGeneratingAenderungsbefehle ? 'Generiere...' : 'Änderungsbefehle erstellen'}
            </button>
            {isGeneratingAenderungsbefehle && (
              <button
                onClick={handleCancelAenderungsbefehle}
                className="px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-all duration-200 font-medium"
              >
                Abbrechen
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Generated Änderungsbefehle Display */}
      {aenderungsbefehle && (
        <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-800">
              Generierte Änderungsbefehle
            </h3>
            <button
              onClick={() => navigator.clipboard.writeText(aenderungsbefehle)}
              className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors text-sm"
            >
              📋 Kopieren
            </button>
          </div>
          <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
            <pre className="whitespace-pre-wrap text-sm text-slate-800 font-mono">
              {aenderungsbefehle}
            </pre>
          </div>
        </div>
      )}

      {/* Step 2: Generate Gesetzesentwurf (only shown after Änderungsbefehle are generated) */}
      {aenderungsbefehle && (
        <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-slate-800 mb-2">
                Schritt 2: Gesetzesentwurf erstellen
              </h3>
              <p className="text-slate-600">
                Erstelle einen vollständigen Gesetzesentwurf basierend auf den generierten Änderungsbefehlen.
              </p>
            </div>
            <div className="flex gap-4">
              <button
                onClick={generateGesetzesentwurf}
                disabled={isGeneratingEntwurf || !aenderungsbefehle}
                className="px-6 py-3 bg-slate-600 text-white rounded-lg hover:bg-slate-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors font-medium"
              >
                {isGeneratingEntwurf ? 'Generiere...' : 'Gesetzesentwurf erstellen'}
              </button>
              {isGeneratingEntwurf && (
                <button
                  onClick={handleCancelEntwurf}
                  className="px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-all duration-200 font-medium"
                >
                  Abbrechen
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <div className="flex items-center space-x-2">
            <span className="text-red-500">⚠️</span>
            <span className="text-red-700 font-medium">Fehler:</span>
          </div>
          <p className="text-red-600 mt-1">{error}</p>
        </div>
      )}


      {/* Generated Entwurf Display */}
      {state.generatedEntwurf && (
        <div className="bg-white rounded-xl shadow-lg border border-slate-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-800">
              Generierter Gesetzesentwurf
            </h3>
            <div className="flex space-x-2">
              <button
                onClick={() => navigator.clipboard.writeText(state.generatedEntwurf || '')}
                className="px-4 py-2 bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors text-sm"
              >
                📋 Kopieren
              </button>
              <button
                onClick={downloadGesetzesentwurf}
                className="px-6 py-2 bg-gradient-to-r from-slate-600 to-slate-700 text-white rounded-xl hover:from-slate-700 hover:to-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-500 focus:ring-offset-2 transition-all duration-200 font-semibold shadow-lg"
              >
                Als Textdatei speichern
              </button>
            </div>
          </div>
          <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
            <pre className="whitespace-pre-wrap text-sm text-slate-800 font-mono">
              {state.generatedEntwurf}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}