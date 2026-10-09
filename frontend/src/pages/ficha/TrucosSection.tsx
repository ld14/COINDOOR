import { forwardRef, useEffect, useImperativeHandle, useLayoutEffect, useRef, useState, type DragEvent, type KeyboardEvent } from 'react';
import { Card, DosButton, DosInput, DosTextarea, InlineSuggestion, OriginChip, Spinner } from '@/components/dos';
import { FICHA_SECCIONES } from '@/hooks/useFichaProgress';
import type { CheatGroup, Game } from '@/lib/domain/types';
import { parseCheatsText } from '@/lib/api/fields';
import { useFichaAutosave } from './autosaveContext';
import { confirmManualDelete } from './helpers';
import { AvisoSugerido, EtiquetaIA } from './origenIA';
import type { SaveHandle } from './types';
import styles from './TrucosSection.module.css';

/** Símbolos de arcade que cuesta teclear: se insertan donde está el cursor, sin sacar el foco del campo. */
const SIMBOLOS = ['←', '↑', '→', '↓', '↖', '↗', '↘', '↙', '[ATAQUE]', '[SALTO]', '[ESPECIAL]', '+'];
/** Un grupo con más entradas que estas muestra solo las primeras y un «Ver N más». */
const ENTRADAS_VISIBLES = 4;
/** Una entrada más larga que esto se muestra en una sola línea hasta que se la abre. */
const LARGO_COLAPSADO = 100;

interface Fila { id: number; name: string; input: string }
interface Grupo { id: number; name: string; entries: Fila[] }

let secuencia = 0;
const nuevoId = () => { secuencia += 1; return secuencia; };

const conIds = (groups: CheatGroup[]): Grupo[] => groups.map((g) => ({
  id: nuevoId(),
  name: g.name,
  entries: g.entries.map((e) => ({ id: nuevoId(), name: e.name, input: e.input })),
}));

/** Lo que se guarda: sin entradas totalmente en blanco (un «+ Agregar truco» que nadie llenó). */
const aDominio = (grupos: Grupo[]): CheatGroup[] => grupos.map((g) => ({
  name: g.name,
  entries: g.entries.filter((e) => e.name.trim() || e.input.trim()).map((e) => ({ name: e.name, input: e.input })),
}));

const firma = (groups: CheatGroup[]) => JSON.stringify(groups.map((g) => ({
  name: g.name,
  entries: g.entries.map((e) => ({ name: e.name, input: e.input })),
})));

const esLarga = (fila: Fila) => fila.name.length + fila.input.length > LARGO_COLAPSADO || fila.input.includes('\n');
const plural = (n: number, uno: string, varios: string) => `${n} ${n === 1 ? uno : varios}`;

