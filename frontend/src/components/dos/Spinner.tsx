import styles from './Spinner.module.css';

export function Spinner() {
  return <span aria-label="Cargando" className={styles.spinner} role="status" />;
}
