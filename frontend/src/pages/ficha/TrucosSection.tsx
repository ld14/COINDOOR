import { forwardRef, useEffect, useImperativeHandle, useState } from 'react';
import { DosButton, DosInput, DosTextarea, FieldTag, Panel, SectionHeader, Spinner, SunkenBox } from '@/components/dos';
import type { CheatGroup, Game } from '@/lib/domain/types';
import { parseCheatsText } from '@/lib/api/fields';
import { confirmManualDelete } from './helpers';
import type { SaveHandle } from './types';
import styles from '../ReadPages.module.css';

export const CheatsSection = forwardRef<SaveHandle, {
  game: Game;
  onCheats: (groups: CheatGroup[]) => void;
  onDelete: () => void;
  onSuggest: () => void;
}>(function CheatsSection({ game, onCheats, onDelete, onSuggest }, ref) {
  const [groups, setGroups] = useState<CheatGroup[]>(game.cheats.groups);
  const [editando, setEditando] = useState(false);
  // Mientras se edita, lo que llega del servidor no pisa lo que el usuario escribió.
  useEffect(() => {
    if (!editando) setGroups(game.cheats.groups);
  }, [editando, game.cheats.groups]);
  useImperativeHandle(ref, () => ({ save: () => onCheats(groups) }), [onCheats, groups]);

  const draftKey = `coindoor:cheats-draft:${game.id}`;
  const [pastedText, setPastedText] = useState(() => {
    try {
      return localStorage.getItem(draftKey) ?? '';
    } catch {
      return '';
    }
  });
  const [interpreting, setInterpreting] = useState(false);
  const [interpretError, setInterpretError] = useState<string | null>(null);

  useEffect(() => {
    try {
      if (pastedText) {
        localStorage.setItem(draftKey, pastedText);
      } else {
        localStorage.removeItem(draftKey);
      }
    } catch {
      // localStorage no disponible (privado, cuota, etc.): el borrador solo vive en memoria.
    }
  }, [draftKey, pastedText]);

  const handleInterpret = async () => {
    if (!pastedText.trim()) return;
    setInterpreting(true);
    setInterpretError(null);
    try {
      const result = await parseCheatsText(game.id, pastedText);
      if (result.groups.length === 0) {
        setInterpretError('No se encontró ningún truco identificable en ese texto.');
      } else {
        setGroups((prev) => [...prev, ...result.groups]);
      }
    } catch (err) {
      setInterpretError(err instanceof Error ? err.message : 'No se pudo interpretar el texto.');
    } finally {
      setInterpreting(false);
    }
  };

  const updateGroupName = (groupIdx: number, name: string) => {
    setGroups((prev) => prev.map((g, i) => (i === groupIdx ? { ...g, name } : g)));
  };
  const removeGroup = (groupIdx: number) => {
    setGroups((prev) => prev.filter((_, i) => i !== groupIdx));
  };
  const addGroup = () => {
    setGroups((prev) => [...prev, { name: 'Nuevo grupo', entries: [] }]);
  };
  const updateEntry = (groupIdx: number, entryIdx: number, field: keyof CheatGroup['entries'][number], value: string) => {
    setGroups((prev) => prev.map((g, i) => (
      i === groupIdx
        ? { ...g, entries: g.entries.map((e, j) => (j === entryIdx ? { ...e, [field]: value } : e)) }
        : g
    )));
  };
  const removeEntry = (groupIdx: number, entryIdx: number) => {
    setGroups((prev) => prev.map((g, i) => (
      i === groupIdx ? { ...g, entries: g.entries.filter((_, j) => j !== entryIdx) } : g
    )));
  };
  const addEntry = (groupIdx: number) => {
    setGroups((prev) => prev.map((g, i) => (
      i === groupIdx ? { ...g, entries: [...g.entries, { name: '', input: '' }] } : g
    )));
  };

  return (
    <Panel>
      <SectionHeader>TRUCOS</SectionHeader>
      <SunkenBox className={styles.stack}>
        <div className={styles.fieldTop}><span className={styles.name}>Códigos cargados</span><FieldTag status={game.cheats.status} /></div>
        {!editando && groups.length > 0 ? (
          <div className={styles.cheatLedger}>
            {groups.map((group, groupIdx) => (
              <div className={styles.cheatGroup} key={groupIdx}>
                <span className={styles.cheatGroupName}>{group.name}</span>
                {group.entries.map((entry, entryIdx) => (
                  <div className={styles.cheatEntry} key={entryIdx}>
                    <span>{entry.name}</span>
                    <code>{entry.input}</code>
                  </div>
                ))}
              </div>
            ))}
          </div>
        ) : null}
        {editando && groups.length > 0 ? (
          <div className={styles.cheatLedger}>
            {groups.map((group, groupIdx) => (
              <div className={styles.cheatGroup} key={groupIdx}>
                <div className={styles.cheatGroupEdit}>
                  <DosInput aria-label="Nombre del grupo" onChange={(event) => updateGroupName(groupIdx, event.target.value)} value={group.name} />
                  <DosButton onClick={() => removeGroup(groupIdx)} variant="danger-small">Eliminar grupo</DosButton>
                </div>
                {group.entries.map((entry, entryIdx) => (
                  <div className={styles.cheatEntryEdit} key={entryIdx}>
                    <DosInput aria-label="Qué hace el truco" onChange={(event) => updateEntry(groupIdx, entryIdx, 'name', event.target.value)} placeholder="Qué hace" value={entry.name} />
                    <DosInput aria-label="Código o procedimiento" onChange={(event) => updateEntry(groupIdx, entryIdx, 'input', event.target.value)} placeholder="Código / procedimiento" value={entry.input} />
                    <DosButton onClick={() => removeEntry(groupIdx, entryIdx)} variant="danger-small">Eliminar</DosButton>
                  </div>
                ))}
                <div className={styles.toolbar}>
                  <DosButton onClick={() => addEntry(groupIdx)} variant="ghost-small">+ Agregar truco</DosButton>
                </div>
              </div>
            ))}
          </div>
        ) : null}
        {groups.length === 0 ? <p className={styles.empty}>No Disponible</p> : null}
        {editando ? (
          <div className={styles.toolbar}>
            <DosButton onClick={addGroup} variant="ghost-small">+ Agregar grupo</DosButton>
            <DosButton onClick={() => { onCheats(groups); setEditando(false); }} variant="primary-small">Guardar trucos</DosButton>
            <DosButton onClick={() => { setGroups(game.cheats.groups); setEditando(false); }} variant="ghost-small">Cancelar</DosButton>
          </div>
        ) : (
          <div className={styles.toolbar}>
            <DosButton onClick={() => setEditando(true)} variant="primary-small">Editar trucos</DosButton>
            <DosButton onClick={onSuggest} variant="ghost-small">Sugerir</DosButton>
            <DosButton onClick={() => confirmManualDelete(game.cheats.status, onDelete)} variant="danger-small">Borrar</DosButton>
          </div>
        )}
        {editando ? (
          <div className={styles.field}>
            <span className={styles.label}>Pegar texto (Markdown, lista o prosa)</span>
            <DosTextarea
              aria-label="Texto de trucos a interpretar"
              onChange={(event) => setPastedText(event.target.value)}
              placeholder="Pegá acá una guía, lista o texto suelto con trucos…"
              value={pastedText}
            />
            <div className={styles.toolbar}>
              <DosButton disabled={interpreting || !pastedText.trim()} onClick={() => void handleInterpret()} variant="ghost-small">
                {interpreting ? 'Interpretando…' : 'Interpretar con IA'}
              </DosButton>
              {interpreting ? <Spinner /> : null}
            </div>
            {interpretError ? <p className={styles.error}>{interpretError}</p> : null}
          </div>
        ) : null}
      </SunkenBox>
    </Panel>
  );
});
