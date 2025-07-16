'use client';

import React, { useState, useEffect } from 'react';
import { useApp } from '@/contexts/AppContext';
import { apiClient } from '@/lib/api';
import { Model } from '@/types';

interface OrganizedModels {
  openai: {
    recommended: Model[];
    additional: Model[];
  };
  deepinfra: {
    recommended: Model[];
    additional: Model[];
  };
}

export default function ModelSelector() {
  const { state, setSelectedModel, setAvailableModels } = useApp();
  const [loading, setLoading] = useState(true);
  const [openaiApiKey, setOpenaiApiKey] = useState('');
  const [deepinfraApiKey, setDeepinfraApiKey] = useState('');
  const [organizedModels, setOrganizedModels] = useState<OrganizedModels | null>(null);

  useEffect(() => {
    loadModels();
    // Load API keys from localStorage on client side
    setOpenaiApiKey(localStorage.getItem('openai_api_key') || '');
    setDeepinfraApiKey(localStorage.getItem('deepinfra_api_key') || '');
  }, []);

  const loadModels = async () => {
    try {
      // Get API keys from localStorage
      const storedOpenaiKey = localStorage.getItem('openai_api_key') || '';
      const storedDeepinfraKey = localStorage.getItem('deepinfra_api_key') || '';
      
      let organizedModels: any = { openai: { recommended: [], additional: [] }, deepinfra: { recommended: [], additional: [] } };
      let allModels: any[] = [];
      let defaultModel: string | null = null;
      
      // Try fetching with OpenAI key first
      if (storedOpenaiKey) {
        try {
          const openaiResults = await apiClient.fetchOrganizedModels(storedOpenaiKey);
          organizedModels.openai = openaiResults.organized.openai || { recommended: [], additional: [] };
          defaultModel = openaiResults.default;
          
          const openaiAllResults = await apiClient.fetchModels(storedOpenaiKey);
          allModels = [...allModels, ...openaiAllResults.models.filter(m => m.provider === 'OpenAI')];
        } catch (error) {
          console.log('OpenAI key failed:', error);
        }
      }
      
      // Try fetching with DeepInfra key
      if (storedDeepinfraKey) {
        try {
          const deepinfraResults = await apiClient.fetchOrganizedModels(storedDeepinfraKey);
          organizedModels.deepinfra = deepinfraResults.organized.deepinfra || { recommended: [], additional: [] };
          
          const deepinfraAllResults = await apiClient.fetchModels(storedDeepinfraKey);
          allModels = [...allModels, ...deepinfraAllResults.models.filter(m => m.provider === 'DeepInfra')];
        } catch (error) {
          console.log('DeepInfra key failed:', error);
        }
      }
      
      setOrganizedModels(organizedModels);
      setAvailableModels(allModels);
      
      if (defaultModel && !state.selectedModel) {
        setSelectedModel(defaultModel);
      } else if (allModels.length > 0 && !state.selectedModel) {
        setSelectedModel(allModels[0].id);
      }
    } catch (error) {
      console.error('Error loading models:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApiKeyChange = (key: string, value: string, type: 'openai' | 'deepinfra') => {
    if (type === 'openai') {
      setOpenaiApiKey(value);
      localStorage.setItem('openai_api_key', value);
    } else {
      setDeepinfraApiKey(value);
      localStorage.setItem('deepinfra_api_key', value);
    }
    
    // Reload models when API key changes
    if (value.length > 10) { // Basic validation
      loadModels();
    }
  };

  const getApiKey = (): string => {
    const selectedModelData = state.availableModels.find(m => m.id === state.selectedModel);
    const provider = selectedModelData?.provider?.toLowerCase();
    
    if (provider === 'deepinfra') {
      return deepinfraApiKey;
    }
    return openaiApiKey;
  };

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-slate-50 to-slate-100/70 border border-slate-200/60 rounded-xl p-6 shadow-sm">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-slate-200 rounded w-3/4"></div>
          <div className="h-3 bg-slate-200 rounded w-1/2"></div>
          <div className="h-8 bg-slate-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-slate-50 to-slate-100/70 border border-slate-200/60 rounded-xl p-6 shadow-sm">
      <div className="flex items-center mb-4">
        <span className="text-lg mr-2">🤖</span>
        <h3 className="text-lg font-semibold text-slate-800">Modell-Auswahl</h3>
      </div>
      
      {/* API Key Inputs */}
      <div className="space-y-4 mb-6">
        <div>
          {!openaiApiKey ? (
            <div className="flex items-center space-x-2 text-orange-600 mb-2">
              <span className="text-sm">⚠️</span>
              <span className="text-sm">Enter OpenAI API key:</span>
            </div>
          ) : (
            <div className="flex items-center space-x-2 text-green-600 mb-2">
              <span className="text-sm">✅</span>
              <span className="text-sm">OpenAI API Key loaded</span>
            </div>
          )}
          <input
            type="password"
            placeholder="OpenAI API Key"
            value={openaiApiKey}
            onChange={(e) => handleApiKeyChange('openai_api_key', e.target.value, 'openai')}
            className="block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-slate-500 text-sm"
          />
        </div>

        <div>
          {!deepinfraApiKey ? (
            <div className="flex items-center space-x-2 text-orange-600 mb-2">
              <span className="text-sm">⚠️</span>
              <span className="text-sm">Enter DeepInfra API key:</span>
            </div>
          ) : (
            <div className="flex items-center space-x-2 text-green-600 mb-2">
              <span className="text-sm">✅</span>
              <span className="text-sm">DeepInfra API Key loaded</span>
            </div>
          )}
          <input
            type="password"
            placeholder="DeepInfra API Key"
            value={deepinfraApiKey}
            onChange={(e) => handleApiKeyChange('deepinfra_api_key', e.target.value, 'deepinfra')}
            className="block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-slate-500 text-sm"
          />
        </div>
      </div>

      {/* Model Selection */}
      {organizedModels ? (
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Wählen Sie ein Modell:
          </label>
          
          <select
            value={state.selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-slate-500 text-sm"
          >
            {/* Recommended Models */}
            <optgroup label="Empfohlen">
              {organizedModels.openai.recommended.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name} (OpenAI)
                </option>
              ))}
              {organizedModels.deepinfra.recommended.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name} (DeepInfra)
                </option>
              ))}
            </optgroup>
            
            {/* All OpenAI Models */}
            <optgroup label="Alle Modelle - OpenAI (experimentell)">
              {organizedModels.openai.additional.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </optgroup>
            
            {/* All DeepInfra Models */}
            <optgroup label="Alle Modelle - DeepInfra (experimentell)">
              {organizedModels.deepinfra.additional.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </optgroup>
          </select>
          
          <p className="mt-2 text-sm text-slate-500">
            Empfohlene Modelle bieten die beste Balance aus Leistung und Geschwindigkeit. 
            Alle verfügbaren Modelle sind nach Anbieter gruppiert.
          </p>
        </div>
      ) : (
        <div className="text-orange-600 text-sm">
          ⚠️ Keine Modelle verfügbar. Bitte Backend prüfen.
        </div>
      )}

      {/* Current API Key Status
      {state.selectedModel && (
        <div className="mt-4 p-3 bg-white/60 border border-green-200 rounded-md">
          <p className="text-sm text-gray-700 mb-1">
            <strong>Aktuelles Modell:</strong> {state.availableModels.find(m => m.id === state.selectedModel)?.name}
          </p>
          <div className="flex items-center">
            <span className="text-sm text-gray-700 mr-2"><strong>API Key Status:</strong></span>
            {getApiKey() ? (
              <span className="flex items-center text-sm text-green-600">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-1"></span>
                Verfügbar
              </span>
            ) : (
              <span className="flex items-center text-sm text-red-600">
                <span className="w-2 h-2 bg-red-400 rounded-full mr-1"></span>
                Fehlt
              </span>
            )}
          </div>
        </div>
      )}
      */}
    </div>
  );
}