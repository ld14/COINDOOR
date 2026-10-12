import { forwardRef, useEffect, useImperativeHandle, useState } from 'react';
import { Card, DosButton, DosInput, OriginChip } from '@/components/dos';
import { ChoiceCards, NumberStepper, type ChoiceOption } from '@/components/dos/entrada';
import { soportaArcadeDb } from '@/lib/domain/arcade';
import { FIELDDEFS } from '@/lib/domain/types';
import type { Game, Identity, IdentityKey } from '@/lib/domain/types';
import { useFichaAutosave } from './autosaveContext';
import type { SaveHandle } from './types';
import styles from './IdentidadSection.module.css';

/** Soportes físicos que acepta el contrato (backend/bundle/gamejson.py · FORMATOS_FISICOS). */
const FORMATOS = ['Arcade', 'GD-ROM', 'PCB', 'Cartucho', 'Diskette', 'CD', 'DVD'];

const EJEMPLOS: Record<IdentityKey, string> = {
  title: 'Arkanoid',
  year: '1986',
  developer: 'Taito America',
  publisher: 'Taito',
  genre: 'Paleta / Breakout',
  players: '2',
  format: 'Arcade',
};

const MAX_JUGADORES = 8;
const SUGERIR = 'Sugerir desde ArcadeDB';

function opcionesDeFormato(actual: string, recomendado?: string): ChoiceOption[] {
  const base = FORMATOS.map((value) => ({ value, label: value, recommended: value === recomendado }));
  // Un valor fuera de la lista (ficha vieja) se conserva visible: el contrato lo marcará como error.
  return actual && !FORMATOS.includes(actual) ? [...base, { value: actual, label: actual, recommended: false }] : base;
}

const firma = (identity: Identity) => JSON.stringify(FIELDDEFS.identity.map((f) => identity[f.key]));

export const IdentitySection = forwardRef<SaveHandle, { game: Game; onSave: (identity: Identity) => void; onSuggest: (key: IdentityKey) => void; onSuggestBatch: () => void }>(function IdentitySection({ game, onSave, onSuggest, onSuggestBatch }, ref) {
  const { markDirty } = useFichaAutosave();
  const [identity, setIdentity] = useState(game.identity);
  const guardada = firma(game.identity);
  useEffect(() => setIdentity(game.identity), [guardada]); // eslint-disable-line react-hooks/exhaustive-deps
  // Escribe solo si algo cambió: así un campo de la fuente que nadie tocó no pasa a manual.
  useImperativeHandle(ref, () => ({
    save: () => {
      if (firma(identity) !== guardada) onSave(identity);
    },
  }), [onSave, identity, guardada]);

  const cambiar = (key: IdentityKey, value: string) => {
    setIdentity((prev) => ({ ...prev, [key]: value }));
    markDirty('identidad');
  };

  const recomendado = soportaArcadeDb(game.systemId) ? 'Arcade' : undefined;
  // El stepper solo representa un entero o nada; "1-2" y similares siguen siendo texto.
  const jugadoresNumerico = /^\d*$/.test(game.identity.players);

  const control = (key: IdentityKey, label: string, bloquea: boolean) => {
    if (key === 'format') {
      return (
        <ChoiceCards
          ariaLabel={label}
          compact
          onChange={(value) => cambiar('format', value)}
          options={opcionesDeFormato(identity.format, recomendado)}
          value={identity.format}
        />
      );
    }
    if (key === 'players' && jugadoresNumerico) {
      const n = Number.parseInt(identity.players, 10);
      return (
        <NumberStepper
          ariaLabel={label}
          max={MAX_JUGADORES}
          min={0}
          onChange={(value) => cambiar('players', value === 0 ? '' : String(value))}
          value={Number.isNaN(n) ? 0 : n}
        />
      );
    }
    return (
      <DosInput
        aria-label={label}
        invalid={bloquea}
        onChange={(event) => cambiar(key, event.target.value)}
        placeholder={`Ej.: ${EJEMPLOS[key]}`}
        value={identity[key]}
      />
    );
  };

  return (
    <Card
      actions={<DosButton onClick={onSuggestBatch} size="sm" title={SUGERIR} variant="ghost">↻ Sugerir todo</DosButton>}
      band="var(--accent-3)"
      bandInk="var(--ink-on-accent)"
      hint={`Fuente actual: ${game.identitySource}`}
      number={1}
      title="Identidad"
    >
      <div className={styles.grid}>
        {FIELDDEFS.identity.map((field) => {
          const vacio = game.identity[field.key] === '';
          const bloquea = vacio && field.required;
          return (
            <div
              className={[styles.field, field.key === 'format' ? styles.wide : ''].filter(Boolean).join(' ')}
              key={field.key}
            >
              <div className={styles.head}>
                <span className={styles.label}>{field.label}</span>
                <OriginChip required={bloquea} source={game.identitySource} status={vacio ? 'empty' : 'manual'} />
              </div>
              <div className={styles.row}>
                <div className={styles.control} data-campo={field.key}>{control(field.key, field.label, bloquea)}</div>
                <button
                  aria-label={`Sugerir ${field.label}`}
                  className={styles.suggest}
                  onClick={() => onSuggest(field.key)}
                  title={SUGERIR}
                  type="button"
                >
                  ↻ Sugerir
                </button>
              </div>
              {bloquea ? <span className={styles.blocks}>✕ Bloquea la exportación</span> : null}
            </div>
          );
        })}
      </div>
    </Card>
  );
});
