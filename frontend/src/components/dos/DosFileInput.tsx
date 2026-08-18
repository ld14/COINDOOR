import { useRef } from 'react';
import { DosButton } from './DosButton';
import styles from './DosFileInput.module.css';

interface DosFileInputProps {
  accept?: string;
  ariaLabel?: string;
  fileName?: string;
  onChange: (file: File | null) => void;
}

export function DosFileInput({ accept, ariaLabel, fileName, onChange }: DosFileInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className={styles.container}>
      <input
        accept={accept}
        aria-label={ariaLabel}
        className={styles.input}
        onChange={(event) => onChange(event.target.files?.[0] ?? null)}
        ref={inputRef}
        type="file"
      />
      <DosButton onClick={() => inputRef.current?.click()} variant="ghost-small" type="button">
        Seleccionar archivo
      </DosButton>
      {fileName ? <span className={styles.fileName}>{fileName}</span> : null}
    </div>
  );
}
