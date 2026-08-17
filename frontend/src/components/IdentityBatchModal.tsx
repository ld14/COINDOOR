import { useCallback, useEffect, useRef, useState } from 'react';
import { DosButton, Modal, Spinner } from '@/components/dos';
import { getJob } from '@/lib/api/jobs';
import { applySuggestion, createIdentityBatchJob, type SuggestionCandidate, type SuggestionsResult } from '@/lib/api/suggestions';
import type { IdentityKey } from '@/lib/domain/types';
import styles from './SuggestionsModal.module.css';

const POLL_MS = 400;
type Phase = 'buscando' | 'resultados' | 'sin-resultados' | 'error';

interface IdentityBatchModalProps {
  gameId: string;
  open: boolean;
  onClose: () => void;
  onApplied: () => void;
}

export function IdentityBatchModal({ gameId, open, onClose, onApplied }: IdentityBatchModalProps) {
  const [result, setResult] = useState<SuggestionsResult | null>(null);
  const [phase, setPhase] = useState<Phase>('buscando');
  const [applying, setApplying] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const requestId = useRef(0);

  const start = useCallback((reintentar = false) => {
    const id = ++requestId.current;
    setPhase('buscando');
    setResult(null);
    setErrorMessage('');
    void (async () => {
      try {
        const { jobId } = await createIdentityBatchJob(gameId, reintentar);
        while (requestId.current === id) {
          const job = await getJob<SuggestionsResult>(jobId);
          if (requestId.current !== id) return;
          if (job.status === 'succeeded' && job.result) {
            setResult(job.result);
            setPhase(job.result.candidatos.length > 0 ? 'resultados' : job.result.respondieron === 0 ? 'error' : 'sin-resultados');
            return;
          }
          if (job.status === 'failed' || job.status === 'cancelled') {
            setPhase('error');
            setErrorMessage(job.error || 'Error desconocido');
            return;
          }
          await new Promise((resolve) => setTimeout(resolve, POLL_MS));
        }
      } catch (e) {
        if (requestId.current === id) {
          setPhase('error');
          setErrorMessage(e instanceof Error ? e.message : 'Error de red');
        }
      }
    })();
  }, [gameId]);

  useEffect(() => {
    if (open) start();
    else requestId.current += 1;
  }, [open, start]);

  async function applyAll() {
    if (!result) return;
    const identityCandidates = result.candidatos.filter((c) => c.kind === 'identity' && c.clase === 'aplicable');
    if (identityCandidates.length === 0) return;
    setApplying(true);
    try {
      for (const candidate of identityCandidates) {
        await applySuggestion(gameId, candidate.key, candidate.id);
      }
      onApplied();
      onClose();
    } catch {
      // errors are non-critical for individual fields
    } finally {
      setApplying(false);
    }
  }

  async function applyOne(candidate: SuggestionCandidate) {
    setApplying(true);
    try {
      await applySuggestion(gameId, candidate.key, candidate.id);
      onApplied();
      onClose();
    } catch {
      // ignore
    } finally {
      setApplying(false);
    }
  }

  function candidateFor(key: string): SuggestionCandidate | undefined {
    return result?.candidatos.find((c) => c.key === key && c.kind === 'identity');
  }

  const IDENTITY_FIELDS: { key: IdentityKey; label: string }[] = [
    { key: 'developer', label: 'Desarrollador' },
    { key: 'publisher', label: 'Editor' },
    { key: 'genre', label: 'Género' },
    { key: 'players', label: 'Jugadores' },
    { key: 'format', label: 'Formato' },
  ];

  return (
    <Modal onClose={onClose} open={open} size="large" title="Sugerencias de identidad">
      <p className={styles.subtitle}>Un solo llamado a la IA completa todos los campos de identidad.</p>

      {phase === 'buscando' ? (
        <div className={styles.state}>
          <Spinner />
          <p>Consultando IA…</p>
        </div>
      ) : null}

      {phase === 'sin-resultados' ? (
        <div className={styles.state}>
          <p className={styles.stateTitle}>SIN RESULTADOS</p>
          <p>No se pudo obtener información para este juego.</p>
          <div className={styles.actions}>
            <DosButton onClick={() => start(true)} variant="primary">Reintentar</DosButton>
            <DosButton onClick={onClose} variant="ghost">Cerrar</DosButton>
          </div>
        </div>
      ) : null}

      {phase === 'error' ? (
        <div className={styles.state}>
          <p className={styles.stateTitle}>ERROR</p>
          <p>{errorMessage || 'Problema al consultar la IA. Reintentá.'}</p>
          <div className={styles.actions}>
            <DosButton onClick={() => start(true)} variant="primary">Reintentar</DosButton>
          </div>
        </div>
      ) : null}

      {phase === 'resultados' && result ? (
        <>
          <div className={styles.grid}>
            {IDENTITY_FIELDS.map(({ key, label }) => {
              const c = candidateFor(key);
              return (
                <div className={styles.batchField} key={key}>
                  <span className={styles.name}>{label}</span>
                  {c ? (
                    <button className={styles.candidate} disabled={applying} onClick={() => applyOne(c)} type="button">
                      <div className={styles.preview}>{c.value}</div>
                      {c.generadoPorIa ? <span className={styles.iaBadge}>IA</span> : null}
                      <span className={styles.source}>{c.fuente}</span>
                    </button>
                  ) : (
                    <span className={styles.empty}>Sin sugerencia</span>
                  )}
                </div>
              );
            })}
          </div>
          <div className={styles.actions} style={{ marginTop: '1rem' }}>
            <DosButton disabled={applying} onClick={applyAll} variant="primary">Aplicar todos</DosButton>
            <DosButton onClick={onClose} variant="ghost">Cerrar</DosButton>
          </div>
          <p className={styles.count}>{result.respondieron} de {result.consultados} fuentes respondieron</p>
        </>
      ) : null}
    </Modal>
  );
}
