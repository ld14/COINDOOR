import { useCallback, useEffect, useRef, useState } from 'react';
import { getJob } from '@/lib/api/jobs';
import { createSuggestionJob, type SuggestionsResult } from '@/lib/api/suggestions';

const POLL_MS = 400;

type Phase = 'buscando' | 'resultados' | 'sin-resultados' | 'error';

export function useSuggestionsJob(gameId: string, key: string, open: boolean) {
  const [result, setResult] = useState<SuggestionsResult | null>(null);
  const [phase, setPhase] = useState<Phase>('buscando');
  const requestId = useRef(0);

  const start = useCallback((reintentar = false, source?: string) => {
    const id = ++requestId.current;
    setPhase('buscando');
    setResult(null);
    void (async () => {
      const { jobId } = await createSuggestionJob(gameId, key, reintentar, source);
      while (requestId.current === id) {
        const job = await getJob<SuggestionsResult>(jobId);
        if (requestId.current !== id) return;
        if (job.status === 'succeeded' && job.result) {
          setResult(job.result);
          setPhase(deriveFase(job.result));
          return;
        }
        if (job.status === 'failed' || job.status === 'cancelled') {
          setPhase('error');
          return;
        }
        await new Promise((resolve) => setTimeout(resolve, POLL_MS));
      }
    })();
  }, [gameId, key]);

  useEffect(() => {
    if (open) start();
    else requestId.current += 1;
  }, [open, start]);

  const retryAll = useCallback(() => start(true), [start]);
  const retrySource = useCallback((source: string) => {
    setPhase('buscando');
    void (async () => {
      const { jobId } = await createSuggestionJob(gameId, key, true, source);
      const id = requestId.current;
      while (requestId.current === id) {
        const job = await getJob<SuggestionsResult>(jobId);
        if (requestId.current !== id) return;
        if (job.status === 'succeeded' && job.result) {
          // Merge: keep existing candidates from other sources, replace this source
          setResult((prev) => {
            if (!prev) return job.result;
            const kept = prev.candidatos.filter((c) => c.fuente !== source);
            const nuevos = job.result!.candidatos;
            const merged = { ...job.result!, candidatos: [...kept, ...nuevos] };
            setPhase(deriveFase(merged));
            return merged;
          });
          return;
        }
        if (job.status === 'failed' || job.status === 'cancelled') {
          setPhase('error');
          return;
        }
        await new Promise((resolve) => setTimeout(resolve, POLL_MS));
      }
    })();
  }, [gameId, key]);

  return { phase, result, retry: retryAll, retrySource };
}

function deriveFase(result: SuggestionsResult): Phase {
  if (result.candidatos.length > 0) return 'resultados';
  if (result.respondieron === 0) return 'error';
  return 'sin-resultados';
}
