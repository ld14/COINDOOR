import { forwardRef, useEffect, useImperativeHandle, useState, type ReactNode } from 'react';
import { Card, DosButton, DosTextarea, ListEditor, OriginChip, itemsALineas, lineasAItems } from '@/components/dos';
import { FIELDDEFS } from '@/lib/domain/types';
import type { Game, TextKey } from '@/lib/domain/types';
import { useFichaAutosave } from './autosaveContext';
import { confirmManualDelete } from './helpers';
import type { SaveHandle } from './types';
import styles from './TextosSection.module.css';

// Textos del bloque `guia` («Cómo se juega») que se editan acá. Las listas viajan con un ítem por línea.
const GUIA_KEYS: TextKey[] = ['objetivo', 'primerosPasos', 'reglasEsenciales'];
const LISTAS: TextKey[] = ['primerosPasos', 'reglasEsenciales'];

const PLACEHOLDER_OBJETIVO = 'En una frase: qué tiene que lograr el jugador. Ej.: «Eliminá a los criminales de cada escenario sin dispararle a los civiles.»';
const PLACEHOLDER_SINOPSIS = 'Ej.: Versión norteamericana del arcade de 1986. Controlás la nave Vaus y rebotás una bola para destruir los bloques de cada pantalla.';

function maxDe(key: TextKey): number | undefined {
  return FIELDDEFS.texts.find((field) => field.key === key)?.maxLength;
}

interface CampoProps {
  campo: TextKey;
  etiqueta: string;
  game: Game;
  /** Obligatorio que bloquea algo: vacío se pinta en error con este motivo. */
  bloqueo?: string;
  acciones?: ReactNode;
  ayuda?: string;
  contador?: { actual: number; maximo?: number };
  children: ReactNode;
  onDelete: (key: string) => void;
}

function Campo({ campo, etiqueta, game, bloqueo, acciones, ayuda, contador, children, onDelete }: CampoProps) {
  const { aceptar } = useFichaAutosave();
  const field = game.texts[campo];
  const status = field?.status ?? 'empty';
  const bloquea = status === 'empty' && !!bloqueo;
  return (
    <div className={[styles.campo, status === 'suggested' ? styles.sugerido : ''].filter(Boolean).join(' ')} data-bloquea={bloquea || undefined} data-estado={status} data-grupo={campo}>
      <div className={styles.cabecera}>
        <span className={styles.rotulo}>{etiqueta}</span>
        <OriginChip required={bloquea} source={field?.source} status={status} />
        {contador ? (
          <span className={[styles.contador, contador.maximo && contador.actual >= contador.maximo ? styles.contadorLleno : ''].filter(Boolean).join(' ')}>
            {contador.actual}{contador.maximo ? ` / ${contador.maximo}` : ''}
          </span>
        ) : null}
        <div className={styles.acciones}>
          {acciones}
          {status !== 'empty' ? (
            <DosButton onClick={() => confirmManualDelete(status, () => onDelete(campo))} size="sm" title="Borrar" variant="ghost">Borrar</DosButton>
          ) : null}
        </div>
      </div>
      {children}
      {bloquea ? <p className={styles.error}>✕ {bloqueo}</p> : null}
      {ayuda ? <p className={styles.ayuda}>{ayuda}</p> : null}
      {status === 'suggested' ? (
        <div className={styles.pie}>
          <DosButton aria-label={`Aceptar ${etiqueta.toLowerCase()}`} onClick={() => aceptar(campo)} size="sm" variant="primary">✓ Aceptar</DosButton>
          <span className={styles.atajo}>Aceptar como está, o editalo y queda como Manual.</span>
        </div>
      ) : null}
    </div>
  );
}

