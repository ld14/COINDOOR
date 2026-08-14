import { DosButton, Modal, Spinner } from '@/components/dos';
import { useSuggestionsJob } from '@/hooks/useSuggestionsJob';
import type { SuggestionCandidate } from '@/lib/api/suggestions';
import styles from './SuggestionsModal.module.css';

const MANUAL_REPLACE_CONFIRM = 'Este campo fue cargado a mano. ¿Reemplazarlo por la sugerencia elegida?';

interface SuggestionsModalProps {
  fieldKey: string;
  gameId: string;
  hasContent: boolean;
  isManual: boolean;
  label: string;
  onApply: (candidateId: string) => void;
  onClose: () => void;
  open: boolean;
}

export function SuggestionsModal({ fieldKey, gameId, hasContent, isManual, label, onApply, onClose, open }: SuggestionsModalProps) {
  const { phase, result, retry } = useSuggestionsJob(gameId, fieldKey, open);

  function pick(candidate: SuggestionCandidate) {
    if (candidate.clase === 'referencia') {
      if (candidate.origenUrl) window.open(candidate.origenUrl, '_blank', 'noopener');
      return;
    }
    if (isManual && !window.confirm(MANUAL_REPLACE_CONFIRM)) return;
    onApply(candidate.id);
    onClose();
  }

  return (
    <Modal onClose={onClose} open={open} size="large" title={`Sugerencias — ${label}`}>
      <p className={styles.subtitle}>Elegí una opción. Lo que ya tenés cargado cuenta como candidato — quedárselo es el default.</p>

      {phase === 'buscando' ? (
        <div className={styles.state}>
          <Spinner />
          <p>Buscando en fuentes externas…</p>
        </div>
      ) : null}

      {phase === 'sin-resultados' ? (
        <div className={styles.state}>
          <p className={styles.stateTitle}>SIN RESULTADOS</p>
          <p>Pasa seguido con juegos oscuros. Podés reintentar, ajustar la búsqueda o cargar a mano.</p>
          <div className={styles.actions}>
            <DosButton onClick={() => retry()} variant="primary">Reintentar</DosButton>
            <DosButton onClick={onClose} variant="ghost">Cargar a mano</DosButton>
          </div>
        </div>
      ) : null}

      {phase === 'error' ? (
        <div className={styles.state}>
          <p className={styles.stateTitle}>ERROR DE LA FUENTE EXTERNA</p>
          <p>Problema temporal y ajeno a tu juego. Reintentá en vez de abandonar.</p>
          <div className={styles.actions}>
            <DosButton onClick={() => retry()} variant="primary">Reintentar</DosButton>
          </div>
        </div>
      ) : null}

      {phase === 'resultados' && result ? (
        <>
          <div className={styles.grid}>
            {hasContent ? (
              <button className={`${styles.candidate} ${styles.current}`} onClick={onClose} type="button">
                <div className={styles.preview}>Tu archivo actual</div>
                <span className={styles.name}>Tu archivo actual</span>
              </button>
            ) : null}
            {result.candidatos.map((candidate) => (
              <button className={styles.candidate} key={candidate.id} onClick={() => pick(candidate)} type="button">
                <div className={styles.preview}>{candidate.previewUrl ?? candidate.value ?? candidate.nombre}</div>
                {candidate.generadoPorIa ? <span className={styles.iaBadge}>IA</span> : null}
                <span className={styles.name}>{candidate.nombre}</span>
                <span className={styles.source}>{candidate.fuente}</span>
                {candidate.clase === 'referencia' ? <span className={styles.referenciaBadge}>Abre enlace, no aplica</span> : null}
              </button>
            ))}
          </div>
          <p className={styles.count}>{result.respondieron} de {result.consultados} fuentes respondieron</p>
        </>
      ) : null}
    </Modal>
  );
}
