/*
 * FichaPage · andamiaje de la ficha de juego (feature 019, DESIGN_SPEC §5.1).
 *
 * Orden vertical: crumbs → Hero → banner de precarga → avisos → StepNav sticky →
 * [col-main: secciones | col-side sticky: Siguiente pendiente + paneles laterales] → ActionBar.
 *
 * ── CONTRATO PARA LAS SECCIONES ───────────────────────────────────────────────────────────
 * Una sección es un componente que FichaJuego monta como `node` de un `FichaSeccion`. Esta
 * página la envuelve; la sección NO dibuja ancla, StepNav ni botones de guardado.
 *
 * 1. Ancla. El wrapper es `<section id="seccion-<clave>" data-seccion="<clave>">`. `<clave>` es
 *    una de `FICHA_SECCIONES` (hooks/useFichaProgress): identidad, imagenes, textos, guia,
 *    trucos, presentacion, resena, manual. Para sumar un paso (p. ej. `video`, `galeria`) se agrega
 *    a `FICHA_SECCIONES` y se parte el nodo en FichaJuego; el StepNav y el progreso lo toman solos.
 *    `scroll-margin-top` ya compensa el StepNav sticky.
 *
 * 2. Props. La sección recibe `game` (siempre el último dato del servidor... salvo mientras hay un
 *    campo con foco o una escritura en vuelo: ahí recibe el último valor previo, ver
 *    `useCongeladoMientrasEdita`) y callbacks que FichaJuego cablea a `useGameMutations`. No llama
 *    a `fetch` ni a mutaciones por su cuenta. Mantené el estado local sincronizado SOLO cuando
 *    cambia el valor de servidor (`useEffect(..., [game.x.value])`), nunca en cada render.
 *
 * 3. Guardado sin botones. Si la sección tiene estado local, expone `save()` con
 *    `forwardRef` + `useImperativeHandle(ref, () => ({ save }))` (tipo `SaveHandle`) y FichaJuego la
 *    registra con `ref={registrar('<clave>')}`. El autosave llama a `save()` ~800 ms después de
 *    la última edición y al perder el foco. `save()` tiene que ser idempotente y escribir SOLO lo que
 *    cambió respecto de `game` (no marcar `manual` un campo sugerido que nadie tocó). Un campo cuyo
 *    valor a medias es inválido (ruta, hex) puede llevar `data-autosave="blur"` y se guarda recién
 *    al salir. Los botones "Guardar X" / "Guardar todo" ya no existen: no los dibujes.
 *
 * 4. Cambios sucios. Cualquier `input`/`change` nativo dentro del wrapper marca la sección como
 *    sucia por delegación: no hay que hacer nada. Para cambios sin evento nativo (arrastrar para
 *    reordenar, quitar un ítem de un ListEditor, elegir una tarjeta) llamá a
 *    `const { markDirty } = useFichaAutosave(); markDirty('<clave>')`.
 *
 * 5. Anclas de campo. Poné `data-campo="<clave del campo>"` (la de fielddefs.json: `title`,
 *    `caratula`, `sinopsis`, `objetivo`, `accent`, `cheats`, `review`…) en el control o en su
 *    contenedor. Las píldoras "Para exportar falta:", "Siguiente pendiente" (`N`) y `Enter` lo usan
 *    para hacer scroll y resaltar. Si falta, se busca por `aria-label` igual al rótulo del campo.
 *
 * 6. Sugerencias. Un campo `suggested` se acepta con `useFichaAutosave().aceptar('<clave>')` (pages/ficha/autosaveContext)
 *    (POST /games/{id}/fields/{clave}/accept: conserva valor y `source`, status pasa a `manual`).
 *    `Enter` sobre el campo con foco hace lo mismo (en un textarea, `Ctrl+Enter`: Enter escribe).
 *
 * Atajos globales de la ficha: `N` siguiente pendiente (no actúa al escribir), `Esc` suelta el foco
 * de un campo, `Enter` acepta la sugerencia del campo con foco.
 */
import { useCallback, useEffect, useMemo, useState, type KeyboardEvent, type ReactNode, type RefObject } from 'react';
import { Link } from 'react-router-dom';
import { anclaSeccion, type FichaProgress, type PendienteFicha } from '@/hooks/useFichaProgress';
import type { Autosave } from '@/hooks/useAutosave';
import type { computeGameStatus } from '@/lib/domain/completeness';
import type { Game, System } from '@/lib/domain/types';
import { FichaAutosaveContext, type FichaAutosaveApi } from './autosaveContext';
import { FichaHero } from './FichaHero';
import { FichaActionBar, FichaNextPending, FichaStepNav } from './FichaWrappers';
import { irAPendiente, irASeccion, sugerenciaEnFoco } from './navegacion';
import type { AccentSlot } from './types';
import styles from './ficha.module.css';

export interface FichaSeccion {
  clave: string;
  node: ReactNode;
  /** Guardar al salir del campo y no mientras se teclea (`data-autosave="blur"` en el wrapper). */
  soloAlSalir?: boolean;
}

