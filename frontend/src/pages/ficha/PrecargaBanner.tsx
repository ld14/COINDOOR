import { useEffect, useRef, useState } from 'react';
import { Card, DosButton, ProgressBar } from '@/components/dos';
import { getJob, type JobStatus } from '@/lib/api/jobs';
import type { ResumenPrecarga } from './precarga';
import styles from './ficha.module.css';

interface PrecargaBannerProps {
  jobId: string;
  onComplete: () => void;
}

/** Progreso de la precarga mientras corre el job (ArcadeDB o LaunchBox + IA). Al terminar avisa con `onComplete`. */
export function PrecargaBanner({ jobId, onComplete }: PrecargaBannerProps) {
  const [status, setStatus] = useState<JobStatus>('queued');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [jobResult, setJobResult] = useState<{ estado?: string; romset?: string } | null>(null);
  // La ficha pasa una función nueva en cada render: sin esto el sondeo se reiniciaría todo el tiempo.
  const onCompleteRef = useRef(onComplete);
  useEffect(() => { onCompleteRef.current = onComplete; });

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const poll = async () => {
      try {
        const job = await getJob<{ estado?: string; romset?: string }>(jobId);
        if (cancelled) return;
        setStatus(job.status);
        setProgress(job.progress);
        if (job.status === 'succeeded' || job.status === 'failed' || job.status === 'cancelled') {
          setJobResult(job.result);
          onCompleteRef.current();
          return;
        }
        timer = setTimeout(poll, 500);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Error consultando progreso');
        }
      }
    };
    void poll();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [jobId]);

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
        <Card band="var(--accent-2)" title="PRECARGA DE ARCADEDB">
          <p className={styles.meta}>{reason}</p>
        </Card>
      );
    }
    return null;
  }

  return (
    <Card band="var(--accent-2)" title="PRECARGA DE ARCADEDB">
      <div className={styles.stack}>
        <div className={styles.filaProgreso}>
          <span className={styles.nombre}>{failed ? 'Error en la precarga' : 'Buscando datos en ArcadeDB…'}</span>
          <span className={styles.meta}>{progress}%</span>
        </div>
        <ProgressBar state={failed ? 'error' : 'active'} value={progress} />
        {error ? <p className={styles.error}>{error}</p> : null}
        {failed ? (
          <p className={styles.error}>La precarga falló. Podés reintentar desde la ficha del juego.</p>
        ) : null}
      </div>
    </Card>
  );
}

interface PrecargaResumenProps {
  resumen: ResumenPrecarga;
  /** Nombre de la fuente para el titular: "ArcadeDB", "LaunchBox", … */
  fuente: string;
  aceptando: boolean;
  onAcceptAll: () => void;
  onReviewOneByOne: () => void;
}

/** "ArcadeDB trajo N datos · X aplicados · Y esperan revisión" con la acción para resolver las Y. */
export function PrecargaResumen({ resumen, fuente, aceptando, onAcceptAll, onReviewOneByOne }: PrecargaResumenProps) {
  const { traidos, aplicados, pendientes } = resumen;
  if (pendientes === 0) return null;
  const proporcion = traidos === 0 ? 0 : Math.round((aplicados / traidos) * 100);
  return (
    <section aria-label="Resumen de la precarga" className={styles.banner}>
      <div className={styles.bannerTexto}>
        <p className={styles.bannerTitulo}>
          {`${fuente} trajo ${traidos} ${traidos === 1 ? 'dato' : 'datos'} · ${aplicados} ${aplicados === 1 ? 'aplicado' : 'aplicados'} · `}
          <strong>{`${pendientes} ${pendientes === 1 ? 'espera' : 'esperan'} revisión`}</strong>
        </p>
        <ProgressBar label="Datos aplicados sobre los que trajo la fuente" state="ok" value={proporcion} />
      </div>
      <div className={styles.bannerAcciones}>
        <DosButton disabled={aceptando} onClick={onAcceptAll} variant="primary-small">
          {aceptando ? 'Aceptando…' : 'Aceptar todo'}
        </DosButton>
        <DosButton onClick={onReviewOneByOne} variant="ghost-small">Revisar una por una →</DosButton>
      </div>
    </section>
  );
}
