import styles from './FieldTag.module.css';

export type FieldTagStatus = 'manual' | 'suggested' | 'empty';

const label: Record<FieldTagStatus, string> = {
  manual: '● MANUAL',
  suggested: '◔ SUGERIDO',
  empty: '○ VACÍO',
};

interface FieldTagProps {
  status?: FieldTagStatus;
}

export function FieldTag({ status = 'empty' }: FieldTagProps) {
  return <span className={[styles.tag, styles[status]].join(' ')}>{label[status]}</span>;
}
