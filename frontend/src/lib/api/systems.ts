import type { System } from '@/lib/domain/types';
import { fetchJson } from './client';

export interface CreateSystemPayload {
  name: string;
  shortName: string;
  launchCmd: string;
}

export function listSystems() {
  return fetchJson<System[]>('/systems');
}

export function createSystem(payload: CreateSystemPayload) {
  return fetchJson<System>('/systems', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
