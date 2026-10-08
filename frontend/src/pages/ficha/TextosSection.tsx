import { forwardRef, useEffect, useImperativeHandle, useState } from 'react';
import { DosButton, DosSelect, DosTextarea, FieldTag, Panel, SectionHeader, SunkenBox } from '@/components/dos';
import { FIELDDEFS } from '@/lib/domain/types';
import type { Game, TextKey } from '@/lib/domain/types';
import { confirmManualDelete } from './helpers';
import type { SaveHandle } from './types';
import styles from '../ReadPages.module.css';

// Textos opcionales del bloque `guia` («Cómo se juega»). Las listas llevan un ítem por línea.
const GUIA_TEXTOS: { key: TextKey; label: string; aria: string; guardar: string; ayuda?: string }[] = [
  { key: 'objetivo', label: 'Objetivo (Cómo se juega)', aria: 'Objetivo', guardar: 'Guardar objetivo' },
  { key: 'primerosPasos', label: 'Primeros pasos (Cómo se juega)', aria: 'Primeros pasos', guardar: 'Guardar primeros pasos', ayuda: 'Un paso por línea.' },
  { key: 'reglasEsenciales', label: 'Reglas esenciales (Cómo se juega)', aria: 'Reglas esenciales', guardar: 'Guardar reglas esenciales', ayuda: 'Una regla por línea.' },
];
const MODOS_MULTIJUGADOR = ['individual', 'cooperativo', 'versus'] as const;
const GUIA_KEYS: TextKey[] = [...GUIA_TEXTOS.map((texto) => texto.key), 'modo'];

export const TextSection = forwardRef<SaveHandle, {
  game: Game;
  onDelete: (key: string) => void;
  onSuggest: (key: TextKey) => void;
  onText: (key: TextKey, value: string) => void;
}>(function TextSection({ game, onDelete, onSuggest, onText }, ref) {
  const [sinopsis, setSinopsis] = useState(game.texts.sinopsis.value);
  useEffect(() => setSinopsis(game.texts.sinopsis.value), [game.texts.sinopsis.value]);
  const guardado = (key: TextKey) => game.texts[key]?.value ?? '';
  const [guia, setGuia] = useState<Record<string, string>>(() => Object.fromEntries(GUIA_KEYS.map((key) => [key, guardado(key)])));
  const firma = JSON.stringify(GUIA_KEYS.map(guardado));
  useEffect(() => setGuia(Object.fromEntries(GUIA_KEYS.map((key) => [key, guardado(key)]))), [firma]); // eslint-disable-line react-hooks/exhaustive-deps
  // Los textos de la guía son opcionales: guardar todo no debe marcar como escrito a mano uno sin tocar.
  useImperativeHandle(ref, () => ({
    save: () => {
      onText('sinopsis', sinopsis);
      for (const key of GUIA_KEYS) {
        if (guia[key].trim() && guia[key] !== guardado(key)) onText(key, guia[key]);
      }
    },
  }), [onText, sinopsis, guia, firma]); // eslint-disable-line react-hooks/exhaustive-deps
  const estado = (key: TextKey) => game.texts[key]?.status ?? 'empty';
  const cambiar = (key: TextKey, value: string) => setGuia((prev) => ({ ...prev, [key]: value }));

  return (
    <Panel>
      <SectionHeader>TEXTOS</SectionHeader>
      <SunkenBox>
        <div className={styles.fieldTop}><span className={styles.name}>Sinopsis</span><FieldTag status={game.texts.sinopsis.status} /></div>
        <DosTextarea aria-label="Sinopsis" maxLength={FIELDDEFS.texts[0].maxLength} onChange={(event) => setSinopsis(event.target.value)} value={sinopsis} />
        <div className={styles.toolbar}>
          <DosButton onClick={() => onText('sinopsis', sinopsis)} variant="primary-small">Guardar sinopsis</DosButton>
          <DosButton onClick={() => onSuggest('sinopsis')} variant="ghost-small">Sugerir</DosButton>
          <DosButton onClick={() => confirmManualDelete(game.texts.sinopsis.status, () => onDelete('sinopsis'))} variant="danger-small">Borrar</DosButton>
        </div>
      </SunkenBox>
      {GUIA_TEXTOS.map((texto) => (
        <SunkenBox key={texto.key}>
          <div className={styles.fieldTop}><span className={styles.name}>{texto.label}</span><FieldTag status={estado(texto.key)} /></div>
          {texto.ayuda ? <p className={styles.meta}>{texto.ayuda}</p> : null}
          <DosTextarea aria-label={texto.aria} maxLength={FIELDDEFS.texts.find((field) => field.key === texto.key)?.maxLength} onChange={(event) => cambiar(texto.key, event.target.value)} value={guia[texto.key]} />
          <div className={styles.toolbar}>
            <DosButton onClick={() => onText(texto.key, guia[texto.key])} variant="primary-small">{texto.guardar}</DosButton>
            <DosButton onClick={() => onSuggest(texto.key)} variant="ghost-small">Sugerir</DosButton>
            <DosButton onClick={() => confirmManualDelete(estado(texto.key), () => onDelete(texto.key))} variant="danger-small">Borrar</DosButton>
          </div>
        </SunkenBox>
      ))}
      <SunkenBox>
        <div className={styles.fieldTop}><span className={styles.name}>Modo multijugador (Cómo se juega)</span><FieldTag status={estado('modo')} /></div>
        <p className={styles.meta}>Vacío: ATTRACT lo deduce solo en juegos de un jugador o por turnos.</p>
        <DosSelect aria-label="Modo multijugador" onChange={(event) => cambiar('modo', event.target.value)} value={guia.modo}>
          <option value="">Sin elegir</option>
          {MODOS_MULTIJUGADOR.map((modo) => <option key={modo} value={modo}>{modo}</option>)}
        </DosSelect>
        <div className={styles.toolbar}>
          <DosButton onClick={() => onText('modo', guia.modo)} variant="primary-small">Guardar modo</DosButton>
          <DosButton onClick={() => onSuggest('modo')} variant="ghost-small">Sugerir</DosButton>
          <DosButton onClick={() => confirmManualDelete(estado('modo'), () => onDelete('modo'))} variant="danger-small">Borrar</DosButton>
        </div>
      </SunkenBox>
    </Panel>
  );
});
