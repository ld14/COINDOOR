import { DosButton } from './DosButton';
import styles from './InlineSuggestion.module.css';

interface InlineSuggestionProps {
  source: string;
  value: string;
  onUse: () => void;
  onIgnore: () => void;
}

export function InlineSuggestion({ source, value, onUse, onIgnore }: InlineSuggestionProps) {
  return (
    <div aria-label={`Sugerencia de ${source}`} className={styles.box} role="group">
      <span className={styles.text}>
        {source} sugiere: <strong className={styles.value}>{value}</strong> —
      </span>
      <DosButton onClick={onUse} variant="primary-small">Usar</DosButton>
      <DosButton onClick={onIgnore} variant="ghost-small">Ignorar</DosButton>
    </div>
  );
}
