import { useCallback, useEffect, useRef, useState } from 'react';
import { getJob } from '@/lib/api/jobs';
import { createSuggestionJob, type SuggestionsResult } from '@/lib/api/suggestions';

const POLL_MS = 400;

type Phase = 'buscando' | 'resultados' | 'sin-resultados' | 'error';

export function useSuggestionsJob(gameId: string, key: string, open: boolean) {
  const [result, setResult] = useState<SuggestionsResult | null>(null);
  const [phase, setPhase] = useState<Phase>('buscando');
  const requestId = useRef(0);

  const start = useCallback((reintentar = false) => {
    const id = ++requestId.current;
    setPhase('buscando');
    setResult(null);
    void (async () => {
      const { jobId } = await createSuggestionJob(gameId, key, reintentar);
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

  return { phase, result, retry: () => start(true) };
}

function deriveFase(result: SuggestionsResult): Phase {
  if (result.candidatos.length > 0) return 'resultados';
  if (result.respondieron === 0) return 'error';
  return 'sin-resultados';
}
