import { useCallback, useEffect, useLayoutEffect, useRef, useState, type MutableRefObject, type RefObject } from 'react';
import { saveStatusStore } from './useSaveStatus';

/** Espera tras la última tecla antes de guardar (DESIGN_SPEC §4). */
export const AUTOSAVE_DELAY_MS = 800;

/** Marca de una sección en el DOM: `data-seccion="<clave>"`. La pone FichaPage, no cada sección. */
export const ATRIBUTO_SECCION = 'data-seccion';
/**
 * `data-autosave="blur"` en un campo (o en un contenedor suyo): se guarda al salir del campo y no
 * mientras se teclea. Para valores que un guardado a medias vuelve inválidos (rutas, hex).
 */
export const ATRIBUTO_SOLO_AL_SALIR = 'data-autosave';

export interface AutosaveOptions {
  /** Contenedor cuyos eventos de edición se escuchan (por delegación, `input`/`change`/`focusout`). */
  containerRef: RefObject<HTMLElement | null>;
  /** Guarda las secciones indicadas (dispara sus mutaciones). Puede ser asíncrono. */
  save: (secciones: string[]) => void | Promise<void>;
  /** Resuelve cuando no queda ninguna escritura en vuelo. Si falta, `flushAndWait` solo espera a `save`. */
  waitIdle?: () => Promise<void>;
  /** Hay escrituras en vuelo ahora mismo (para `beforeunload`). */
  isSaving?: () => boolean;
  delay?: number;
}

export interface Autosave {
  /** Avisa a mano que una sección tiene cambios (las secciones que no emiten eventos nativos). */
  markDirty: (seccion: string, opciones?: { soloAlSalir?: boolean }) => void;
  /** Guarda ya las secciones sucias, sin esperar el debounce. */
  flush: () => void;
  /** `flush` y espera a que terminen todas las escrituras. Úsalo antes de navegar. */
  flushAndWait: () => Promise<void>;
  /** Reintenta lo último que se intentó guardar (más lo que haya quedado sucio). */
  retry: () => void;
  hasUnsaved: () => boolean;
  /** Estado para la UI: hay cambios que todavía no se mandaron. */
  dirty: boolean;
}

/** Los `change` de inputs de texto son ruido: ya los cubre `input`, y dispararían un segundo guardado al salir del campo. */
function esCambioRelevante(target: HTMLElement): boolean {
  if (target instanceof HTMLSelectElement) return true;
  if (target instanceof HTMLInputElement) return !TIPOS_DE_TEXTO.includes(target.type);
  return false;
}

/** Clave del fallo de `save` en el store de guardado (los de mutaciones llevan la clave de su campo). */
const CLAVE_FALLO = 'autosave';

const TIPOS_DE_TEXTO = ['text', 'search', 'url', 'email', 'tel', 'password', 'number'];

/** Donde se teclea: ahí una recarga de datos pisaría lo escrito. Selects, casillas y archivos son elecciones discretas. */
function esEntradaDeTexto(el: HTMLElement): boolean {
  if (el.isContentEditable || el instanceof HTMLTextAreaElement) return true;
  return el instanceof HTMLInputElement && TIPOS_DE_TEXTO.includes(el.type);
}

function seccionDe(target: EventTarget | null): string | null {
  if (!(target instanceof HTMLElement)) return null;
  return target.closest(`[${ATRIBUTO_SECCION}]`)?.getAttribute(ATRIBUTO_SECCION) ?? null;
}

/**
 * Autosave por delegación de eventos: cualquier edición dentro del contenedor marca su sección
 * como sucia y, pasado `delay` sin más cambios o al perder el foco, llama a `save` con las
 * secciones sucias. Las secciones no saben nada de esto: siguen exponiendo `save()`.
 *
 * Un fallo de `save` deja las secciones sucias, publica el error en `saveStatusStore` (la TopBar
 * muestra "Reintentar") y `retry()` lo vuelve a intentar.
 */
