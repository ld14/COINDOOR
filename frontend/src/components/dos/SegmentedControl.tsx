import type { KeyboardEvent } from 'react';
import { useRef } from 'react';
import styles from './SegmentedControl.module.css';

export interface SegmentedOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SegmentedControlProps {
  options: SegmentedOption[];
  value: string;
  onChange: (value: string) => void;
  ariaLabel: string;
  disabled?: boolean;
}

export function SegmentedControl({ options, value, onChange, ariaLabel, disabled = false }: SegmentedControlProps) {
  const refs = useRef<Array<HTMLButtonElement | null>>([]);
  const enabled = (index: number) => !disabled && !options[index].disabled;
  const activeIndex = options.findIndex((option) => option.value === value);
  const tabbable = activeIndex >= 0 && enabled(activeIndex) ? activeIndex : options.findIndex((_, i) => enabled(i));

  function move(from: number, step: 1 | -1) {
    for (let i = 1; i <= options.length; i += 1) {
      const next = (from + step * i + options.length * i) % options.length;
      if (enabled(next)) {
        onChange(options[next].value);
        refs.current[next]?.focus();
        return;
      }
    }
  }

  function onKeyDown(event: KeyboardEvent, index: number) {
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
      event.preventDefault();
      move(index, 1);
    } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
      event.preventDefault();
      move(index, -1);
    }
  }

  return (
    <div aria-label={ariaLabel} className={styles.group} role="radiogroup">
      {options.map((option, index) => {
        const checked = option.value === value;
        return (
          <button
            aria-checked={checked}
            className={[styles.segment, checked ? styles.active : '', option.disabled ? styles.impossible : ''].filter(Boolean).join(' ')}
            disabled={!enabled(index)}
            key={option.value}
            onClick={() => onChange(option.value)}
            onKeyDown={(event) => onKeyDown(event, index)}
            ref={(node) => { refs.current[index] = node; }}
            role="radio"
            tabIndex={index === tabbable ? 0 : -1}
            type="button"
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