export const CheatsSection = forwardRef<SaveHandle, {
  game: Game;
  onCheats: (groups: CheatGroup[]) => void;
  onDelete: () => void;
  onSuggest: () => void;
  /** Número del círculo del encabezado. Por defecto el del paso en el StepNav. */
  numero?: number;
}>(function CheatsSection({ game, onCheats, onDelete, onSuggest, numero }, ref) {
  const { markDirty, aceptar } = useFichaAutosave();
  const [grupos, setGrupos] = useState<Grupo[]>(() => conIds(game.cheats.groups));
  const [abiertas, setAbiertas] = useState<Set<number>>(new Set());
  const [expandidos, setExpandidos] = useState<Set<number>>(new Set());
  const [enfocada, setEnfocada] = useState<number | null>(null);
  const [arrastre, setArrastre] = useState<{ grupo: number; fila: number } | null>(null);
  const [sobre, setSobre] = useState<number | null>(null);
  const campos = useRef(new Map<number, HTMLTextAreaElement>());
  const manijas = useRef(new Map<number, HTMLButtonElement>());
  const cursor = useRef<{ fila: number; pos: number } | null>(null);
  const foco = useRef<number | null>(null);

  // Lo que llega del servidor reemplaza lo local solo si es distinto de lo que ya se guardaría:
  // así el guardado propio no borra la fila en blanco que el usuario acaba de agregar.
  const servidor = firma(game.cheats.groups);
  useEffect(() => {
    setGrupos((previo) => (firma(aDominio(previo)) === servidor ? previo : conIds(game.cheats.groups)));
  }, [servidor]); // eslint-disable-line react-hooks/exhaustive-deps

  useImperativeHandle(ref, () => ({
    save: () => {
      const groups = aDominio(grupos);
      if (firma(groups) !== servidor) onCheats(groups);
    },
  }), [onCheats, grupos, servidor]);

  useLayoutEffect(() => {
    if (cursor.current) {
      const { fila, pos } = cursor.current;
      cursor.current = null;
      const el = campos.current.get(fila);
      if (el?.isConnected) {
        el.focus();
        el.setSelectionRange(pos, pos);
      }
    }
    if (foco.current !== null) {
      manijas.current.get(foco.current)?.focus();
      foco.current = null;
    }
  });

  const cambiar = (fn: (previo: Grupo[]) => Grupo[]) => {
    setGrupos(fn);
    markDirty('trucos');
  };
  const mapGrupo = (gid: number, fn: (g: Grupo) => Grupo) => cambiar((prev) => prev.map((g) => (g.id === gid ? fn(g) : g)));
  const mapFila = (gid: number, fid: number, parche: Partial<Fila>) => mapGrupo(gid, (g) => ({
    ...g,
    entries: g.entries.map((e) => (e.id === fid ? { ...e, ...parche } : e)),
  }));
  const marcar = (set: Set<number>, id: number) => new Set(set).add(id);

  const agregarGrupo = () => cambiar((prev) => [...prev, { id: nuevoId(), name: 'Nuevo grupo', entries: [] }]);
  const quitarGrupo = (gid: number) => cambiar((prev) => prev.filter((g) => g.id !== gid));
  const agregarFila = (gid: number) => {
    const fila: Fila = { id: nuevoId(), name: '', input: '' };
    setAbiertas((prev) => marcar(prev, fila.id));
    setExpandidos((prev) => marcar(prev, gid));
    mapGrupo(gid, (g) => ({ ...g, entries: [...g.entries, fila] }));
  };
  const quitarFila = (gid: number, fid: number) => mapGrupo(gid, (g) => ({ ...g, entries: g.entries.filter((e) => e.id !== fid) }));

  const mover = (gid: number, desde: number, hasta: number, conFoco?: number) => {
    if (desde === hasta) return;
    if (conFoco !== undefined) foco.current = conFoco;
    mapGrupo(gid, (g) => {
      if (hasta < 0 || hasta >= g.entries.length) return g;
      const entries = [...g.entries];
      const [fila] = entries.splice(desde, 1);
      entries.splice(hasta, 0, fila);
      return { ...g, entries };
    });
  };
  const alTeclearManija = (event: KeyboardEvent<HTMLButtonElement>, gid: number, indice: number, fid: number) => {
    if (event.key === 'ArrowUp') { event.preventDefault(); mover(gid, indice, indice - 1, fid); }
    if (event.key === 'ArrowDown') { event.preventDefault(); mover(gid, indice, indice + 1, fid); }
  };
  const alSoltar = (event: DragEvent, grupo: Grupo, destino: number) => {
    event.preventDefault();
    const origen = arrastre;
    setArrastre(null);
    setSobre(null);
    if (!origen || origen.grupo !== grupo.id) return;
    const desde = grupo.entries.findIndex((e) => e.id === origen.fila);
    const hasta = grupo.entries.findIndex((e) => e.id === destino);
    if (desde >= 0 && hasta >= 0) mover(grupo.id, desde, hasta, origen.fila);
  };

  const insertar = (gid: number, fila: Fila, simbolo: string) => {
    const el = campos.current.get(fila.id);
    const inicio = el?.selectionStart ?? fila.input.length;
    const fin = el?.selectionEnd ?? inicio;
    cursor.current = { fila: fila.id, pos: inicio + simbolo.length };
    mapFila(gid, fila.id, { input: fila.input.slice(0, inicio) + simbolo + fila.input.slice(fin) });
  };

  // Pegar una guía y separarla en trucos: el resultado queda como propuesta (sugerido) hasta que se la use.
  const claveBorrador = `coindoor:cheats-draft:${game.id}`;
  const [pegado, setPegado] = useState(() => {
    try {
      return localStorage.getItem(claveBorrador) ?? '';
    } catch {
      return '';
    }
  });
  const [separando, setSeparando] = useState(false);
  const [errorSeparar, setErrorSeparar] = useState<string | null>(null);
  const [propuesta, setPropuesta] = useState<CheatGroup[]>([]);

  useEffect(() => {
    try {
      if (pegado) localStorage.setItem(claveBorrador, pegado);
      else localStorage.removeItem(claveBorrador);
    } catch {
      // localStorage no disponible (privado, cuota, etc.): el borrador solo vive en memoria.
    }
  }, [claveBorrador, pegado]);

  const separar = async () => {
    if (!pegado.trim()) return;
    setSeparando(true);
    setErrorSeparar(null);
    try {
      const resultado = await parseCheatsText(game.id, pegado);
      if (resultado.groups.length === 0) setErrorSeparar('No se encontró ningún truco identificable en ese texto.');
      else setPropuesta(resultado.groups);
    } catch (err) {
      setErrorSeparar(err instanceof Error ? err.message : 'No se pudo interpretar el texto.');
    } finally {
      setSeparando(false);
    }
  };
  const usarPropuesta = () => {
    cambiar((prev) => [...prev, ...conIds(propuesta)]);
    setPropuesta([]);
    setPegado('');
  };
  const totalPropuesta = propuesta.reduce((n, g) => n + g.entries.length, 0);

  const total = grupos.reduce((n, g) => n + g.entries.length, 0);
  const pasoNumero = numero ?? FICHA_SECCIONES.findIndex((s) => s.clave === 'trucos') + 1;
  const { status, source } = game.cheats;

  return (
    <Card
      actions={(
        <>
          <DosButton aria-label="Agregar grupo" onClick={agregarGrupo} size="sm" variant="secondary">+ Grupo</DosButton>
          <DosButton aria-label="Sugerir trucos" onClick={onSuggest} size="sm" title="Sugerir desde ArcadeDB" variant="secondary">↻</DosButton>
        </>
      )}
      band="var(--accent-2)"
      bandInk="var(--ink-on-accent-2)"
      data-campo="cheats"
      hint={total > 0 ? `${plural(grupos.length, 'grupo', 'grupos')} · ${plural(total, 'truco', 'trucos')}` : 'opcional'}
      number={pasoNumero}
      title="Trucos"
    >
      <div className={styles.cuerpo}>
        <div className={styles.origen}>
          <OriginChip source={source} status={status} />
          <EtiquetaIA source={source} />
          <DosButton
            className={styles.borrar}
            onClick={() => confirmManualDelete(status, onDelete)}
            size="sm"
            variant="ghost"
          >
            Borrar
          </DosButton>
        </div>

        {status === 'suggested' ? <AvisoSugerido nombre="los trucos" onAceptar={() => aceptar('cheats')} source={source} /> : null}

        <div className={styles.pegar}>
          <label className={styles.rotulo} htmlFor={`trucos-pegar-${game.id}`}>Pegá una guía o texto suelto</label>
          <DosTextarea
            aria-label="Texto de trucos a interpretar"
            id={`trucos-pegar-${game.id}`}
            onChange={(event) => setPegado(event.target.value)}
            placeholder="Pegá acá una lista de trucos, una guía o un texto copiado de una revista…"
            rows={2}
            value={pegado}
          />
          <div className={styles.fila}>
            <DosButton disabled={separando || !pegado.trim()} disabledReason={!pegado.trim() ? 'Pegá primero el texto de los trucos.' : undefined} onClick={() => void separar()} size="sm" variant="secondary">
              {separando ? 'Separando…' : '✦ Separar en trucos'}
            </DosButton>
            {separando ? <Spinner /> : <span className={styles.ayuda}>la propuesta se revisa antes de entrar</span>}
          </div>
          {errorSeparar ? <p className={styles.error}>{errorSeparar}</p> : null}
          {propuesta.length > 0 ? (
            <InlineSuggestion
              onIgnore={() => setPropuesta([])}
              onUse={usarPropuesta}
              source="IA"
              value={`${plural(totalPropuesta, 'truco', 'trucos')} en ${plural(propuesta.length, 'grupo', 'grupos')}`}
            />
          ) : null}
        </div>

        {grupos.length === 0 ? (
          <p className={styles.vacio}>Todavía no hay trucos. Pegá una guía arriba o agregá un grupo.</p>
        ) : null}

        {grupos.map((grupo, gi) => {
          const sobran = grupo.entries.length - ENTRADAS_VISIBLES;
          const verTodo = expandidos.has(grupo.id) || sobran <= 0;
          const visibles = verTodo ? grupo.entries : grupo.entries.slice(0, ENTRADAS_VISIBLES);
          return (
            <div className={styles.grupo} key={grupo.id}>
              <div className={styles.grupoHead}>
                <DosInput
                  aria-label={gi === 0 ? 'Nombre del grupo' : `Nombre del grupo ${gi + 1}`}
                  className={styles.grupoNombre}
                  onChange={(event) => mapGrupo(grupo.id, (g) => ({ ...g, name: event.target.value }))}
                  value={grupo.name}
                />
                <span className={styles.ayuda}>{plural(grupo.entries.length, 'truco', 'trucos')}</span>
                <DosButton className={styles.eliminar} onClick={() => quitarGrupo(grupo.id)} size="sm" variant="ghost">Eliminar grupo</DosButton>
              </div>
              <ul className={styles.lista}>
                {visibles.map((fila) => {
                  const indice = grupo.entries.findIndex((e) => e.id === fila.id);
                  const colapsada = esLarga(fila) && !abiertas.has(fila.id) && enfocada !== fila.id;
                  const clases = [
                    styles.truco,
                    colapsada ? styles.colapsado : '',
                    arrastre?.fila === fila.id ? styles.arrastrando : '',
                    sobre === fila.id && arrastre?.fila !== fila.id ? styles.sobre : '',
                  ].filter(Boolean).join(' ');
                  return (
                    <li
                      className={clases}
                      key={fila.id}
                      onDragLeave={() => setSobre((actual) => (actual === fila.id ? null : actual))}
                      onDragOver={(event) => {
                        if (!arrastre || arrastre.grupo !== grupo.id) return;
                        event.preventDefault();
                        setSobre(fila.id);
                      }}
                      onDrop={(event) => alSoltar(event, grupo, fila.id)}
                    >
                      <button
                        aria-label={`Mover truco ${indice + 1} del grupo ${grupo.name || gi + 1}`}
                        className={styles.manija}
                        draggable
                        onDragEnd={() => { setArrastre(null); setSobre(null); }}
                        onDragStart={(event) => {
                          setArrastre({ grupo: grupo.id, fila: fila.id });
                          event.dataTransfer.effectAllowed = 'move';
                          event.dataTransfer.setData('text/plain', String(fila.id));
                        }}
                        onKeyDown={(event) => alTeclearManija(event, grupo.id, indice, fila.id)}
                        ref={(node) => { if (node) manijas.current.set(fila.id, node); else manijas.current.delete(fila.id); }}
                        title="Arrastrá para reordenar (o usá ↑ ↓ con el foco acá)"
                        type="button"
                      >
                        ⋮⋮
                      </button>
                      {colapsada ? (
                        <div className={styles.resumen}>
                          <strong className={styles.resumenNombre}>{fila.name || 'Sin descripción'}</strong>
                          <span className={styles.resumenTexto}>{fila.input.replace(/\s+/g, ' ')}</span>
                        </div>
                      ) : (
                        <div className={styles.campos}>
                          <DosInput
                            aria-label="Qué hace el truco"
                            onChange={(event) => mapFila(grupo.id, fila.id, { name: event.target.value })}
                            onFocus={() => setAbiertas((prev) => marcar(prev, fila.id))}
                            placeholder="Qué hace"
                            value={fila.name}
                          />
                          <DosTextarea
                            aria-label="Código o procedimiento"
                            className={styles.codigo}
                            onBlur={() => setEnfocada((actual) => (actual === fila.id ? null : actual))}
                            onChange={(event) => mapFila(grupo.id, fila.id, { input: event.target.value })}
                            onFocus={(event) => {
                              campos.current.set(fila.id, event.currentTarget);
                              setEnfocada(fila.id);
                              setAbiertas((prev) => marcar(prev, fila.id));
                            }}
                            placeholder="Código / procedimiento"
                            rows={2}
                            value={fila.input}
                          />
                          {enfocada === fila.id ? (
                            <div aria-label="Símbolos" className={styles.simbolos} role="group">
                              {SIMBOLOS.map((simbolo) => (
                                <button
                                  className={styles.simbolo}
                                  key={simbolo}
                                  onClick={() => insertar(grupo.id, fila, simbolo)}
                                  onMouseDown={(event) => event.preventDefault()}
                                  tabIndex={-1}
                                  type="button"
                                >
                                  {simbolo}
                                </button>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      )}
                      {colapsada ? (
                        <button aria-label="Editar truco" className={styles.icono} onClick={() => setAbiertas((prev) => marcar(prev, fila.id))} type="button">✎</button>
                      ) : null}
                      <button aria-label="Eliminar truco" className={`${styles.icono} ${styles.quitar}`} onClick={() => quitarFila(grupo.id, fila.id)} title="Eliminar truco" type="button">✕</button>
                    </li>
                  );
                })}
              </ul>
              <div className={styles.pie}>
                <DosButton onClick={() => agregarFila(grupo.id)} size="sm" variant="ghost">+ Agregar truco</DosButton>
                {sobran > 0 ? (
                  <DosButton
                    onClick={() => setExpandidos((prev) => {
                      const siguiente = new Set(prev);
                      if (siguiente.has(grupo.id)) siguiente.delete(grupo.id); else siguiente.add(grupo.id);
                      return siguiente;
                    })}
                    size="sm"
                    variant="ghost"
                  >
                    {verTodo ? 'Ver menos' : `Ver ${sobran} más`}
                  </DosButton>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
});
