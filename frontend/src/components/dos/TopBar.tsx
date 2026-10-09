import { useEffect, useRef, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { formatHace, saveStatusStore, useSaveStatus } from '@/hooks/useSaveStatus';
import type { ContractStatus } from '@/lib/contractStatus';
import { ContractBadge } from './ContractBadge';
import styles from './TopBar.module.css';

interface TopBarProps {
  contract?: ContractStatus;
}

function isTypingTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) return false;
  return target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName);
}

/** Estado del autosave (DESIGN_SPEC §4). No ocupa lugar mientras nada se guardó en la sesión. */
function SaveIndicator() {
  const status = useSaveStatus();
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (status.kind !== 'saved') return undefined;
    setNow(Date.now());
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [status]);

  if (status.kind === 'idle') return <span className={styles.save} role="status" />;
  if (status.kind === 'saving') {
    return <span className={styles.save} role="status"><i aria-hidden="true" className={[styles.dot, styles.dotSaving].join(' ')} />Guardando…</span>;
  }
  if (status.kind === 'saved') {
    return <span className={styles.save} role="status"><i aria-hidden="true" className={styles.dot} />{`Guardado · ${formatHace(status.savedAt, now)}`}</span>;
  }
  return (
    <span className={[styles.save, styles.saveError].join(' ')} role="status" title={status.message}>
      Error al guardar
      {status.canRetry ? (
        <>
          {' — '}
          <button className={styles.retry} onClick={() => saveStatusStore.retry()} type="button">Reintentar</button>
        </>
      ) : null}
    </span>
  );
}

/** Barra superior: marca, búsqueda global (`/` la enfoca) e indicador del contrato.
 *
 * `Ctrl+K` queda reservado para una paleta de comandos; todavía no hace nada.
 */
export function TopBar({ contract }: TopBarProps) {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState('');

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key !== '/' || event.defaultPrevented) return;
      if (event.ctrlKey || event.metaKey || event.altKey) return;
      if (isTypingTarget(event.target)) return;
      if (document.querySelector('[role="dialog"][aria-modal="true"]')) return;
      event.preventDefault();
      inputRef.current?.focus();
      inputRef.current?.select();
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    const q = query.trim();
    navigate(q ? `/juegos?q=${encodeURIComponent(q)}` : '/juegos');
  }

  return (
    <header className={styles.topbar}>
      <div className={styles.brand}>
        <span aria-hidden="true" className={styles.logo}><i /><i /><i /></span>
        <span className={styles.name}>COINDOOR</span>
        <span className={styles.tagline}>preparador de metadata arcade</span>
      </div>
      <form className={styles.search} onSubmit={onSubmit} role="search">
        <input
          aria-label="Buscar juego, sistema o romset"
          className={styles.input}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={(event) => { if (event.key === 'Escape') event.currentTarget.blur(); }}
          placeholder="Buscar juego, sistema o romset…"
          ref={inputRef}
          type="search"
          value={query}
        />
        <kbd aria-hidden="true" className={styles.kbd}>/</kbd>
      </form>
      <SaveIndicator />
      <ContractBadge status={contract} />
    </header>
  );
}
