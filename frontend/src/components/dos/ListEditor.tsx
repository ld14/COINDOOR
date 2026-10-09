import type { DragEvent, KeyboardEvent } from 'react';
import { useEffect, useRef, useState } from 'react';
import styles from './ListEditor.module.css';

interface Row {
  id: number;
  text: string;
}

interface ListEditorProps {
  items: string[];
  onChange: (items: string[]) => void;
  ariaLabel: string;
  addLabel?: string;
  itemLabel?: string;
  placeholder?: string;
  disabled?: boolean;
}

const nonBlank = (rows: Row[]) => rows.map((row) => row.text).filter((text) => text.trim().length > 0);
const sameItems = (a: string[], b: string[]) => a.length === b.length && a.every((value, i) => value === b[i]);

export function ListEditor({ items, onChange, ariaLabel, addLabel = '+ Agregar paso', itemLabel = 'Paso', placeholder, disabled = false }: ListEditorProps) {
  const nextId = useRef(0);
  const makeRows = (list: string[]): Row[] => list.map((text) => ({ id: nextId.current++, text }));
  const [rows, setRows] = useState<Row[]>(() => makeRows(items));
  const [dragId, setDragId] = useState<number | null>(null);
  const [overId, setOverId] = useState<number | null>(null);
  const inputRefs = useRef(new Map<number, HTMLInputElement>());
  const handleRefs = useRef(new Map<number, HTMLButtonElement>());
  const pendingFocus = useRef<{ id: number; target: 'input' | 'handle' } | null>(null);

  // Si el padre cambia los ítems por fuera (otro valor que el que emitimos), reiniciamos las filas.
  const itemsKey = JSON.stringify(items);
  useEffect(() => {
    const externos = JSON.parse(itemsKey) as string[];
    setRows((current) => (sameItems(nonBlank(current), externos) ? current : makeRows(externos)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [itemsKey]);

  useEffect(() => {
    const pending = pendingFocus.current;
    if (!pending) return;
    pendingFocus.current = null;
    (pending.target === 'input' ? inputRefs.current.get(pending.id) : handleRefs.current.get(pending.id))?.focus();
  });

  function commit(next: Row[]) {
    setRows(next);
    const emitted = nonBlank(next);
    if (!sameItems(emitted, items)) onChange(emitted);
  }

  function addAfter(index: number) {
    const row: Row = { id: nextId.current++, text: '' };
    const next = [...rows.slice(0, index + 1), row, ...rows.slice(index + 1)];
    pendingFocus.current = { id: row.id, target: 'input' };
    setRows(next);
  }

  function move(from: number, to: number, focus: 'input' | 'handle') {
    if (to < 0 || to >= rows.length || from === to) return;
    const next = [...rows];
    const [row] = next.splice(from, 1);
    next.splice(to, 0, row);
    pendingFocus.current = { id: row.id, target: focus };
    commit(next);
  }

  function remove(index: number) {
    const next = rows.filter((_, i) => i !== index);
    const neighbour = next[index > 0 ? index - 1 : 0];
    if (neighbour) pendingFocus.current = { id: neighbour.id, target: 'input' };
    commit(next);
  }

  function onInputKeyDown(event: KeyboardEvent<HTMLInputElement>, index: number) {
    if (event.key === 'Enter') {
      event.preventDefault();
      addAfter(index);
    } else if (event.key === 'Backspace' && rows[index].text === '') {
      event.preventDefault();
      remove(index);
    } else if (event.altKey && event.key === 'ArrowUp') {
      event.preventDefault();
      move(index, index - 1, 'input');
    } else if (event.altKey && event.key === 'ArrowDown') {
      event.preventDefault();
      move(index, index + 1, 'input');
    }
  }

  function onHandleKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    if (event.key === 'ArrowUp') {
      event.preventDefault();
      move(index, index - 1, 'handle');
    } else if (event.key === 'ArrowDown') {
      event.preventDefault();
      move(index, index + 1, 'handle');
    }
  }

  function onDrop(event: DragEvent, targetId: number) {
    event.preventDefault();
    const from = rows.findIndex((row) => row.id === dragId);
    const to = rows.findIndex((row) => row.id === targetId);
    setDragId(null);
    setOverId(null);
    if (from >= 0 && to >= 0) move(from, to, 'handle');
  }

  return (
    <div className={styles.editor}>
      <ol aria-label={ariaLabel} className={styles.list}>
        {rows.map((row, index) => (
          <li
            className={[styles.row, dragId === row.id ? styles.dragging : '', overId === row.id && dragId !== row.id ? styles.over : ''].filter(Boolean).join(' ')}
            key={row.id}
            onDragLeave={() => setOverId((current) => (current === row.id ? null : current))}
            onDragOver={(event) => {
              if (dragId === null) return;
              event.preventDefault();
              setOverId(row.id);
            }}
            onDrop={(event) => onDrop(event, row.id)}
          >
            <button
              aria-label={`Mover ${itemLabel.toLowerCase()} ${index + 1}`}
              className={styles.handle}
              disabled={disabled}
              draggable={!disabled}
              onDragEnd={() => { setDragId(null); setOverId(null); }}
              onDragStart={(event) => {
                setDragId(row.id);
                event.dataTransfer.effectAllowed = 'move';
                event.dataTransfer.setData('text/plain', String(row.id));
              }}
              onKeyDown={(event) => onHandleKeyDown(event, index)}
              ref={(node) => { if (node) handleRefs.current.set(row.id, node); else handleRefs.current.delete(row.id); }}
              type="button"
            >
              ⋮⋮
            </button>
            <span aria-hidden="true" className={styles.number}>{index + 1}</span>
            <input
              aria-label={`${itemLabel} ${index + 1}`}
              className={styles.input}
              disabled={disabled}
              onChange={(event) => commit(rows.map((r) => (r.id === row.id ? { ...r, text: event.target.value } : r)))}
              onKeyDown={(event) => onInputKeyDown(event, index)}
              placeholder={placeholder}
              ref={(node) => { if (node) inputRefs.current.set(row.id, node); else inputRefs.current.delete(row.id); }}
              type="text"
              value={row.text}
            />
            <button aria-label={`Quitar ${itemLabel.toLowerCase()} ${index + 1}`} className={styles.remove} disabled={disabled} onClick={() => remove(index)} type="button">✕</button>
          </li>
        ))}
      </ol>
      <button className={styles.add} disabled={disabled} onClick={() => addAfter(rows.length - 1)} type="button">{addLabel}</button>
    </div>
  );
}