export function useAutosave({ containerRef, save, waitIdle, isSaving, delay = AUTOSAVE_DELAY_MS }: AutosaveOptions): Autosave {
  const sucias = useRef(new Set<string>());
  const ultimas = useRef<string[]>([]);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [dirty, setDirty] = useState(false);
  // El hook siempre ve la última versión de las funciones sin reinstalar listeners.
  const config = useRef({ save, waitIdle, isSaving, delay });
  useLayoutEffect(() => { config.current = { save, waitIdle, isSaving, delay }; });

  const cancelarTimer = () => {
    if (timer.current !== null) {
      clearTimeout(timer.current);
      timer.current = null;
    }
  };

  const retryRef = useRef<() => void>(() => undefined);

  const guardar = useCallback((ids: string[], reintento = false): Promise<void> => {
    const fallo = (error: unknown) => {
      for (const id of ids) sucias.current.add(id);
      setDirty(true);
      saveStatusStore.reportError(error instanceof Error ? error.message : 'No se pudo guardar', CLAVE_FALLO, () => retryRef.current());
    };
    try {
      const resultado = config.current.save(ids);
      return Promise.resolve(resultado).then(() => { if (reintento) saveStatusStore.resolve(CLAVE_FALLO); }, fallo);
    } catch (error) {
      fallo(error);
      return Promise.resolve();
    }
  }, []);

  const flushInterno = useCallback((reintento = false): Promise<void> => {
    cancelarTimer();
    if (sucias.current.size === 0) return Promise.resolve();
    const ids = [...sucias.current];
    sucias.current.clear();
    ultimas.current = ids;
    setDirty(false);
    return guardar(ids, reintento);
  }, [guardar]);

  const flush = useCallback(() => { void flushInterno(); }, [flushInterno]);

  const markDirty = useCallback((seccion: string, opciones?: { soloAlSalir?: boolean }) => {
    sucias.current.add(seccion);
    setDirty(true);
    if (opciones?.soloAlSalir) return; // lo guarda el focusout (o el timer de otra edición)
    cancelarTimer();
    timer.current = setTimeout(() => {
      timer.current = null;
      void flushInterno();
    }, config.current.delay);
  }, [flushInterno]);

  const retry = useCallback(() => {
    for (const id of ultimas.current) sucias.current.add(id);
    void flushInterno(true);
  }, [flushInterno]);
  useEffect(() => { retryRef.current = retry; }, [retry]);

  const flushAndWait = useCallback(async () => {
    await flushInterno();
    await config.current.waitIdle?.();
  }, [flushInterno]);

  const hasUnsaved = useCallback(() => sucias.current.size > 0 || saveStatusStore.hasFailures() || (config.current.isSaving?.() ?? false), []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return undefined;
    const alEditar = (event: Event) => {
      const id = seccionDe(event.target);
      if (!id) return;
      const soloAlSalir = event.target instanceof HTMLElement && event.target.closest(`[${ATRIBUTO_SOLO_AL_SALIR}="blur"]`) !== null;
      markDirty(id, { soloAlSalir });
    };
    const alCambiar = (event: Event) => {
      if (event.target instanceof HTMLElement && esCambioRelevante(event.target)) alEditar(event);
    };
    const alPerderFoco = () => { flush(); };
    el.addEventListener('input', alEditar);
    el.addEventListener('change', alCambiar);
    el.addEventListener('focusout', alPerderFoco);
    return () => {
      el.removeEventListener('input', alEditar);
      el.removeEventListener('change', alCambiar);
      el.removeEventListener('focusout', alPerderFoco);
    };
  }, [containerRef, markDirty, flush]);

  useEffect(() => {
    const alCerrar = (event: BeforeUnloadEvent) => {
      if (!hasUnsaved()) return;
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', alCerrar);
    return () => window.removeEventListener('beforeunload', alCerrar);
  }, [hasUnsaved]);

  // Al desmontar (cambio de ruta sin pasar por un blur) se guarda lo pendiente y se reintenta lo que
  // había fallado: si no, salir de la ficha descartaría la edición en silencio. El layout cleanup
  // corre antes de que los hijos suelten sus refs, así que `save()` todavía existe.
  useLayoutEffect(() => () => {
    flush();
    saveStatusStore.retry();
  }, [flush]);

  return { markDirty, flush, flushAndWait, retry, hasUnsaved, dirty };
}

/**
 * Devuelve `value` salvo mientras el usuario edita (foco en un campo dentro del contenedor) o
 * hay escrituras en vuelo: en ese lapso conserva el último valor, así una recarga de datos no
 * pisa lo que se está tecleando. Al terminar, devuelve el valor más reciente.
 */
export function useCongeladoMientrasEdita<T>(
  value: T,
  containerRef: RefObject<HTMLElement | null>,
  guardando = false,
): T {
  const [editando, setEditando] = useState(false);
  const congelado: MutableRefObject<T> = useRef(value);
  const sigueCongelado = editando || guardando;
  if (!sigueCongelado) congelado.current = value;

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return undefined;
    const esCampo = (target: EventTarget | null) => target instanceof HTMLElement && esEntradaDeTexto(target);
    const alEnfocar = (event: FocusEvent) => { if (esCampo(event.target)) setEditando(true); };
    // Pasar de un campo a otro no es dejar de editar: se mira adónde va el foco.
    const alSoltar = (event: FocusEvent) => { if (!esCampo(event.relatedTarget) || !el.contains(event.relatedTarget as Node)) setEditando(false); };
    el.addEventListener('focusin', alEnfocar);
    el.addEventListener('focusout', alSoltar);
    return () => {
      el.removeEventListener('focusin', alEnfocar);
      el.removeEventListener('focusout', alSoltar);
    };
  }, [containerRef]);

  return congelado.current;
}
