import { NavLink } from 'react-router-dom';
import styles from './MenuBar.module.css';

const items = [
  { label: 'Sistemas', to: '/sistemas' },
  { label: 'Juegos', to: '/juegos' },
  { label: 'Nuevo juego', to: '/juegos/nuevo' },
  { label: 'Exportar', to: '/exportar' },
];

export function MenuBar() {
  return (
    <nav aria-label="Secciones" className={styles.menu}>
      <div className={styles.header}>COINDOOR</div>
      <div className={styles.links}>
        {items.map((item) => (
          <NavLink className={({ isActive }) => [styles.link, isActive ? styles.active : ''].filter(Boolean).join(' ')} key={item.to} to={item.to}>{item.label}</NavLink>
        ))}
      </div>
      <div className={styles.footer}>0 juegos cargados</div>
    </nav>
  );
}
