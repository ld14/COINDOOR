import { NavLink, useLocation } from 'react-router-dom';
import styles from './Rail.module.css';

export interface RailCounts {
  /** Fichas de juegos. */
  games?: number;
  systems?: number;
  /** ROMs instalados que todavía no tienen ficha. */
  romsWithoutSheet?: number;
  /** Juegos listos que todavía no se exportaron. */
  pendingExport?: number;
}

interface RailProps {
  /** `undefined` en un contador = todavía cargando o sin dato: no se muestra. */
  counts?: RailCounts;
}

interface RailItem {
  label: string;
  to: string;
  icon: string;
  count?: keyof RailCounts;
  hint?: string;
}

const items: RailItem[] = [
  { label: 'Sistemas', to: '/sistemas', icon: '▦', count: 'systems' },
  { label: 'Juegos', to: '/juegos', icon: '▶', count: 'games' },
  { label: 'Nuevo juego', to: '/juegos/nuevo', icon: '+', count: 'romsWithoutSheet', hint: 'ROMs sin ficha' },
  { label: 'Exportar', to: '/exportar', icon: '⇪', count: 'pendingExport', hint: 'pendientes de exportar' },
  { label: 'Configuración', to: '/configuracion', icon: '⚙' },
];

/** Navegación vertical con contadores reales. Bajo 900px se reduce a íconos. */
export function Rail({ counts = {} }: RailProps) {
  const { pathname } = useLocation();

  return (
    <nav aria-label="Secciones" className={styles.rail}>
      {items.map((item) => {
        const count = item.count ? counts[item.count] : undefined;
        // `/juegos/nuevo` cuelga de `/juegos` pero tiene su propio ítem.
        const shadowed = item.to === '/juegos' && pathname === '/juegos/nuevo';
        return (
          <NavLink
            className={({ isActive }) => [styles.link, isActive && !shadowed ? styles.active : ''].filter(Boolean).join(' ')}
            key={item.to}
            title={item.hint && count !== undefined ? `${count} ${item.hint}` : item.label}
            to={item.to}
          >
            <span aria-hidden="true" className={styles.icon}>{item.icon}</span>
            <span className={styles.label}>{item.label}</span>
            {count !== undefined && <span className={styles.count}>{count}</span>}
          </NavLink>
        );
      })}
    </nav>
  );
}
