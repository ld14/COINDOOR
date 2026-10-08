import { forwardRef, useEffect, useImperativeHandle, useState } from 'react';
import { DosButton, DosInput, Panel, SectionHeader, SunkenBox } from '@/components/dos';
import type { Game } from '@/lib/domain/types';
import type { AccentSlot, PresentationHandle } from './types';
import styles from '../ReadPages.module.css';

const hex = (value: string) => `#${value}`;

const ACCENT_PRESETS = [
  { label: 'dorado', value: hex('d4a017'), className: styles.swatchGold },
  { label: 'cian', value: hex('00aaaa'), className: styles.swatchCyan },
  { label: 'rojo', value: hex('aa0000'), className: styles.swatchRed },
  { label: 'verde', value: hex('006600'), className: styles.swatchGreen },
  { label: 'azul', value: hex('0000aa'), className: styles.swatchBlue },
];

export const PresentationSection = forwardRef<PresentationHandle, {
  game: Game;
  onSave: (accentValue: string, accent2Value: string) => void;
}>(function PresentationSection({ game, onSave }, ref) {
  const [accentValue, setAccentValue] = useState(game.accentValue);
  const [accent2Value, setAccent2Value] = useState(game.accent2Value);
  useEffect(() => setAccentValue(game.accentValue), [game.accentValue]);
  useEffect(() => setAccent2Value(game.accent2Value), [game.accent2Value]);
  useImperativeHandle(ref, () => ({
    save: () => onSave(accentValue, accent2Value),
    // Los colores predominantes de la carátula viven en el encabezado, que es
    // otro componente: entran por acá en vez de subir el estado de acento a la
    // página entera.
    setAccent: (slot: AccentSlot, value: string) => {
      if (slot === 0) setAccentValue(value);
      else setAccent2Value(value);
    },
  }), [onSave, accentValue, accent2Value]);
  return (
    <Panel>
      <SectionHeader>PRESENTACIÓN</SectionHeader>
      <SunkenBox className={styles.accentPanel}>
        <AccentRow label="Color de acento primario" status={game.accent} value={accentValue} onChange={setAccentValue} />
        <AccentRow label="Color de acento secundario" status={accent2Value ? game.accent : 'empty'} value={accent2Value} onChange={setAccent2Value} />
        <div className={styles.accentActions}>
          <DosButton onClick={() => onSave(accentValue, accent2Value)} variant="primary-small">Guardar presentación</DosButton>
        </div>
      </SunkenBox>
    </Panel>
  );
});

function AccentRow({ label, onChange, status, value }: { label: string; onChange: (value: string) => void; status: string; value: string }) {
  return (
    <div className={styles.accentRow}>
      <div className={styles.accentTopline}>
        <span className={styles.name}>{label}</span>
        <span className={styles.meta}>{status === 'empty' ? 'sin definir' : status === 'suggested' ? 'sugerido' : 'cargado'}</span>
      </div>
      <div className={styles.swatches}>
        {ACCENT_PRESETS.map((preset) => (
          <button
            aria-label={`${label} ${preset.label}`}
            className={[styles.swatch, preset.className, value.toLowerCase() === preset.value ? styles.swatchActive : ''].filter(Boolean).join(' ')}
            key={preset.label}
            onClick={() => onChange(preset.value)}
            type="button"
          />
        ))}
      </div>
      <label className={styles.hexField}>
        <span className={styles.label}>Agregar color HEX:</span>
        <DosInput aria-label={label} onChange={(event) => onChange(event.target.value)} placeholder="#RRGGBB" value={value} />
      </label>
    </div>
  );
}
