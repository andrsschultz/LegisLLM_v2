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
  const [expandedNorms, setExpandedNorms] = useState<Set<number>>(new Set());

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

  const toggleNormExpansion = (index: number) => {
    setExpandedNorms(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  const formatTextWithSuperscript = (text: string) => {
    // Split text by <SUP> markers and create React elements
    const parts = text.split(/(<SUP>\d+<\/SUP>)/);
    
    return parts.map((part, index) => {
      // Check if this part is a SUP marker
      const supMatch = part.match(/^<SUP>(\d+)<\/SUP>$/);
      if (supMatch) {
        const number = supMatch[1];
        return (
          <sup key={index} className="text-xs font-medium text-blue-600">
            {number}
          </sup>
        );
      }
      // Regular text part
      return part;
    });
  };

  const formatNormContent = (text: string) => {
    if (!text) return null;

    // Split by the first line break to separate title from content
    const lines = text.split('\n');
    const firstLine = lines[0];
    const restOfContent = lines.slice(1).join('\n');

    // Check if first line is a title (contains § and text)
    const titleMatch = firstLine.match(/^(§\s*\d+[a-z]?)\s*(.*)$/);
    
    if (titleMatch) {
      const sectionNumber = titleMatch[1];
      const title = titleMatch[2];
      
      return (
        <div className="space-y-6">
          {/* Section Title */}
          <div className="border-b-2 border-blue-200 pb-4">
            <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-3">
              <span className="inline-flex items-center justify-center text-xl font-bold text-white bg-gradient-to-r from-blue-600 to-blue-700 px-4 py-2 rounded-lg shadow-sm">
                {sectionNumber}
              </span>
              <h3 className="text-lg font-bold text-gray-900 leading-tight">
                {title}
              </h3>
            </div>
          </div>
          
          {/* Content */}
          <div className="prose prose-sm max-w-none">
            <div className="text-gray-800 leading-7 font-serif whitespace-pre-wrap">
              {formatContentParagraphs(restOfContent)}
            </div>
          </div>
        </div>
      );
    }

    // Fallback: no title detected, format as regular content
    return (
      <div className="prose prose-sm max-w-none">
        <div className="text-gray-800 leading-7 font-serif whitespace-pre-wrap">
          {formatContentParagraphs(text)}
        </div>
      </div>
    );
  };

  const formatContentParagraphs = (text: string) => {
    // Split content into paragraphs and format each
    const paragraphs = text.split(/\n\s*\n/);
    
    return paragraphs.map((paragraph, index) => {
      if (!paragraph.trim()) return null;
      
      // Check if paragraph starts with a number in parentheses like (1), (2), etc.
      const paragraphMatch = paragraph.match(/^(\(\d+\))\s*(.*)/s);
      
      if (paragraphMatch) {
        const paragraphNum = paragraphMatch[1];
        const paragraphContent = paragraphMatch[2];
        
        return (
          <div key={index} className="mb-6 text-gray-800">
            {paragraphNum} {formatTextWithSuperscript(paragraphContent)}
          </div>
        );
      }
      
      // Regular paragraph without number
      return (
        <div key={index} className="mb-4 text-gray-800">
          {formatTextWithSuperscript(paragraph)}
        </div>
      );
    }).filter(Boolean);
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
          
          {/* Individual Collapsible Norm Cards */}
          <div className="space-y-4">
            {state.relevantNorms.map((norm, index) => (
              <div key={index} className="bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden">
                {/* Clickable Header */}
                <button
                  onClick={() => toggleNormExpansion(index)}
                  className="w-full px-6 py-4 bg-gradient-to-r from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 text-left flex items-center justify-between transition-all duration-200 border-b border-blue-100"
                >
                  <div className="flex items-center space-x-3">
                    <div className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-semibold">
                      {norm.jurabk}
                    </div>
                    <span className="font-semibold text-blue-900 text-lg">
                      {norm.enbez} {norm.P ? `Abs. ${norm.P}` : ''}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-blue-600 font-medium">
                      {expandedNorms.has(index) ? 'Einklappen' : 'Volltext anzeigen'}
                    </span>
                    <svg
                      className={`w-5 h-5 text-blue-600 transition-transform duration-300 ${
                        expandedNorms.has(index) ? 'rotate-180' : ''
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </button>
                
                {/* Collapsible Content */}
                {expandedNorms.has(index) && (
                  <div className="px-6 py-6 bg-white">
                    <div className="prose prose-sm max-w-none">
                      {formatNormContent(norm.wording || '')}
                    </div>
                  </div>
                )}
              </div>
            ))}
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