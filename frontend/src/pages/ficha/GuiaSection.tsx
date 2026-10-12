import { forwardRef, useEffect, useImperativeHandle, useState } from 'react';
import { Card, DosButton, DosInput, DosTextarea, ListEditor, OriginChip, SegmentedControl, itemsALineas, lineasAItems, type SegmentedOption } from '@/components/dos';
import { FIELDDEFS } from '@/lib/domain/types';
import type { CabinetButton, Game, TextKey } from '@/lib/domain/types';
import { useFichaAutosave } from './autosaveContext';
import { Campo } from './CampoTexto';
import { confirmManualDelete } from './helpers';
import type { SaveHandle } from './types';
import styles from './TextosSection.module.css';

// Textos del bloque `guia` que se editan acá. Las listas viajan con un ítem por línea.
const GUIA_KEYS: TextKey[] = ['objetivo', 'primerosPasos', 'reglasEsenciales'];
const LISTAS: TextKey[] = ['primerosPasos', 'reglasEsenciales'];

const PLACEHOLDER_OBJETIVO = 'En una frase: qué tiene que lograr el jugador. Ej.: «Eliminá a los criminales de cada escenario sin dispararle a los civiles.»';

const MODOS: { value: string; label: string }[] = [
  { value: 'individual', label: 'Individual' },
  { value: 'cooperativo', label: 'Cooperativo' },
  { value: 'versus', label: 'Versus' },
];

function maxDe(key: TextKey): number | undefined {
  return FIELDDEFS.texts.find((field) => field.key === key)?.maxLength;
}

const BOTON_VACIO: CabinetButton = { control: '', color: '', action: '' };

/** Acciones de los botones (`cabinet.button_list`): vienen de ArcadeDB y se pueden cargar o corregir a mano. */
function BotonesEditor({ botones, onChange }: { botones: CabinetButton[]; onChange: (botones: CabinetButton[]) => void }) {
  const cambiar = (indice: number, campo: keyof CabinetButton, valor: string) =>
    onChange(botones.map((boton, i) => (i === indice ? { ...boton, [campo]: valor } : boton)));
  return (
    <div className={styles.botones}>
      {botones.map((boton, i) => (
        <div className={styles.botonFila} key={i}>
          <DosInput aria-label={`Control del botón ${i + 1}`} onChange={(e) => cambiar(i, 'control', e.target.value)} placeholder="Ej.: P1_BUTTON1" value={boton.control} />
          <DosInput aria-label={`Acción del botón ${i + 1}`} onChange={(e) => cambiar(i, 'action', e.target.value)} placeholder="Ej.: Saltar" value={boton.action} />
          <DosInput aria-label={`Color del botón ${i + 1}`} onChange={(e) => cambiar(i, 'color', e.target.value)} placeholder="Color (opcional)" value={boton.color} />
          <DosButton aria-label={`Quitar botón ${i + 1}`} onClick={() => onChange(botones.filter((_, j) => j !== i))} size="sm" variant="ghost">✕</DosButton>
        </div>
      ))}
      <div>
        <DosButton onClick={() => onChange([...botones, { ...BOTON_VACIO }])} size="sm" variant="secondary">+ Agregar botón</DosButton>
      </div>
    </div>
  );
}

interface GuiaSectionProps {
  game: Game;
  onDelete: (key: string) => void;
  onSuggest: (key: TextKey) => void;
  onText: (key: TextKey, value: string) => void;
  onButtons: (botones: CabinetButton[]) => void;
}

