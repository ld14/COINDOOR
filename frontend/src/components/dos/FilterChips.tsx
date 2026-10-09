import styles from './FilterChips.module.css';

export interface FilterChipItem {
  id: string;
  label: string;
  count?: number;
}

interface FilterChipsProps {
  items: FilterChipItem[];
  /** Ids seleccionados. En modo single hay a lo sumo uno; vacío = sin filtro. */
  value: string[];
  onChange: (value: string[]) => void;
  /** multi (por defecto): cada chip alterna. single: elegir uno reemplaza; volver a pulsarlo lo quita. */
  mode?: 'multi' | 'single';
  'aria-label'?: string;
  className?: string;
}

export function FilterChips({ items, value, onChange, mode = 'multi', className, 'aria-label': ariaLabel = 'Sistemas' }: FilterChipsProps) {
  function toggle(id: string) {
    const selected = value.includes(id);
    if (mode === 'single') onChange(selected ? [] : [id]);
    else onChange(selected ? value.filter((v) => v !== id) : [...value, id]);
  }

  return (
    <div aria-label={ariaLabel} className={[styles.chips, className].filter(Boolean).join(' ')} role="group">
      {items.map((item) => {
        const pressed = value.includes(item.id);
        return (
          <button
            aria-pressed={pressed}
            className={[styles.chip, pressed ? styles.pressed : ''].filter(Boolean).join(' ')}
            key={item.id}
            onClick={() => toggle(item.id)}
            type="button"
          >
            {item.label}
            {item.count !== undefined ? <span className={styles.count}>{item.count}</span> : null}
          </button>
        );
      })}
    </div>
  );
}
