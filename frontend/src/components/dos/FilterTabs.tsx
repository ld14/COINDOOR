import { useRef } from 'react';
import type { KeyboardEvent } from 'react';
import styles from './FilterTabs.module.css';

export interface FilterTabItem {
  id: string;
  label: string;
  count?: number;
}

interface FilterTabsProps {
  items: FilterTabItem[];
  value: string;
  onChange: (id: string) => void;
  'aria-label'?: string;
  className?: string;
}

export function FilterTabs({ items, value, onChange, className, 'aria-label': ariaLabel = 'Filtro' }: FilterTabsProps) {
  const refs = useRef<Array<HTMLButtonElement | null>>([]);
  const selectedIndex = Math.max(0, items.findIndex((item) => item.id === value));

  function move(index: number) {
    if (items.length === 0) return;
    const next = (index + items.length) % items.length;
    onChange(items[next].id);
    refs.current[next]?.focus();
  }

  function onKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    if (event.key === 'ArrowRight') { event.preventDefault(); move(index + 1); }
    else if (event.key === 'ArrowLeft') { event.preventDefault(); move(index - 1); }
    else if (event.key === 'Home') { event.preventDefault(); move(0); }
    else if (event.key === 'End') { event.preventDefault(); move(items.length - 1); }
  }

  return (
    <div aria-label={ariaLabel} className={[styles.tabs, className].filter(Boolean).join(' ')} role="tablist">
      {items.map((item, index) => {
        const selected = index === selectedIndex;
        return (
          <button
            aria-selected={selected}
            className={[styles.tab, selected ? styles.selected : ''].filter(Boolean).join(' ')}
            key={item.id}
            onClick={() => onChange(item.id)}
            onKeyDown={(event) => onKeyDown(event, index)}
            ref={(node) => { refs.current[index] = node; }}
            role="tab"
            tabIndex={selected ? 0 : -1}
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