/** «Cómo se juega»: los campos que alimentan la guía del export. El estado resumido va en el checklist de la columna lateral. */
export const GuiaSection = forwardRef<SaveHandle, GuiaSectionProps>(function GuiaSection({ game, onDelete, onSuggest, onText, onButtons }, ref) {
  const { markDirty, aceptar } = useFichaAutosave();
  const guardado = (key: TextKey) => game.texts[key]?.value ?? '';
  const leer = () => Object.fromEntries(GUIA_KEYS.map((key) => [key, LISTAS.includes(key) ? lineasAItems(guardado(key)) : guardado(key)]));
  // Las listas se guardan como arreglo (sin recortar): ListEditor reinicia sus filas si el arreglo que recibe difiere del que emitió.
  const [guia, setGuia] = useState<Record<string, string | string[]>>(leer);
  const firma = JSON.stringify(GUIA_KEYS.map(guardado));
  useEffect(() => setGuia(leer()), [firma]); // eslint-disable-line react-hooks/exhaustive-deps
  const guardadosBotones = game.cabinet?.button_list ?? [];
  const [botones, setBotones] = useState<CabinetButton[]>(guardadosBotones);
  const firmaBotones = JSON.stringify(guardadosBotones);
  useEffect(() => setBotones(JSON.parse(firmaBotones) as CabinetButton[]), [firmaBotones]);
  const botonesAGuardar = () => botones.filter((b) => b.control.trim() || b.action.trim() || b.color.trim());
  const comoTexto = (key: TextKey): string => {
    const valor = guia[key];
    return Array.isArray(valor) ? itemsALineas(valor.map((item) => item.trim()).filter(Boolean)) : valor;
  };
  const serializadoGuardado = (key: TextKey) => (LISTAS.includes(key) ? itemsALineas(lineasAItems(guardado(key))) : guardado(key));

  // Escribe SOLO lo que cambió: un texto sugerido que nadie tocó no pasa a «manual» por guardar otro.
  // Los textos de la guía son opcionales: vaciar uno no lo guarda (para eso está «Borrar»).
  useImperativeHandle(ref, () => ({
    save: () => {
      for (const key of GUIA_KEYS) {
        const texto = comoTexto(key);
        if (texto.trim() && texto !== serializadoGuardado(key)) onText(key, texto);
      }
      const nuevos = botonesAGuardar();
      if (JSON.stringify(nuevos) !== firmaBotones) onButtons(nuevos);
    },
  }), [onText, onButtons, guia, botones, firmaBotones, game]); // eslint-disable-line react-hooks/exhaustive-deps

  const objetivoVacio = (game.texts.objetivo?.status ?? 'empty') === 'empty';
  const objetivoPide = objetivoVacio && (game.guiaChecklist?.some((item) => item.key === 'objetivo' && item.requerido && item.estado === 'falta') ?? false);
  const cambiarLista = (key: TextKey, items: string[]) => {
    setGuia((prev) => ({ ...prev, [key]: items }));
    markDirty('guia');
  };
  const proponer = (key: TextKey, texto: string, aria: string) => (
    <DosButton aria-label={aria} onClick={() => onSuggest(key)} size="sm" variant="secondary">{texto}</DosButton>
  );

  const modo = game.texts.modo;
  const modoStatus = modo?.status ?? 'empty';
  const modoValor = (modo?.value ?? '').toLowerCase();
  // En un juego simultáneo ArcadeDB no permite deducir «individual»: se elige cooperativo o versus.
  const simultaneo = /sim/i.test(game.cabinet?.nplayers ?? '');
  const opcionesModo: SegmentedOption[] = MODOS.map((m) => ({ ...m, disabled: simultaneo && m.value === 'individual' }));

  const sinRevisar = [...GUIA_KEYS, 'modo' as TextKey].filter((key) => game.texts[key]?.status === 'suggested').length;

  return (
    <Card band="var(--accent-2)" hint={sinRevisar > 0 ? `${sinRevisar} sin revisar` : undefined} number={8} title="Cómo se juega">
      <div className={styles.campos}>
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

        <div className={styles.campo} data-estado={modoStatus} data-grupo="modo">
          <div className={styles.cabecera}>
            <span className={styles.rotulo}>Modo multijugador</span>
            {modoStatus !== 'empty' ? <OriginChip source={modo?.source} status={modoStatus} /> : null}
            <div className={styles.acciones}>
              {modoStatus === 'empty' ? proponer('modo', '✦ Proponer', 'Proponer modo multijugador') : null}
              {modoStatus === 'suggested' ? <DosButton aria-label="Aceptar modo multijugador" onClick={() => aceptar('modo')} size="sm" variant="primary">✓ Aceptar</DosButton> : null}
              {modoStatus !== 'empty' ? (
                <DosButton aria-label="Borrar modo multijugador" onClick={() => confirmManualDelete(modoStatus, () => onDelete('modo'))} size="sm" variant="ghost">Borrar</DosButton>
              ) : null}
            </div>
          </div>
          <div data-campo="modo">
            <SegmentedControl
              ariaLabel="Modo multijugador"
              onChange={(valor) => { if (valor !== modoValor) onText('modo', valor); }}
              options={opcionesModo}
              value={modoValor}
            />
          </div>
        </div>

        <div className={styles.campo} data-grupo="acciones">
          <div className={styles.cabecera}>
            <span className={styles.rotulo}>Acciones de los botones</span>
          </div>
          <p className={styles.ayuda}>Qué hace cada botón del gabinete. Se completa solo desde ArcadeDB cuando publica el mapa; si no, cargalo acá.</p>
          <div data-campo="acciones">
            <BotonesEditor botones={botones} onChange={(lista) => { setBotones(lista); markDirty('guia'); }} />
          </div>
        </div>
      </div>
    </Card>
  );
});
