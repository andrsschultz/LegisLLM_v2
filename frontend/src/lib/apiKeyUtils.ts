import { Model } from '@/types';

/**
 * Get the appropriate API key based on the selected model and available models
 */
export function getApiKeyForModel(selectedModelId: string, availableModels: Model[]): string {
  const selectedModel = availableModels.find(m => m.id === selectedModelId);
  const provider = selectedModel?.provider?.toLowerCase();
  
  if (provider === 'deepinfra') {
    return localStorage.getItem('deepinfra_api_key') || '';
  }
  
  // Default to OpenAI for OpenAI models or unknown providers
  return localStorage.getItem('openai_api_key') || '';
}

/**
 * Check if any required API key is available for the selected model
 */
export function hasRequiredApiKey(selectedModelId: string, availableModels: Model[]): boolean {
  const apiKey = getApiKeyForModel(selectedModelId, availableModels);
  return apiKey.length > 0;
}