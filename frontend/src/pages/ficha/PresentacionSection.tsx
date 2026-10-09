import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState } from 'react';
import type { MouseEvent, ReactNode } from 'react';
import { Card, DosInput, OriginChip } from '@/components/dos';
import { InlineSuggestion } from '@/components/dos/InlineSuggestion';
import { useDominantColors } from '@/hooks/useDominantColors';
import type { Game } from '@/lib/domain/types';
import { consumirProximoAcento, reiniciarProximoAcento, useProximoAcento } from './acentoSlot';
import { useFichaAutosave } from './autosaveContext';
import type { AccentSlot, PresentationHandle } from './types';
import styles from './presentacion.module.css';

const hex = (value: string) => `#${value}`;

export const ACCENT_PRESETS = [
  { label: 'dorado', value: hex('d4a017') },
  { label: 'cian', value: hex('00aaaa') },
  { label: 'rojo', value: hex('aa0000') },
  { label: 'verde', value: hex('006600') },
  { label: 'azul', value: hex('0000aa') },
];

/** Colores claros y saturados: se leen bien sobre una carátula casi negra. */
const SUGERIDOS_CONTRASTE = [hex('ffc93c'), hex('00d4ff'), hex('ff5c7a'), hex('7dff8a')];
const UMBRAL_NEGRO = 0.05;
const HEX_COMPLETO = /^#[0-9a-f]{6}$/i;

