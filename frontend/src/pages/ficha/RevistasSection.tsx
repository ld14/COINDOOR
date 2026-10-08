import { useState } from 'react';
import { DosButton, Panel, SectionHeader, Spinner, SunkenBox } from '@/components/dos';
import type { Game } from '@/lib/domain/types';
import { searchMagazines, setMagazine, addAppearance, removeAppearance, buildMagazineLinks, type MagazineSearchResult } from '@/lib/api/magazines';
import styles from '../ReadPages.module.css';

export function MagazineSection({ game }: { game: Game }) {
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<MagazineSearchResult[]>([]);

  const handleSearch = async () => {
    setSearching(true);
    setResults([]);
    try {
      const data = await searchMagazines(game.id);
      setResults(data);
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleAddAppearance = async (result: MagazineSearchResult) => {
    if (!result.appearance) return;
    await addAppearance(game.id, result.appearance);
    window.location.reload();
  };

  const handleRemoveAppearance = async (appearanceId: string) => {
    await removeAppearance(game.id, appearanceId);
    window.location.reload();
  };

  const appearances = game.magazineAppearances || [];

  return (
    <Panel>
      <SectionHeader>REVISTA</SectionHeader>
      <SunkenBox className={styles.stack}>
        {game.magazine === 'linked' ? (
          <div className={styles.cheatEntry}>
            <span className={styles.name}>{game.magazineName}</span>
            <DosButton onClick={() => { setMagazine(game.id, ''); window.location.reload(); }} variant="danger-small">Desvincular</DosButton>
          </div>
        ) : null}
        {appearances.length > 0 ? (
          <div className={styles.stack}>
            <span className={styles.name}>Apariciones en revistas:</span>
            {appearances.map((a) => {
              const links = buildMagazineLinks(a);
              return (
                <div className={styles.cheatEntry} key={a.id}>
                  <span className={styles.name}>{a.magazineName}</span>
                  {a.issueNumber ? <span className={styles.meta}>N° {a.issueNumber}</span> : null}
                  {a.date ? <span className={styles.meta}>{a.date}</span> : null}
                  <span className={styles.meta}>{a.contentType}</span>
                  <span className={styles.meta}>{a.appearanceType}</span>
                  {links.archiveOrg ? (
                    <DosButton onClick={() => window.open(links.archiveOrg, '_blank')} variant="ghost-small">Archive.org</DosButton>
                  ) : null}
                  {links.retroCdn ? (
                    <DosButton onClick={() => window.open(links.retroCdn, '_blank')} variant="ghost-small">Retro CDN</DosButton>
                  ) : null}
                  <DosButton onClick={() => handleRemoveAppearance(a.id)} variant="danger-small">Eliminar</DosButton>
                </div>
              );
            })}
          </div>
        ) : <p className={styles.empty}>Sin cobertura en revistas</p>}
        <div className={styles.toolbar}>
          <DosButton disabled={searching} onClick={handleSearch} variant="ghost-small">
            {searching ? 'Buscando…' : 'Buscar revistas'}
          </DosButton>
        </div>
        {searching ? (
          <div className={styles.toolbar}>
            <Spinner />
            <span className={styles.meta}>Identificando apariciones en revistas…</span>
          </div>
        ) : null}
        {results.length > 0 ? (
          <div className={styles.stack}>
            <span className={styles.name}>Resultados:</span>
            {results.map((result, idx) => (
              <div className={styles.cheatEntry} key={result.url || idx}>
                <span>{result.title}</span>
                <span className={styles.meta}>{result.magazine}</span>
                {result.url ? (
                  <DosButton onClick={() => window.open(result.url, '_blank')} variant="ghost-small">Abrir</DosButton>
                ) : null}
                {result.links?.archiveOrg ? (
                  <DosButton onClick={() => window.open(result.links!.archiveOrg, '_blank')} variant="ghost-small">Archive.org</DosButton>
                ) : null}
                {result.links?.retroCdn ? (
                  <DosButton onClick={() => window.open(result.links!.retroCdn, '_blank')} variant="ghost-small">Retro CDN</DosButton>
                ) : null}
                {result.appearance ? (
                  <DosButton onClick={() => handleAddAppearance(result)} variant="ghost-small">Agregar</DosButton>
                ) : null}
              </div>
            ))}
          </div>
        ) : null}
      </SunkenBox>
    </Panel>
  );
}
