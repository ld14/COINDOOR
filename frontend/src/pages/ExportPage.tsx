import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { DosButton, Panel, ProgressBar, SectionHeader, Spinner, SunkenBox } from '@/components/dos';
import { createExport, getExportOptions, getExportStatus, type ExportOption, type ExportResult } from '@/lib/api/export';
import styles from './ReadPages.module.css';

export function ExportPage() {
  const { gameId } = useParams<{ gameId: string }>();
  const [options, setOptions] = useState<{ obligatorio: ExportOption[]; opcional: ExportOption[] } | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<ExportResult | null>(null);
  const [runId, setRunId] = useState<string | null>(null);

  useEffect(() => {
    if (!gameId) return;
    setLoading(true);
    getExportOptions(gameId)
      .then((data) => {
        setOptions(data);
        const initial = new Set(data.obligatorio.map((o) => o.key));
        setSelected(initial);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Error al cargar opciones'))
      .finally(() => setLoading(false));
  }, [gameId]);

  useEffect(() => {
    if (!runId) return;
    const interval = setInterval(() => {
      getExportStatus(runId).then((job) => {
        setProgress(job.progress);
        if (job.status === 'succeeded') {
          setResult(job.result);
          setRunId(null);
          clearInterval(interval);
        } else if (job.status === 'failed') {
          setError(job.error || 'Error desconocido');
          setRunId(null);
          clearInterval(interval);
        }
      });
    }, 500);
    return () => clearInterval(interval);
  }, [runId]);

  const toggleOptional = useCallback((key: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }, []);

  const toggleAllOptional = useCallback(() => {
    if (!options) return;
    const availableKeys = options.opcional.filter((o) => o.disponible).map((o) => o.key);
    const allSelected = availableKeys.every((key) => selected.has(key));
    setSelected((prev) => {
      const next = new Set(prev);
      if (allSelected) {
        availableKeys.forEach((key) => next.delete(key));
      } else {
        availableKeys.forEach((key) => next.add(key));
      }
      return next;
    });
  }, [options, selected]);

  const totalBytes = options
    ? options.obligatorio.filter((o) => selected.has(o.key)).reduce((sum, o) => sum + o.bytes, 0) +
      options.opcional.filter((o) => selected.has(o.key)).reduce((sum, o) => sum + o.bytes, 0)
    : 0;

  async function handleExport() {
    if (!gameId) return;
    setLoading(true);
    setError('');
    try {
      const job = await createExport(gameId, Array.from(selected));
      setRunId(job.runId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al iniciar export');
    } finally {
      setLoading(false);
    }
  }

  if (!gameId) {
    return (
      <div className={styles.page}>
        <Panel>
          <SectionHeader>EXPORTAR</SectionHeader>
          <SunkenBox>
            <p className={styles.empty}>Seleccioná un juego desde la lista para exportarlo.</p>
            <Link to="/juegos"><DosButton variant="primary-small">Ir a Juegos</DosButton></Link>
          </SunkenBox>
        </Panel>
      </div>
    );
  }

  if (result) {
    return (
      <div className={styles.page}>
        <Panel>
          <SectionHeader>EXPORTAR — RESULTADO</SectionHeader>
          <SunkenBox className={styles.stack}>
            <p className={styles.name}>Export completado</p>
            <p className={styles.meta}>Archivo: {result.file}</p>
            <p className={styles.meta}>Tamaño: {(result.bytes / 1024).toFixed(1)} KB</p>
            <p className={styles.meta}>Contenido: {result.incluye.join(', ')}</p>
            <div className={styles.toolbar}>
              <Link to="/juegos"><DosButton variant="primary-small">Volver a Juegos</DosButton></Link>
              <DosButton onClick={() => setResult(null)} variant="ghost-small">Exportar otro</DosButton>
            </div>
          </SunkenBox>
        </Panel>
      </div>
    );
  }

  if (runId) {
    return (
      <div className={styles.page}>
        <Panel>
          <SectionHeader>EXPORTAR — EN PROGRESO</SectionHeader>
          <SunkenBox className={styles.stack}>
            <Spinner />
            <ProgressBar value={progress} />
            <p className={styles.meta}>{progress}% completado</p>
          </SunkenBox>
        </Panel>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <Panel>
        <SectionHeader>EXPORTAR</SectionHeader>
        <SunkenBox className={styles.stack}>
          {loading ? <Spinner /> : null}
          {error ? <p className={styles.error}>{error}</p> : null}
          {options ? (
            <>
              <div>
                <p className={styles.name}>Obligatorio</p>
                {options.obligatorio.map((opt) => (
                  <label className={styles.field} key={opt.key}>
                    <input checked disabled type="checkbox" />
                    <span className={styles.label}>{opt.label}</span>
                    <span className={styles.meta}>{formatBytes(opt.bytes)}</span>
                  </label>
                ))}
              </div>
              <div>
                <p className={styles.name}>Opcional</p>
                <label className={styles.field}>
                  <input
                    checked={options.opcional.filter((o) => o.disponible).length > 0 && options.opcional.filter((o) => o.disponible).every((o) => selected.has(o.key))}
                    onChange={toggleAllOptional}
                    type="checkbox"
                  />
                  <span className={styles.label}>Seleccionar todo</span>
                </label>
                {options.opcional.map((opt) => (
                  <label className={styles.field} key={opt.key}>
                    <input
                      checked={selected.has(opt.key)}
                      disabled={!opt.disponible}
                      onChange={() => toggleOptional(opt.key)}
                      type="checkbox"
                    />
                    <span className={styles.label}>{opt.label}</span>
                    <span className={styles.meta}>{opt.disponible ? formatBytes(opt.bytes) : '—'}</span>
                  </label>
                ))}
              </div>
              <div className={styles.toolbar}>
                <span className={styles.name}>Total: {formatBytes(totalBytes)}</span>
                <DosButton onClick={handleExport} variant="primary-small">Exportar</DosButton>
              </div>
            </>
          ) : null}
        </SunkenBox>
      </Panel>
    </div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
