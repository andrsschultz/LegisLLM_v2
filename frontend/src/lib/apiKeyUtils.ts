import { Model } from '@/types';

function getBrowserStorage(): Storage | null {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    const storage = window.localStorage;
    if (
      storage &&
      typeof storage.getItem === 'function' &&
      typeof storage.setItem === 'function'
    ) {
      return storage;
    }
  } catch {
    return null;
  }

  return null;
}

export function getStoredApiKey(key: 'openai_api_key' | 'deepinfra_api_key'): string {
  const storage = getBrowserStorage();
  if (!storage) {
    return '';
  }

  try {
    return storage.getItem(key) || '';
  } catch {
    return '';
  }
}

export function setStoredApiKey(
  key: 'openai_api_key' | 'deepinfra_api_key',
  value: string
): void {
  const storage = getBrowserStorage();
  if (!storage) {
    return;
  }

  try {
    storage.setItem(key, value);
  } catch {
    // Ignore storage write failures and keep the UI responsive.
  }
}

/**
 * Get the appropriate API key based on the selected model and available models
 */
export function getApiKeyForModel(selectedModelId: string, availableModels: Model[]): string {
  const selectedModel = availableModels.find(m => m.id === selectedModelId);
  const provider = selectedModel?.provider?.toLowerCase();
  
  if (provider === 'deepinfra') {
    return getStoredApiKey('deepinfra_api_key');
  }
  
  // Default to OpenAI for OpenAI models or unknown providers
  return getStoredApiKey('openai_api_key');
}

/**
 * Check if any required API key is available for the selected model
 */
export function hasRequiredApiKey(selectedModelId: string, availableModels: Model[]): boolean {
  const apiKey = getApiKeyForModel(selectedModelId, availableModels);
  return apiKey.length > 0;
}
