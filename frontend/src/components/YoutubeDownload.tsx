import { useMutation, useQueryClient } from '@tanstack/react-query';
import { type FormEvent, useState } from 'react';
import { DosButton, DosInput, ProgressBar } from '@/components/dos';
import { cancelJob, getJob } from '@/lib/api/jobs';
import { startYoutubeDownload } from '@/lib/api/media';
import type { MediaField } from '@/lib/domain/types';
import styles from '@/pages/ReadPages.module.css';

const POLL_MS = 500;
const HOSTS = new Set(['youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be']);
const URL_INVALIDA = 'La URL tiene que ser de un video de youtube.com o youtu.be.';
const REEMPLAZO = 'El video actual fue cargado a mano. ¿Reemplazarlo con el de YouTube?';

// Chequeo liviano para avisar sin ir al servidor; la validación que manda es la del backend.
function esDeYoutube(value: string) {
  try {
    return HOSTS.has(new URL(value).hostname);
  } catch {
    return false;
  }
}

interface YoutubeDownloadProps {
  gameId: string;
  current?: MediaField;
  onDownloaded: () => void;
}

export function YoutubeDownload({ gameId, current, onDownloaded }: YoutubeDownloadProps) {
  const queryClient = useQueryClient();
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');
  const [job, setJob] = useState<{ id: string; progress: number } | null>(null);

  // El polling vive dentro de la mutación: termina cuando termina el job, así el cierre
  // (error, refresco de la ficha) se maneja una sola vez.
  const download = useMutation({
    mutationFn: async (value: string) => {
      const { jobId } = await startYoutubeDownload(gameId, value);
      for (;;) {
        const estado = await getJob<{ url: string }>(jobId);
        setJob({ id: jobId, progress: estado.progress });
        if (estado.status !== 'queued' && estado.status !== 'running') return estado;
        await new Promise((resolve) => setTimeout(resolve, POLL_MS));
      }
    },
    onSuccess: async (estado) => {
      if (estado.status === 'failed') setError(estado.error ?? '');
      if (estado.status !== 'succeeded') return;
      setUrl('');
      onDownloaded();
      await queryClient.invalidateQueries({ queryKey: ['game', gameId] });
    },
    onError: (err) => setError(err.message),
    onSettled: () => setJob(null),
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const value = url.trim();
    setError('');
    if (!esDeYoutube(value)) {
      setError(URL_INVALIDA);
      return;
    }
    if (current?.status === 'manual' && !window.confirm(REEMPLAZO)) return;
    download.mutate(value);
  };

  const progress = job?.progress ?? 0;

  return (
    <form className={styles.stack} onSubmit={submit}>
      <label className={styles.field}>
        <span className={styles.label}>URL de YouTube</span>
        <DosInput
          disabled={download.isPending}
          onChange={(event) => setUrl(event.target.value)}
          value={url}
        />
      </label>
      <div className={styles.toolbar}>
        <DosButton disabled={download.isPending} type="submit" variant="primary-small">Descargar</DosButton>
      </div>
      {download.isPending ? (
        <>
          <div className={styles.fieldTop}>
            <span className={styles.meta}>Descargando de YouTube… {progress}%</span>
            <DosButton
              disabled={!job}
              onClick={() => {
                if (job) void cancelJob(job.id);
              }}
              variant="ghost-small"
            >
              Cancelar
            </DosButton>
          </div>
          <ProgressBar value={progress} />
        </>
      ) : null}
      {error ? <p className={styles.error}>{error}</p> : null}
    </form>
  );
}