export const TextSection = forwardRef<SaveHandle, {
  game: Game;
  onDelete: (key: string) => void;
  onSuggest: (key: TextKey) => void;
  onText: (key: TextKey, value: string) => void;
}>(function TextSection({ game, onDelete, onSuggest, onText }, ref) {
  const { markDirty } = useFichaAutosave();
  const guardado = (key: TextKey) => game.texts[key]?.value ?? '';
  const [sinopsis, setSinopsis] = useState(game.texts.sinopsis.value);
  useEffect(() => setSinopsis(game.texts.sinopsis.value), [game.texts.sinopsis.value]);
  const leer = () => Object.fromEntries(GUIA_KEYS.map((key) => [key, LISTAS.includes(key) ? lineasAItems(guardado(key)) : guardado(key)]));
  // Las listas se guardan como arreglo (sin recortar): ListEditor reinicia sus filas si el arreglo que recibe difiere del que emitió.
  const [guia, setGuia] = useState<Record<string, string | string[]>>(leer);
  const firma = JSON.stringify(GUIA_KEYS.map(guardado));
  useEffect(() => setGuia(leer()), [firma]); // eslint-disable-line react-hooks/exhaustive-deps
  const comoTexto = (key: TextKey): string => {
    const valor = guia[key];
    return Array.isArray(valor) ? itemsALineas(valor.map((item) => item.trim()).filter(Boolean)) : valor;
  };
  const serializadoGuardado = (key: TextKey) => (LISTAS.includes(key) ? itemsALineas(lineasAItems(guardado(key))) : guardado(key));

  // Escribe SOLO lo que cambió: un texto sugerido que nadie tocó no pasa a «manual» por guardar otro.
  // Los textos de la guía son opcionales: vaciar uno no lo guarda (para eso está «Borrar»).
  useImperativeHandle(ref, () => ({
    save: () => {
      if (sinopsis !== game.texts.sinopsis.value) onText('sinopsis', sinopsis);
      for (const key of GUIA_KEYS) {
        const texto = comoTexto(key);
        if (texto.trim() && texto !== serializadoGuardado(key)) onText(key, texto);
      }
    },
  }), [onText, sinopsis, guia, game]); // eslint-disable-line react-hooks/exhaustive-deps

  const sinopsisDef = FIELDDEFS.texts.find((field) => field.key === 'sinopsis');
  const sinopsisBloquea = !!sinopsisDef?.required;
  const objetivoVacio = (game.texts.objetivo?.status ?? 'empty') === 'empty';
  const objetivoPide = objetivoVacio && (game.guiaChecklist?.some((item) => item.key === 'objetivo' && item.requerido && item.estado === 'falta') ?? false);
  const cambiarLista = (key: TextKey, items: string[]) => {
    setGuia((prev) => ({ ...prev, [key]: items }));
    markDirty('textos');
  };
  const proponer = (key: TextKey, texto: string, aria: string) => (
    <DosButton aria-label={aria} onClick={() => onSuggest(key)} size="sm" variant="secondary">{texto}</DosButton>
  );

  const sinRevisar = (['sinopsis', ...GUIA_KEYS] as TextKey[]).filter((key) => game.texts[key]?.status === 'suggested').length;

  return (
    <Card band="var(--accent)" hint={sinRevisar > 0 ? `${sinRevisar} sin revisar` : undefined} number={4} title="Textos">
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

        <Campo
          acciones={proponer('objetivo', '✦ Proponer un objetivo', 'Proponer un objetivo')}
          bloqueo={objetivoPide ? 'Sin objetivo la guía de «Cómo se juega» no se exporta' : undefined}
          campo="objetivo"
          contador={{ actual: String(guia.objetivo).length, maximo: maxDe('objetivo') }}
          etiqueta="Objetivo"
          game={game}
          onDelete={onDelete}
        >
          <DosTextarea
            aria-label="Objetivo"
            data-campo="objetivo"
            invalid={objetivoPide}
            maxLength={maxDe('objetivo')}
            onChange={(event) => setGuia((prev) => ({ ...prev, objetivo: event.target.value }))}
            placeholder={PLACEHOLDER_OBJETIVO}
            rows={3}
            value={String(guia.objetivo)}
          />
        </Campo>

        <Campo
          acciones={proponer('primerosPasos', '✦ Proponer 3 pasos', 'Proponer 3 pasos')}
          ayuda="Un paso por fila. Enter agrega otro; arrastrá ⋮⋮ para reordenar."
          campo="primerosPasos"
          etiqueta="Primeros pasos"
          game={game}
          onDelete={onDelete}
        >
          <div data-campo="primerosPasos">
            <ListEditor
              addLabel="+ Agregar paso"
              ariaLabel="Primeros pasos"
              itemLabel="Paso"
              items={guia.primerosPasos as string[]}
              onChange={(items) => cambiarLista('primerosPasos', items)}
              placeholder="Ej.: Rebotá la bola con la nave para destruir los bloques."
            />
          </div>
        </Campo>

        <Campo
          acciones={proponer('reglasEsenciales', '✦ Proponer reglas', 'Proponer reglas esenciales')}
          ayuda="Una regla por fila."
          campo="reglasEsenciales"
          etiqueta="Reglas esenciales"
          game={game}
          onDelete={onDelete}
        >
          <div data-campo="reglasEsenciales">
            <ListEditor
              addLabel="+ Agregar regla"
              ariaLabel="Reglas esenciales"
              itemLabel="Regla"
              items={guia.reglasEsenciales as string[]}
              onChange={(items) => cambiarLista('reglasEsenciales', items)}
              placeholder="Ej.: Si la bola cae al fondo, perdés una vida."
            />
          </div>
        </Campo>
      </div>
    </Card>
  );
});
