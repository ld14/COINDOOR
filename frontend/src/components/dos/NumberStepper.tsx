import type { KeyboardEvent } from 'react';
import styles from './NumberStepper.module.css';

interface NumberStepperProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  ariaLabel: string;
  disabled?: boolean;
}

export function NumberStepper({ value, onChange, min = 0, max = 99, step = 1, ariaLabel, disabled = false }: NumberStepperProps) {
  const set = (n: number) => {
    const next = Math.max(min, Math.min(max, n));
    if (next !== value) onChange(next);
  };

  function onKeyDown(event: KeyboardEvent) {
    if (disabled) return;
    const actions: Record<string, () => void> = {
      ArrowUp: () => set(value + step),
      ArrowRight: () => set(value + step),
      ArrowDown: () => set(value - step),
      ArrowLeft: () => set(value - step),
      Home: () => set(min),
      End: () => set(max),
    };
    const action = actions[event.key];
    if (action) {
      event.preventDefault();
      action();
    }
  }

  return (
    <div className={styles.stepper}>
      <button aria-label="Disminuir" className={styles.button} disabled={disabled || value <= min} onClick={() => set(value - step)} tabIndex={-1} type="button">−</button>
      <span
        aria-disabled={disabled || undefined}
        aria-label={ariaLabel}
        aria-valuemax={max}
        aria-valuemin={min}
        aria-valuenow={value}
        className={styles.value}
        onKeyDown={onKeyDown}
        role="spinbutton"
        tabIndex={disabled ? -1 : 0}
      >
        {value}
      </span>
      <button aria-label="Aumentar" className={styles.button} disabled={disabled || value >= max} onClick={() => set(value + step)} tabIndex={-1} type="button">+</button>
    </div>
  );
}
