import styles from './StatusBar.module.css';

const entries = [
  ['F1', 'Ayuda'],
  ['F2', 'Sistemas'],
  ['F3', 'Juegos'],
  ['F4', 'Exportar'],
  ['Esc', 'Cerrar'],
];

export function StatusBar() {
  return <footer className={styles.bar}>{entries.map(([key, label]) => <span key={key}><span className={styles.key}>{key}</span> {label}</span>)}</footer>;
}
