import { useSyncExternalStore } from 'react';

/**
 * Estado global mínimo del guardado, para que la TopBar lo muestre sin prop drilling
 * (DESIGN_SPEC §4): "Guardando…", "Guardado · hace 4 s" o "Error al guardar — Reintentar".
 *
 * Lo alimenta `useGameMutations` (cada escritura avisa al empezar y al terminar) y el autosave
 * de la ficha (`reportError`). Es un store externo, no estado de React Query, porque lo leen
 * componentes que no comparten árbol con la ficha.
 *
 * Los fallos se recuerdan POR CLAVE (p. ej. `campo:sinopsis`): una escritura posterior que salga
 * bien sobre la misma clave reemplaza al fallo (si no, "Reintentar" pisaría un dato más nuevo con
 * uno viejo), y un éxito sobre otra clave NO borra el error ajeno.
 */
export type SaveStatus =
  | { kind: 'idle'; canRetry: false }
  | { kind: 'saving'; canRetry: false }
  | { kind: 'saved'; savedAt: number; canRetry: false }
  | { kind: 'error'; message: string; canRetry: boolean };

interface Fallo {
  message: string;
  reintentar?: () => void;
}

let inFlight = 0;
let savedAt: number | null = null;
let snapshot: SaveStatus = { kind: 'idle', canRetry: false };
const fallos = new Map<string, Fallo>();
const listeners = new Set<() => void>();

function recompute(): void {
  if (inFlight > 0) {
    snapshot = { kind: 'saving', canRetry: false };
  } else if (fallos.size > 0) {
    const todos = [...fallos.values()];
    snapshot = { kind: 'error', message: todos[todos.length - 1].message, canRetry: todos.some((f) => f.reintentar) };
  } else if (savedAt !== null) {
    snapshot = { kind: 'saved', savedAt, canRetry: false };
  } else {
    snapshot = { kind: 'idle', canRetry: false };
  }
  for (const listener of listeners) listener();
}

export const saveStatusStore = {
  subscribe(listener: () => void) {
    listeners.add(listener);
    return () => { listeners.delete(listener); };
  },
  getSnapshot: () => snapshot,
  /** Una escritura empezó. */
  begin() {
    inFlight += 1;
    recompute();
  },
  /** Una escritura terminó bien. `clave` identifica qué dato escribió: reemplaza a un fallo anterior de esa clave. */
  succeed(clave?: string, now = Date.now()) {
    inFlight = Math.max(0, inFlight - 1);
    if (clave) fallos.delete(clave);
    savedAt = now;
    recompute();
  },
  /** Una escritura falló. El error queda hasta que esa clave se guarde bien o se reintente. */
  fail(message: string, clave: string, reintentar?: () => void) {
    inFlight = Math.max(0, inFlight - 1);
    fallos.delete(clave); // reinsertar la deja como la más reciente
    fallos.set(clave, { message: message || 'No se pudo guardar', reintentar });
    recompute();
  },
  /** Un fallo que no pasó por una mutación (p. ej. una sección que lanzó al guardar). */
  reportError(message: string, clave: string, reintentar?: () => void) {
    fallos.delete(clave);
    fallos.set(clave, { message: message || 'No se pudo guardar', reintentar });
    recompute();
  },
  /** Un fallo quedó resuelto por otra vía. */
  resolve(clave: string) {
    if (fallos.delete(clave)) recompute();
  },
  hasFailures: () => fallos.size > 0,
  /** Vuelve a intentar todo lo que falló. Cada intento informa de nuevo su resultado. */
  retry() {
    const pendientes = [...fallos.entries()].filter(([, f]) => f.reintentar);
    for (const [clave] of pendientes) fallos.delete(clave);
    recompute();
    for (const [, fallo] of pendientes) fallo.reintentar?.();
  },
  /** Solo para tests. */
  reset() {
    inFlight = 0;
    savedAt = null;
    fallos.clear();
    recompute();
  },
};

export function useSaveStatus(): SaveStatus {
  return useSyncExternalStore(saveStatusStore.subscribe, saveStatusStore.getSnapshot, saveStatusStore.getSnapshot);
}

/** "hace 4 s", "hace 2 min": relativo al instante `now`. */
export function formatHace(savedAt: number, now: number): string {
  const seconds = Math.max(0, Math.round((now - savedAt) / 1000));
  if (seconds < 60) return `hace ${seconds} s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `hace ${minutes} min`;
  return `hace ${Math.floor(minutes / 60)} h`;
}
