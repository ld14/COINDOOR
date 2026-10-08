import { useState } from 'react';
import { DosButton, Panel, SectionHeader, Spinner, SunkenBox } from '@/components/dos';
import type { Game } from '@/lib/domain/types';
import { searchManuals, type ManualSearchResult } from '@/lib/api/manuals';
import styles from '../ReadPages.module.css';

export function ManualSection({ game, onUpload, onDelete }: { game: Game; onUpload: (file: File) => void; onDelete: (id: string) => void }) {
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<ManualSearchResult[]>([]);

  const handleSearch = async () => {
    setSearching(true);
    setResults([]);
    try {
      const data = await searchManuals(game.id);
      setResults(data);
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  return (
    <Panel>
      <SectionHeader>MANUAL</SectionHeader>
      <SunkenBox className={styles.stack}>
        {game.manuals.length > 0 ? (
          <div className={styles.cheatLedger}>
            {game.manuals.map((manual) => (
              <div className={styles.cheatEntry} key={manual.id}>
                <span>📎 {manual.fileName}</span>
                <span className={styles.meta}>{manual.status} — {manual.pages} páginas</span>
                <DosButton onClick={() => onDelete(manual.id)} variant="danger-small">Borrar</DosButton>
              </div>
            ))}
          </div>
        ) : <p className={styles.empty}>No Disponible</p>}
        <div className={styles.toolbar}>
          <label className={styles.meta}>
            Cargar PDF:
            <input
              multiple
              accept=".pdf"
              onChange={(event) => {
                const files = event.target.files;
                if (files) Array.from(files).forEach((file) => onUpload(file));
              }}
              type="file"
            />
          </label>
          <DosButton disabled={searching} onClick={handleSearch} variant="ghost-small">
            {searching ? 'Buscando…' : 'Buscar manuales'}
          </DosButton>
        </div>
        {searching ? (
          <div className={styles.toolbar}>
            <Spinner />
            <span className={styles.meta}>Buscando manuales digitales…</span>
          </div>
        ) : null}
        {results.length > 0 ? (
          <div className={styles.stack}>
            <span className={styles.name}>Resultados de búsqueda:</span>
            {results.map((result) => (
              <div className={styles.cheatEntry} key={result.url}>
                <span>{result.title}</span>
                <span className={styles.meta}>{result.source}</span>
                <DosButton onClick={() => window.open(result.url, '_blank')} variant="ghost-small">Abrir</DosButton>
              </div>
            ))}
          </div>
        ) : null}
      </SunkenBox>
    </Panel>
  );
}
