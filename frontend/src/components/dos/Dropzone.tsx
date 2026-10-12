import type { ClipboardEvent, DragEvent, KeyboardEvent } from 'react';
import { useRef, useState } from 'react';
import { aceptaArchivo } from './aceptaArchivo';
import styles from './Dropzone.module.css';

interface DropzoneProps {
  /** Mismo formato que el atributo `accept` de un input file (ej. "image/*,.png"). */
  accept?: string;
  /** Un archivo por vez (comportamiento original). */
  onFile?: (file: File) => void;
  /** Con `multiple`, recibe todos los archivos válidos juntos (si no se define, se llama `onFile` con cada uno). */
  onFiles?: (files: File[]) => void;
  multiple?: boolean;
  /** Si está definido (0-100), se muestra el estado de progreso en lugar del cuerpo. */
  progress?: number;
  onCancel?: () => void;
  label?: string;
  secondaryAction?: { label: string; onClick: () => void };
  disabled?: boolean;
  /** Versión baja, para slots angostos: menos relleno y texto chico. */
  compact?: boolean;
}

export function Dropzone({ accept, onFile, onFiles, multiple = false, progress, onCancel, label = 'Soltá una imagen acá o pegala con Ctrl+V', secondaryAction, disabled = false, compact = false }: DropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  const [rejected, setRejected] = useState(false);
  const busy = progress !== undefined;
  const inactive = disabled || busy;

  function deliver(candidates: Array<File | null | undefined> | ArrayLike<File> | null | undefined) {
    const lista = Array.from((candidates ?? []) as ArrayLike<File | null | undefined>).filter((file): file is File => !!file);
    if (lista.length === 0) return;
    const candidatos = multiple ? lista : lista.slice(0, 1);
    const validos = candidatos.filter((file) => aceptaArchivo(file, accept));
    setRejected(validos.length < candidatos.length);
    if (validos.length === 0) return;
    if (multiple && onFiles) onFiles(validos);
    else validos.forEach((file) => onFile?.(file));
  }

  function onDrop(event: DragEvent) {
    event.preventDefault();
    setOver(false);
    if (inactive) return;
    deliver(event.dataTransfer.files);
  }

  function onPaste(event: ClipboardEvent) {
    if (inactive) return;
    const files = Array.from(event.clipboardData.files ?? []);
    const validos = files.filter((candidate) => aceptaArchivo(candidate, accept));
    const elegidos = validos.length > 0 ? validos : files.slice(0, 1);
    if (elegidos.length > 0) {
      event.preventDefault();
      deliver(elegidos);
    }
  }

  function onKeyDown(event: KeyboardEvent) {
    if (inactive) return;
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      inputRef.current?.click();
    }
  }

  if (busy) {
    const value = Number.isFinite(progress) ? Math.max(0, Math.min(100, progress)) : 0;
    return (
      <div className={styles.wrap}>
        <div className={[styles.zone, styles.busy].join(' ')}>
          <span aria-live="polite" className={styles.label} role="status">Subiendo… {Math.round(value)}%</span>
          <div aria-label="Progreso de subida" aria-valuemax={100} aria-valuemin={0} aria-valuenow={Math.round(value)} className={styles.track} role="progressbar">
            <div className={styles.fill} style={{ width: `${value}%` }} />
          </div>
          {onCancel ? <button className={styles.action} onClick={onCancel} type="button">Cancelar</button> : null}
        </div>
      </div>
    );
  }

  return (
    <div className={styles.wrap}>
      <div
        aria-disabled={disabled || undefined}
        aria-label={label}
        className={[styles.zone, compact ? styles.compact : '', over ? styles.over : '', disabled ? styles.disabled : '', rejected ? styles.rejected : ''].filter(Boolean).join(' ')}
        onClick={() => { if (!inactive) inputRef.current?.click(); }}
        onDragLeave={() => setOver(false)}
        onDragOver={(event) => {
          event.preventDefault();
          if (!inactive) setOver(true);
        }}
        onDrop={onDrop}
        onKeyDown={onKeyDown}
        onPaste={onPaste}
        role="button"
        tabIndex={disabled ? -1 : 0}
      >
        <span className={styles.label}>{label}</span>
        {compact ? null : <span className={styles.hint}>o hacé clic para elegir un archivo</span>}
        {rejected ? <span className={styles.error} role="alert">Ese tipo de archivo no está admitido.</span> : null}
        <input
          accept={accept}
          aria-hidden="true"
          className={styles.input}
          data-testid="dropzone-input"
          disabled={disabled}
          multiple={multiple || undefined}
          onChange={(event) => {
            deliver(event.target.files);
            event.target.value = '';
          }}
          onClick={(event) => event.stopPropagation()}
          ref={inputRef}
          tabIndex={-1}
          type="file"
        />
      </div>
      {secondaryAction ? (
        <button className={styles.action} disabled={disabled} onClick={secondaryAction.onClick} type="button">{secondaryAction.label}</button>
      ) : null}
    </div>
  );
}
