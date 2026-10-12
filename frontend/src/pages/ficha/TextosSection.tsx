import { forwardRef, useEffect, useImperativeHandle, useState } from 'react';
import { Card, DosButton, DosTextarea } from '@/components/dos';
import { FIELDDEFS } from '@/lib/domain/types';
import type { Game, TextKey } from '@/lib/domain/types';
import { Campo } from './CampoTexto';
import type { SaveHandle } from './types';
import styles from './TextosSection.module.css';

const PLACEHOLDER_SINOPSIS = 'Ej.: Versión norteamericana del arcade de 1986. Controlás la nave Vaus y rebotás una bola para destruir los bloques de cada pantalla.';

/** Textos del juego: hoy solo la sinopsis. Lo que explica cómo se juega vive en `GuiaSection`. */
export const TextSection = forwardRef<SaveHandle, {
  game: Game;
  onDelete: (key: string) => void;
  onSuggest: (key: TextKey) => void;
  onText: (key: TextKey, value: string) => void;
}>(function TextSection({ game, onDelete, onSuggest, onText }, ref) {
  const [sinopsis, setSinopsis] = useState(game.texts.sinopsis.value);
  useEffect(() => setSinopsis(game.texts.sinopsis.value), [game.texts.sinopsis.value]);

  // Escribe solo si algo cambió: una sinopsis sugerida que nadie tocó no pasa a «manual» por guardar.
  useImperativeHandle(ref, () => ({
    save: () => {
      if (sinopsis !== game.texts.sinopsis.value) onText('sinopsis', sinopsis);
    },
  }), [onText, sinopsis, game]);

  const sinopsisDef = FIELDDEFS.texts.find((field) => field.key === 'sinopsis');
  const sinopsisBloquea = !!sinopsisDef?.required;
  const sinRevisar = game.texts.sinopsis.status === 'suggested' ? 1 : 0;

  return (
    <Card band="var(--accent)" hint={sinRevisar > 0 ? `${sinRevisar} sin revisar` : undefined} number={6} title="Textos">
      <div className={styles.campos}>
        <Campo
          acciones={<DosButton aria-label="Sugerir sinopsis desde ArcadeDB" onClick={() => onSuggest('sinopsis')} size="sm" title="Sugerir desde ArcadeDB" variant="ghost">↻</DosButton>}
          bloqueo={sinopsisBloquea ? 'Bloquea la exportación' : undefined}
          campo="sinopsis"
          contador={{ actual: sinopsis.length, maximo: sinopsisDef?.maxLength }}
          etiqueta="Sinopsis"
          game={game}
          onDelete={onDelete}
        >
          <DosTextarea
            aria-label="Sinopsis"
            data-campo="sinopsis"
            invalid={sinopsisBloquea && game.texts.sinopsis.status === 'empty'}
            maxLength={sinopsisDef?.maxLength}
            onChange={(event) => setSinopsis(event.target.value)}
            placeholder={PLACEHOLDER_SINOPSIS}
            rows={4}
            value={sinopsis}
          />
        </Campo>
      </div>
    </Card>
  );
});
