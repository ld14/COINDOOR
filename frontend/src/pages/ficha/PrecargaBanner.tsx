import { useEffect, useState } from 'react';
import { Panel, ProgressBar, SectionHeader, SunkenBox } from '@/components/dos';
import { getJob, type JobStatus } from '@/lib/api/jobs';
import styles from '../ReadPages.module.css';

interface PrecargaBannerProps {
  jobId: string;
  onComplete: () => void;
}

export function PrecargaBanner({ jobId, onComplete }: PrecargaBannerProps) {
  const [status, setStatus] = useState<JobStatus>('queued');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [jobResult, setJobResult] = useState<{ estado?: string; romset?: string } | null>(null);

  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      try {
        const job = await getJob<{ estado?: string; romset?: string }>(jobId);
        if (cancelled) return;
        setStatus(job.status);
        setProgress(job.progress);
        if (job.status === 'succeeded' || job.status === 'failed' || job.status === 'cancelled') {
          setJobResult(job.result);
          onComplete();
          return;
        }
        setTimeout(poll, 500);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Error consultando progreso');
        }
      }
    };
    poll();
    return () => { cancelled = true; };
  }, [jobId, onComplete]);

  const failed = status === 'failed' || (status === 'succeeded' && jobResult && 'error' in jobResult);
  const notFound = status === 'succeeded' && jobResult?.estado === 'no-encontrado';
  const noRomset = status === 'succeeded' && jobResult?.estado === 'sin-romset';
  const systemUnsupported = status === 'succeeded' && jobResult?.estado === 'sistema-no-soportado';
  const isActive = status === 'queued' || status === 'running';

  if (!isActive && !failed) {
    if (notFound || noRomset || systemUnsupported) {
      const reason = notFound
        ? `Romset "${jobResult?.romset}" no encontrado en ArcadeDB.`
        : noRomset
          ? 'El juego no tiene romset definido.'
          : 'El sistema no es compatible con ArcadeDB.';
      return (
        <Panel>
          <SectionHeader>PRECARGA DE ARCADEDB</SectionHeader>
          <SunkenBox className={styles.stack}>
            <p className={styles.meta}>{reason}</p>
          </SunkenBox>
        </Panel>
      );
    }
    return null;
  }

  return (
    <Panel>
      <SectionHeader>PRECARGA DE ARCADEDB</SectionHeader>
      <SunkenBox className={styles.stack}>
        <div className={styles.fieldTop}>
          <span className={styles.name}>
            {failed ? 'Error en la precarga' : 'Buscando datos en ArcadeDB…'}
          </span>
          <span className={styles.meta}>{progress}%</span>
        </div>
        <ProgressBar value={progress} />
        {error ? <p className={styles.error}>{error}</p> : null}
        {failed ? (
          <p className={styles.error}>La precarga falló. Podés reintentar desde la ficha del juego.</p>
        ) : null}
      </SunkenBox>
    </Panel>
  );
}
