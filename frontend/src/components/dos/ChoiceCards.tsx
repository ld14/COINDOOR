import type { KeyboardEvent } from 'react';
import { useRef } from 'react';
import styles from './ChoiceCards.module.css';

export interface ChoiceOption {
  value: string;
  label: string;
  subtitle?: string;
  /** Marca la opción como recomendada; si es string, indica quién la recomienda. */
  recommended?: boolean | string;
  disabled?: boolean;
}

interface ChoiceCardsProps {
  options: ChoiceOption[];
  value: string;
  onChange: (value: string) => void;
  ariaLabel: string;
}

export function ChoiceCards({ options, value, onChange, ariaLabel }: ChoiceCardsProps) {
  const refs = useRef<Array<HTMLButtonElement | null>>([]);
  const activeIndex = options.findIndex((option) => option.value === value && !option.disabled);
  const tabbable = activeIndex >= 0 ? activeIndex : options.findIndex((option) => !option.disabled);

  function move(from: number, step: 1 | -1) {
    for (let i = 1; i <= options.length; i += 1) {
      const next = (from + step * i + options.length * i) % options.length;
      if (!options[next].disabled) {
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
        const recommended = Boolean(option.recommended);
        const subtitle = recommended
          ? typeof option.recommended === 'string' ? `recomendado por ${option.recommended}` : 'recomendado'
          : option.subtitle;
        return (
          <button
            aria-checked={checked}
            className={[styles.card, checked ? styles.selected : '', recommended ? styles.recommended : ''].filter(Boolean).join(' ')}
            disabled={option.disabled}
            key={option.value}
            onClick={() => onChange(option.value)}
            onKeyDown={(event) => onKeyDown(event, index)}
            ref={(node) => { refs.current[index] = node; }}
            role="radio"
            tabIndex={index === tabbable ? 0 : -1}
            type="button"
          >
            <span className={styles.label}>{option.label}</span>
            {subtitle ? <span className={styles.subtitle}>{subtitle}</span> : null}
          </button>
        );
      })}
    </div>
  );
}
