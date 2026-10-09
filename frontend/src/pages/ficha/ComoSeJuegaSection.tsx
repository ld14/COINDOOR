import { Card, DosButton, OriginChip, SegmentedControl, type SegmentedOption } from '@/components/dos';
import type { Game, GuiaChecklistItem, TextKey } from '@/lib/domain/types';
import { useFichaAutosave } from './autosaveContext';
import { confirmManualDelete } from './helpers';
import { irAPendiente } from './navegacion';
import styles from './ComoSeJuegaSection.module.css';

/** Filas del checklist que se resuelven escribiendo en un campo de «Textos». */
const CAMPOS_DE_TEXTO = new Set(['objetivo', 'primerosPasos', 'reglasEsenciales']);

const MODOS: { value: string; label: string }[] = [
  { value: 'individual', label: 'Individual' },
  { value: 'cooperativo', label: 'Cooperativo' },
  { value: 'versus', label: 'Versus' },
];

interface GuiaChecklistProps {
  items: GuiaChecklistItem[];
  fallos: Record<string, string>;
  /**
   * Para resolver «Modo multijugador» en la misma fila hace falta la ficha y cómo escribirla.
   * Sin estos props la fila muestra el estado y el selector queda deshabilitado.
   */
  game?: Game;
  onText?: (key: TextKey, value: string) => void;
  onDelete?: (key: string) => void;
  onSuggest?: (key: TextKey) => void;
}

function irACampo(campo: string, etiquetas: string[]) {
  irAPendiente(document, { id: `ir:${campo}`, label: campo, severity: 'required', seccion: 'textos', campo, etiquetas }, true);
}

type FilaModoProps = Pick<GuiaChecklistProps, 'onText' | 'onDelete' | 'onSuggest'> & { game: Game; item: GuiaChecklistItem };

function FilaModo({ item, game, onText, onDelete, onSuggest }: FilaModoProps) {
  const { aceptar } = useFichaAutosave();
  const campo = game.texts.modo;
  const status = campo?.status ?? 'empty';
  const valor = (campo?.value ?? '').toLowerCase();
  // En un juego simultáneo ArcadeDB no permite deducir «individual»: se elige cooperativo o versus.
  const simultaneo = /sim/i.test(game.cabinet?.nplayers ?? '');
  const opciones: SegmentedOption[] = MODOS.map((modo) => ({ ...modo, disabled: simultaneo && modo.value === 'individual' }));
  return (
    <div className={styles.modoControl} data-campo="modo">
      {status !== 'empty' ? <OriginChip source={campo?.source} status={status} /> : null}
      <SegmentedControl
        ariaLabel="Modo multijugador"
        disabled={!onText}
        onChange={(modo) => { if (modo !== valor) onText?.('modo', modo); }}
        options={opciones}
        value={valor}
      />
      {status === 'suggested' ? <DosButton aria-label="Aceptar modo multijugador" onClick={() => aceptar('modo')} size="sm" variant="primary">✓ Aceptar</DosButton> : null}
      {onSuggest && item.estado === 'falta' ? (
        <DosButton aria-label="Proponer modo multijugador" onClick={() => onSuggest('modo')} size="sm" variant="secondary">✦ Proponer</DosButton>
      ) : null}
      {onDelete && status !== 'empty' ? (
        <DosButton aria-label="Borrar modo multijugador" onClick={() => confirmManualDelete(status, () => onDelete('modo'))} size="sm" variant="ghost">Borrar</DosButton>
      ) : null}
    </div>
  );
}

export function GuiaChecklist({ items, fallos, game, onText, onDelete, onSuggest }: GuiaChecklistProps) {
  if (items.length === 0) return null;
  const listos = items.filter((item) => item.estado === 'ok').length;
  const sinObjetivo = items.some((item) => item.requerido && item.estado === 'falta');
  return (
    <Card band="var(--accent-2)" hint={`${listos} de ${items.length} listos`} number={5} title="Cómo se juega">
      {sinObjetivo ? <p className={`${styles.resumen} ${styles.resumenError}`}>✕ Sin objetivo la guía no se exporta.</p> : null}
      <ul aria-label="Checklist de la guía" className={styles.lista}>
        {items.map((item) => {
          const falla = item.estado === 'falta' ? fallos[item.key] : undefined;
          const ok = item.estado === 'ok';
          const marca = ok ? '✓' : item.requerido ? '✕' : '!';
          const clase = ok ? styles.marcaOk : item.requerido ? styles.marcaError : styles.marcaRevisar;
          const nombreMarca = ok ? 'Listo' : item.requerido ? 'Falta (obligatorio)' : 'Revisar';
          const detalle = falla ? `No se pudo generar: ${falla}. ${item.detalle}` : item.detalle;
          return (
            <li className={styles.fila} data-estado={item.estado} data-requerido={item.requerido} key={item.key}>
              <span aria-label={nombreMarca} className={`${styles.marca} ${clase}`} role="img">{marca}</span>
              <span className={styles.nombre}>
                <span className={styles.etiqueta}>{item.label}</span>
                <span className={`${styles.detalle} ${falla ? styles.detalleError : ''}`}>{detalle}</span>
              </span>
              <span className={styles.accion}>
                {item.key === 'modo' && game ? (
                  <FilaModo game={game} item={item} onDelete={onDelete} onSuggest={onSuggest} onText={onText} />
                ) : null}
                {!ok && CAMPOS_DE_TEXTO.has(item.key) ? (
                  <DosButton aria-label={`Escribir ${item.label.toLowerCase()}`} onClick={() => irACampo(item.key, [item.label])} size="sm" variant="secondary">Escribir ↑</DosButton>
                ) : null}
                {!ok && item.key === 'jugadores' ? (
                  <DosButton aria-label="Ir a Jugadores en Identidad" onClick={() => irACampo('players', ['Jugadores'])} size="sm" variant="secondary">Ir a Identidad ↑</DosButton>
                ) : null}
              </span>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
