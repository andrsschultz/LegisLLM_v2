'use client';

import React, { useState, useEffect } from 'react';
import { useApp } from '@/contexts/AppContext';
import { apiClient } from '@/lib/api';
import { getStoredApiKey, setStoredApiKey } from '@/lib/apiKeyUtils';
import { Model } from '@/types';

interface OrganizedModels {
  deepinfra: {
    recommended: Model[];
    additional: Model[];
  };
}

export default function ModelSelector() {
  const { state, setSelectedModel, setAvailableModels } = useApp();
  const [loading, setLoading] = useState(true);
  const [deepinfraApiKey, setDeepinfraApiKey] = useState('');
  const [organizedModels, setOrganizedModels] = useState<OrganizedModels | null>(null);

  useEffect(() => {
    loadModels();
    setDeepinfraApiKey(getStoredApiKey('deepinfra_api_key'));
  }, []);

  const loadModels = async () => {
    try {
      const storedDeepinfraKey = getStoredApiKey('deepinfra_api_key');

      let organized: any = { deepinfra: { recommended: [], additional: [] } };
      let allModels: any[] = [];
      let defaultModel: string | null = null;

      if (storedDeepinfraKey) {
        try {
          const deepinfraResults = await apiClient.fetchOrganizedModels(storedDeepinfraKey);
          organized.deepinfra = deepinfraResults.organized.deepinfra || { recommended: [], additional: [] };
          defaultModel = deepinfraResults.default;

          const deepinfraAllResults = await apiClient.fetchModels(storedDeepinfraKey);
          allModels = deepinfraAllResults.models.filter(m => m.provider === 'DeepInfra');
        } catch (error) {
          console.log('DeepInfra key failed:', error);
        }
      }

      setOrganizedModels(organized);
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

  const handleApiKeyChange = (value: string) => {
    setDeepinfraApiKey(value);
    setStoredApiKey('deepinfra_api_key', value);

    if (value.length > 10) {
      loadModels();
    }
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
        <h3 className="text-lg font-semibold text-slate-800">Modell-Auswahl</h3>
      </div>

      {/* API Key Input */}
      <div className="space-y-4 mb-6">
        <div>
          {!deepinfraApiKey ? (
            <div className="flex items-center space-x-2 text-orange-600 mb-2">
              <span className="text-sm">DeepInfra API Key eingeben:</span>
            </div>
          ) : (
            <div className="flex items-center space-x-2 text-green-600 mb-2">
              <span className="text-sm">DeepInfra API Key geladen</span>
            </div>
          )}
          <input
            type="password"
            placeholder="DeepInfra API Key"
            value={deepinfraApiKey}
            onChange={(e) => handleApiKeyChange(e.target.value)}
            className="block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-slate-500 text-sm"
          />
        </div>
      </div>

      {/* Model Selection */}
      {organizedModels ? (
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Modell:
          </label>

          <select
            value={state.selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="block w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm bg-white focus:outline-none focus:ring-2 focus:ring-slate-500 focus:border-slate-500 text-sm"
          >
            {organizedModels.deepinfra.recommended.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name}
              </option>
            ))}
          </select>
        </div>
      ) : (
        <div className="text-orange-600 text-sm">
          Keine Modelle verfügbar. Bitte Backend prüfen.
        </div>
      )}
    </div>
  );
}
