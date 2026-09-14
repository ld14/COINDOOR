import { fetchJson } from './client';

export interface ConfigValue {
  attractDir: string | null;
}

export function getConfig() {
  return fetchJson<ConfigValue>('/config');
}

export function updateConfig(attractDir: string) {
  return fetchJson<ConfigValue>('/config', {
    method: 'PATCH',
    body: JSON.stringify({ attractDir }),
  });
}
