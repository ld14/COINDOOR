import { useState } from 'react';
import { Card, DosButton, OriginChip, ProgressBar, Spinner } from '@/components/dos';
import { Dropzone } from '@/components/dos/Dropzone';
import type { Game } from '@/lib/domain/types';
import { searchManuals, type ManualSearchResult } from '@/lib/api/manuals';
import styles from './manual.module.css';

/** El backend puede informar páginas y tamaño cuando la fuente los conoce. */
type ResultadoManual = ManualSearchResult & { pages?: number; sizeBytes?: number };

const ESTADO_MANUAL: Record<string, string> = {
  unprocessed: 'sin procesar',
  processing: 'procesando',
  processed: 'listo',
  failed: 'falló',
};

function tamano(bytes?: number): string {
  if (!bytes) return '';
  return bytes >= 1048576 ? `${(bytes / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

export function ManualSection({ game, onUpload, onDelete }: { game: Game; onUpload: (file: File) => void; onDelete: (id: string) => void }) {
  const [searching, setSearching] = useState(false);
  const [searched, setSearched] = useState(false);
  const [results, setResults] = useState<ResultadoManual[]>([]);

  const handleSearch = async () => {
    setSearching(true);
    setResults([]);
    try {
      setResults(await searchManuals(game.id));
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
      setSearched(true);
    }
  };

  return (
    <Card
      actions={(
        <DosButton disabled={searching} onClick={handleSearch} variant="ghost-small">
          {searching ? 'Buscando…' : 'Buscar manuales'}
        </DosButton>
      )}
      band="var(--accent)"
      number={10}
      title="Manual y revistas"
    >
      <div className={styles.stack} data-campo="manual">
        <div className={styles.busqueda}>
          <span className={styles.rotulo}>Manual en PDF</span>
          <OriginChip source="manual" status={game.manuals.length > 0 ? 'manual' : 'empty'} />
        </div>
        {game.manuals.length > 0 ? (
          <ul className={styles.lista}>
            {game.manuals.map((manual) => (
              <li className={styles.fila} key={manual.id}>
                <span className={styles.filaTexto}>
                  <span className={styles.nombre}>{manual.fileName}</span>
                  <span className={styles.meta}>{`${ESTADO_MANUAL[manual.status] ?? manual.status} — ${manual.pages} páginas`}</span>
                </span>
                <DosButton onClick={() => onDelete(manual.id)} variant="danger-small">Borrar</DosButton>
                {manual.status === 'processing' && manual.progress !== undefined ? (
                  <div className={styles.barra}><ProgressBar label={`Procesando ${manual.fileName}`} value={manual.progress} /></div>
                ) : null}
              </li>
            ))}
          </ul>
        ) : null}
        <Dropzone accept=".pdf,application/pdf" label="Soltá el manual en PDF acá" onFile={onUpload} />

        {searching ? (
          <div className={styles.busqueda}>
            <Spinner />
            <span className={styles.meta}>Buscando manuales digitales…</span>
          </div>
        ) : null}
        {results.length > 0 ? (
          <div className={styles.stack}>
            <span className={styles.rotulo}>Resultados de búsqueda</span>
            <ul className={styles.lista}>
              {results.map((result) => (
                <li className={styles.fila} key={result.url}>
                  <span className={styles.filaTexto}>
                    <span className={styles.nombre}>{result.title}</span>
                    <span className={styles.meta}>
                      {[result.source, result.pages ? `${result.pages} páginas` : '', tamano(result.sizeBytes)].filter(Boolean).join(' · ')}
                    </span>
                  </span>
                  <DosButton onClick={() => window.open(result.url, '_blank')} variant="ghost-small">Abrir</DosButton>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {searched && !searching && results.length === 0 ? <p className={styles.vacio}>La búsqueda no encontró manuales para este juego.</p> : null}
      </div>
    </Card>
  );
}
