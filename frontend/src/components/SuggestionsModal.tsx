import { DosButton, Modal, Spinner } from '@/components/dos';
import { useSuggestionsJob } from '@/hooks/useSuggestionsJob';
import type { SuggestionCandidate, SuggestionTrace } from '@/lib/api/suggestions';
import styles from './SuggestionsModal.module.css';

const MANUAL_REPLACE_CONFIRM = 'Este campo fue cargado a mano. ¿Reemplazarlo por la sugerencia elegida?';

function formatCheatPreview(value: string): string {
  try {
    const data = JSON.parse(value);
    const groups = data.groups as Array<{ name: string; entries: Array<{ name: string; input: string }> }>;
    if (!Array.isArray(groups) || groups.length === 0) return 'Sin trucos';
    return groups.map((g) => {
      const entries = g.entries?.map((e) => `  · ${e.name}: ${e.input}`).join('\n') ?? '';
      return `${g.name}\n${entries}`;
    }).join('\n\n');
  } catch {
    return value;
  }
}

interface SuggestionsModalProps {
  fieldKey: string;
  gameId: string;
  hasContent: boolean;
  isManual: boolean;
  label: string;
  onApply: (candidateId: string) => void;
  onClose: () => void;
  open: boolean;
  current?: { previewUrl?: string | null; value?: string | null };
}

const TODAS_LAS_FUENTES = ['ArcadeDB', 'Image Search', 'Launchbox'];

export function SuggestionsModal({ fieldKey, gameId, hasContent, isManual, label, onApply, onClose, open, current }: SuggestionsModalProps) {
  const { phase, result, retry, retrySource } = useSuggestionsJob(gameId, fieldKey, open);

  function pick(candidate: SuggestionCandidate) {
    if (candidate.clase === 'referencia') {
      if (candidate.origenUrl) window.open(candidate.origenUrl, '_blank', 'noopener');
      return;
    }
    if (isManual && !window.confirm(MANUAL_REPLACE_CONFIRM)) return;
    onApply(candidate.id);
    onClose();
  }

  // Agrupar candidatos por fuente
  const porFuente = new Map<string, SuggestionCandidate[]>();
  for (const fuente of TODAS_LAS_FUENTES) {
    porFuente.set(fuente, []);
  }
  if (result) {
    for (const c of result.candidatos) {
      const lista = porFuente.get(c.fuente) ?? [];
      lista.push(c);
      porFuente.set(c.fuente, lista);
    }
  }

  // Fuentes que no respondieron
  const fuentesNoOk = new Set<string>();
  if (result) {
    for (const trace of result.fuentes) {
      if (trace.estado !== 'ok') fuentesNoOk.add(trace.nombre);
    }
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
          {hasContent ? (
            <div className={styles.sourceSection}>
              <div className={styles.sourceHeaderRow}>
                <h4 className={styles.sourceHeader}>Actual</h4>
              </div>
              <div className={styles.grid}>
                <button className={`${styles.candidate} ${styles.current}`} onClick={onClose} type="button">
                  <div className={styles.preview}>
                    {current?.previewUrl ? (
                      <img alt="Tu archivo actual" className={styles.previewImage} src={current.previewUrl} />
                    ) : current?.value ? (
                      <pre className={styles.previewText}>{fieldKey === 'cheats' ? formatCheatPreview(current.value) : current.value}</pre>
                    ) : (
                      'Tu archivo actual'
                    )}
                  </div>
                  <span className={styles.name}>Tu archivo actual</span>
                </button>
              </div>
            </div>
          ) : null}

          {[...porFuente.entries()].map(([fuente, items]) => (
            <div key={fuente} className={styles.sourceSection}>
              <div className={styles.sourceHeaderRow}>
                <h4 className={styles.sourceHeader}>{fuente}</h4>
                <span className={styles.sourceCount}>{items.length}</span>
                {fuentesNoOk.has(fuente) && items.length === 0 && (
                  <DosButton
                    onClick={() => retrySource(fuente)}
                    variant="ghost-small"
                  >
                    Reintentar
                  </DosButton>
                )}
              </div>
              {items.length > 0 ? (
                <div className={styles.grid}>
                  {items.map((candidate) => (
                    <button className={styles.candidate} key={candidate.id} onClick={() => pick(candidate)} type="button">
                      <div className={styles.preview}>
                        {candidate.previewUrl && candidate.previewUrl.startsWith('http') ? (
                          <img alt={candidate.nombre} className={styles.previewImage} src={candidate.previewUrl} />
                        ) : candidate.kind === 'text' && candidate.value ? (
                          <pre className={styles.previewText}>{fieldKey === 'cheats' ? formatCheatPreview(candidate.value) : candidate.value}</pre>
                        ) : candidate.mediaUrl && candidate.mediaUrl.startsWith('http') ? (
                          <img alt={candidate.nombre} className={styles.previewImage} src={candidate.mediaUrl} />
                        ) : (
                          candidate.previewUrl ?? candidate.nombre
                        )}
                      </div>
                      {candidate.generadoPorIa ? <span className={styles.iaBadge}>IA</span> : null}
                      <span className={styles.name}>{candidate.nombre}</span>
                      {candidate.clase === 'referencia' ? <span className={styles.referenciaBadge}>Abre enlace, no aplica</span> : null}
                    </button>
                  ))}
                </div>
              ) : (
                <p className={styles.empty}>Sin resultados</p>
              )}
            </div>
          ))}
        </>
      ) : null}
    </Modal>
  );
}
