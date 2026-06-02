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

export function getStoredApiKey(key: 'deepinfra_api_key'): string {
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
  key: 'deepinfra_api_key',
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
 * Get the API key for the selected model (always DeepInfra)
 */
export function getApiKeyForModel(selectedModelId: string, availableModels: Model[]): string {
  return getStoredApiKey('deepinfra_api_key');
}

/**
 * Check if the required API key is available
 */
export function hasRequiredApiKey(selectedModelId: string, availableModels: Model[]): boolean {
  const apiKey = getApiKeyForModel(selectedModelId, availableModels);
  return apiKey.length > 0;
}