/** Luminancia relativa (WCAG) de un color [r, g, b] 0-255. */
export function luminancia([r, g, b]: [number, number, number]): number {
  const lin = (canal: number) => {
    const c = canal / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
}

/** Normaliza lo tipeado a `#rrggbb`; `null` si todavía no es un color completo. Acepta sin `#`. */
export function normalizarHex(raw: string): string | null {
  const texto = raw.trim();
  const conGato = texto.startsWith('#') ? texto : `#${texto}`;
  return HEX_COMPLETO.test(conGato) ? conGato.toLowerCase() : null;
}

function errorDeHex(raw: string): string | null {
  const texto = raw.trim();
  if (!texto || normalizarHex(texto)) return null;
  const digitos = texto.replace(/^#/, '');
  if (/^[0-9a-f]*$/i.test(digitos) && digitos.length < 6) return 'Hex incompleto: 6 dígitos';
  return 'Hex inválido: usá 6 dígitos 0-9 y a-f';
}

type Props = {
  game: Game;
  onSave: (accentValue: string, accent2Value: string) => void;
};

export const PresentationSection = forwardRef<PresentationHandle, Props>(function PresentationSection({ game, onSave }, ref) {
  const [accentValue, setAccentValue] = useState(game.accentValue);
  const [accent2Value, setAccent2Value] = useState(game.accent2Value);
  const siguiente = useProximoAcento();
  const [ignorada, setIgnorada] = useState(false);
  const { aceptar, markDirty } = useFichaAutosave();
  useEffect(() => { reiniciarProximoAcento(); }, [game.id]);
  useEffect(() => setAccentValue(game.accentValue), [game.accentValue]);
  useEffect(() => setAccent2Value(game.accent2Value), [game.accent2Value]);

  const caratula = game.images.caratula?.url;
  const { colors } = useDominantColors(caratula, 4);
  const casiNegros = colors.length > 0 && colors.every((color) => luminancia(color.rgb) < UMBRAL_NEGRO);

  const guardado = useRef({ a: game.accentValue, b: game.accent2Value });
  guardado.current = { a: game.accentValue, b: game.accent2Value };

  useImperativeHandle(ref, () => ({
    // Escribe SOLO si cambió algo y es un color completo: un hex a medias conserva el valor guardado.
    save: () => {
      const resolver = (raw: string, previo: string) => (raw.trim() ? normalizarHex(raw) ?? previo : '');
      const a = resolver(accentValue, guardado.current.a);
      const b = resolver(accent2Value, guardado.current.b);
      if (a.toLowerCase() === guardado.current.a.toLowerCase() && b.toLowerCase() === guardado.current.b.toLowerCase()) return;
      onSave(a, b);
    },
    // Los colores predominantes de la carátula viven en el Hero (otro componente): entran por acá.
    // El slot lo decide el contador compartido: el que pasa el orquestador se ignora para no desfasar.
    setAccent: (_slot: AccentSlot, value: string) => {
      if (consumirProximoAcento() === 0) setAccentValue(value);
      else setAccent2Value(value);
      markDirty('presentacion');
    },
  }), [onSave, accentValue, accent2Value, markDirty]);

  const aplicar = useCallback((value: string) => {
    if (consumirProximoAcento() === 0) setAccentValue(value);
    else setAccent2Value(value);
    markDirty('presentacion');
  }, [markDirty]);

  // Toma el color del píxel clicado leyendo la carátula en un canvas (falla en silencio si el navegador no deja).
  const tomarDeCaratula = (event: MouseEvent<HTMLImageElement>) => {
    const img = event.currentTarget;
    try {
      const rect = img.getBoundingClientRect();
      const x = Math.floor(((event.clientX - rect.left) / rect.width) * img.naturalWidth);
      const y = Math.floor(((event.clientY - rect.top) / rect.height) * img.naturalHeight);
      const canvas = document.createElement('canvas');
      canvas.width = 1;
      canvas.height = 1;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      ctx.drawImage(img, x, y, 1, 1, 0, 0, 1, 1);
      const [r, g, b, a] = ctx.getImageData(0, 0, 1, 1).data;
      if (a === 0) return;
      aplicar(`#${[r, g, b].map((c) => c.toString(16).padStart(2, '0')).join('')}`);
    } catch {
      // Imagen de otro origen sin CORS: se elige entre los detectados o se tipea.
    }
  };

  const sugerida = game.accent === 'suggested' && !!game.accentValue && !ignorada;
  const estadoSecundario = accent2Value ? (game.accent === 'suggested' ? 'suggested' : 'manual') : 'empty';

  return (
    <Card band="var(--accent)" hint="Colores del gabinete" number={7} title="Presentación">
      <div className={styles.stack}>
        {sugerida ? (
          <InlineSuggestion
            onIgnore={() => setIgnorada(true)}
            onUse={() => aceptar('accent')}
            source="Precarga"
            value={game.accentValue}
          />
        ) : null}

        {casiNegros ? (
          <div className={styles.aviso} role="status">
            <p>La carátula es casi negra: un acento sacado de ahí no se va a ver sobre fondo oscuro.</p>
            <div className={styles.grupo}>
              <span className={styles.grupoRotulo}>Sugeridos con buen contraste</span>
              <Muestras etiqueta="Sugerido" onPick={aplicar} valores={SUGERIDOS_CONTRASTE} />
            </div>
            <div className={styles.grupo}>
              <span className={styles.grupoRotulo}>Detectados</span>
              <Muestras etiqueta="Detectado" onPick={aplicar} valores={colors.map((color) => color.hex)} />
            </div>
          </div>
        ) : null}

        {caratula ? (
          <div className={styles.caratula}>
            <img
              alt="Carátula: hacé clic para tomar un color"
              className={styles.caratulaImg}
              crossOrigin="anonymous"
              onClick={tomarDeCaratula}
              src={caratula}
            />
            <p className={styles.meta}>{`Un clic en la carátula toma ese color como acento ${siguiente === 0 ? 'primario' : 'secundario'}.`}</p>
          </div>
        ) : null}

        <AccentRow
          campo="accent"
          chip={<OriginChip required source="manual" status={accentValue ? game.accent : 'empty'} />}
          label="Color de acento primario"
          onChange={(v) => { setAccentValue(v); markDirty('presentacion'); }}
          value={accentValue}
        />
        <AccentRow
          campo="accent2"
          chip={<OriginChip source="manual" status={estadoSecundario} />}
          label="Color de acento secundario"
          onChange={(v) => { setAccent2Value(v); markDirty('presentacion'); }}
          opcional
          value={accent2Value}
        />
      </div>
    </Card>
  );
});

function Muestras({ etiqueta, valores, onPick }: { etiqueta: string; valores: string[]; onPick: (value: string) => void }) {
  return (
    <div className={styles.muestras}>
      {valores.map((value) => (
        <button
          aria-label={`${etiqueta} ${value}`}
          className={styles.muestra}
          key={value}
          onClick={() => onPick(value)}
          style={{ backgroundColor: value }}
          title={value}
          type="button"
        />
      ))}
    </div>
  );
}

function AccentRow({ campo, chip, label, onChange, opcional = false, value }: {
  campo: string;
  chip: ReactNode;
  label: string;
  onChange: (value: string) => void;
  opcional?: boolean;
  value: string;
}) {
  const error = errorDeHex(value);
  const valido = normalizarHex(value);
  return (
    <div className={styles.fila} data-campo={campo}>
      <div className={styles.cabecera}>
        <span className={styles.rotulo}>
          {label}
          {opcional ? <span className={styles.opcional}> (opcional)</span> : null}
        </span>
        {chip}
      </div>
      <div className={styles.muestras}>
        {ACCENT_PRESETS.map((preset) => (
          <button
            aria-label={`${label} ${preset.label}`}
            className={[styles.muestra, valido === preset.value ? styles.muestraActiva : ''].filter(Boolean).join(' ')}
            key={preset.label}
            onClick={() => onChange(preset.value)}
            style={{ backgroundColor: preset.value }}
            title={preset.label}
            type="button"
          />
        ))}
      </div>
      <div className={styles.hexLinea}>
        <span
          aria-hidden="true"
          className={[styles.vista, valido ? '' : styles.vistaVacia].filter(Boolean).join(' ')}
          style={valido ? { backgroundColor: valido } : undefined}
        />
        <DosInput
          aria-invalid={error ? true : undefined}
          aria-label={label}
          data-autosave="blur"
          onChange={(event) => onChange(event.target.value)}
          placeholder={hex('RRGGBB')}
          value={value}
        />
      </div>
      {error ? <p className={styles.errorHex} role="alert">{error}</p> : null}
    </div>
  );
}