export interface FichaPageProps {
  game: Game;
  systems: System[];
  status: ReturnType<typeof computeGameStatus>;
  progress: FichaProgress;
  autosave: Autosave;
  /** Contenedor de col-main + col-side: es donde el autosave escucha las ediciones. */
  containerRef: RefObject<HTMLDivElement>;
  /** Banner de precarga (progreso del job o resumen). Va entre el Hero y el StepNav. */
  banner?: ReactNode;
  /** Paneles de error / aviso previos al contenido. */
  avisos?: ReactNode;
  secciones: FichaSeccion[];
  /** Paneles de la columna lateral, debajo de "Siguiente pendiente". */
  lateral?: FichaSeccion[];
  proximoAcento: AccentSlot;
  onSystemChange: (systemId: string) => void;
  onMarkReady: () => void;
  onPickColor: (hex: string) => void;
  /** Acepta la sugerencia de un campo por su clave de API (`accent`, `caratula`, `sinopsis`, `review`…). */
  onAcceptKey: (clave: string) => void;
  onSaveDraft: () => void;
  onExport: () => void;
}

function esControlDeTexto(el: HTMLElement): boolean {
  return el.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName);
}

export function FichaPage({
  game, systems, status, progress, autosave, containerRef, banner, avisos, secciones, lateral = [], proximoAcento,
  onSystemChange, onMarkReady, onPickColor, onAcceptKey, onSaveDraft, onExport,
}: FichaPageProps) {
  const [activa, setActiva] = useState<string | undefined>(progress.secciones[0]?.clave);
  const sistema = systems.find((s) => s.id === game.systemId);

  // Sección visible → paso activo del StepNav.
  useEffect(() => {
    if (typeof IntersectionObserver === 'undefined') return undefined;
    const visibles = new Set<string>();
    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        const clave = entry.target.getAttribute('data-seccion');
        if (!clave) continue;
        if (entry.isIntersecting) visibles.add(clave);
        else visibles.delete(clave);
      }
      const primera = progress.secciones.find((s) => visibles.has(s.clave));
      if (primera) setActiva(primera.clave);
    }, { rootMargin: '-25% 0px -60% 0px' });
    for (const s of progress.secciones) {
      const el = document.getElementById(anclaSeccion(s.clave));
      if (el) observer.observe(el);
    }
    return () => observer.disconnect();
  }, [progress.secciones]);

  const irAPendienteCon = useCallback((pendiente: PendienteFicha, enfocar: boolean) => {
    if (containerRef.current) irAPendiente(containerRef.current, pendiente, enfocar);
    setActiva(pendiente.seccion);
  }, [containerRef]);

  const alTeclear = (event: KeyboardEvent<HTMLDivElement>) => {
    const target = event.target;
    if (!(target instanceof HTMLElement) || target.closest('[role="dialog"]')) return;
    if (event.key === 'Escape' && esControlDeTexto(target)) {
      target.blur();
      return;
    }
    if (event.key !== 'Enter' || event.shiftKey || event.altKey || event.nativeEvent.isComposing) return;
    if (['BUTTON', 'A', 'SELECT'].includes(target.tagName)) return;
    // En un textarea Enter escribe un salto de línea: ahí se acepta con Ctrl/Cmd + Enter.
    if (target.tagName === 'TEXTAREA' && !(event.ctrlKey || event.metaKey)) return;
    const sugerencia = containerRef.current ? sugerenciaEnFoco(containerRef.current, target, progress.sugerencias) : null;
    if (!sugerencia?.aceptarClave) return;
    event.preventDefault();
    onAcceptKey(sugerencia.aceptarClave);
    // Soltar el foco deja que la ficha se refresque con el campo ya aceptado.
    target.blur();
  };

  const api = useMemo<FichaAutosaveApi>(() => ({ markDirty: autosave.markDirty, aceptar: onAcceptKey }), [autosave.markDirty, onAcceptKey]);

  const envolver = (s: FichaSeccion) => (
    <section
      className={styles.seccion}
      data-autosave={s.soloAlSalir ? 'blur' : undefined}
      data-seccion={s.clave}
      id={anclaSeccion(s.clave)}
      key={s.clave}
    >
      {s.node}
    </section>
  );

  return (
    <FichaAutosaveContext.Provider value={api}>
      <div className={styles.ficha}>
        <nav aria-label="Ruta" className={styles.crumbs}>
          <Link to="/juegos">Juegos</Link>
          <span aria-hidden="true">/</span>
          <span>{sistema?.name ?? game.systemId}</span>
        </nav>

        <FichaHero
          game={game}
          onGoPendiente={(p) => irAPendienteCon(p, true)}
          onMarkReady={onMarkReady}
          onPickColor={onPickColor}
          onSystemChange={onSystemChange}
          progress={progress}
          proximoAcento={proximoAcento}
          status={status}
          systems={systems}
        />

        {banner}
        {avisos}

        <FichaStepNav
          activeId={activa}
          onSelect={(clave) => {
            setActiva(clave);
            irASeccion(clave);
          }}
          progress={progress}
        />

        <div className={styles.cols} onKeyDown={alTeclear} ref={containerRef}>
          <div className={styles.main}>{secciones.map(envolver)}</div>
          <aside aria-label="Pendientes y archivo" className={styles.side}>
            <FichaNextPending onGo={(p) => irAPendienteCon(p, false)} progress={progress} />
            {lateral.map(envolver)}
          </aside>
        </div>

        <FichaActionBar
          erroresDeFormato={game.errors.length}
          onExport={onExport}
          onSaveDraft={onSaveDraft}
          progress={progress}
        />
      </div>
    </FichaAutosaveContext.Provider>
  );
}
