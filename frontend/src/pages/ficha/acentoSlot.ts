import { useSyncExternalStore } from 'react';
import type { AccentSlot } from './types';

/**
 * Próximo acento a completar (0 = primario, 1 = secundario) al tomar un color de la carátula.
 * Una sola fuente de verdad: el Hero (colores predominantes) y Presentación (clic en la
 * carátula) alternan el mismo contador y no pueden desfasarse.
 */
let siguiente: AccentSlot = 0;
const oyentes = new Set<() => void>();

function emitir() {
  oyentes.forEach((oyente) => oyente());
}

function suscribir(oyente: () => void) {
  oyentes.add(oyente);
  return () => { oyentes.delete(oyente); };
}

export function leerProximoAcento(): AccentSlot {
  return siguiente;
}

/** Devuelve el slot a completar ahora y deja el otro como próximo. */
export function consumirProximoAcento(): AccentSlot {
  const actual = siguiente;
  siguiente = actual === 0 ? 1 : 0;
  emitir();
  return actual;
}

export function reiniciarProximoAcento() {
  if (siguiente === 0) return;
  siguiente = 0;
  emitir();
}

export function useProximoAcento(): AccentSlot {
  return useSyncExternalStore(suscribir, leerProximoAcento, leerProximoAcento);
}
