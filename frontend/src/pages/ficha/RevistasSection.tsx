import { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Card, DosButton, OriginChip, Spinner } from '@/components/dos';
import type { Game } from '@/lib/domain/types';
import { searchMagazines, setMagazine, addAppearance, removeAppearance, buildMagazineLinks, type MagazineSearchResult } from '@/lib/api/magazines';
import styles from './manual.module.css';

/*
 * Revistas según D3: solo se buscan y se VINCULAN como referencia interna. Nunca se descargan,
 * no se exportan y no hay estado «roto» ni «faltante»: sin referencias es un estado normal.
 */
export function MagazineSection({ game }: { game: Game }) {
  const queryClient = useQueryClient();
  const [searching, setSearching] = useState(false);
  const [searched, setSearched] = useState(false);
  const [results, setResults] = useState<MagazineSearchResult[]>([]);

  const refrescar = () => queryClient.invalidateQueries({ queryKey: ['game', game.id] });

  const handleSearch = async () => {
    setSearching(true);
    setResults([]);
    try {
      setResults(await searchMagazines(game.id));
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
      setSearched(true);
    }
  };

  const handleVincular = async (result: MagazineSearchResult) => {
    if (!result.appearance) return;
    try {
      await addAppearance(game.id, result.appearance);
      // Ya vinculada: sale de los resultados para no duplicar la referencia.
      setResults((prev) => prev.filter((item) => item !== result));
      await refrescar();
    } catch {
      // Queda en los resultados para reintentar.
    }
  };

  const handleRemoveAppearance = async (appearanceId: string) => {
    try {
      await removeAppearance(game.id, appearanceId);
      await refrescar();
    } catch {
      // La referencia sigue en la lista.
    }
  };

  const appearances = game.magazineAppearances || [];

  return (
    <Card
      actions={(
        <DosButton disabled={searching} onClick={handleSearch} variant="ghost-small">
          {searching ? 'Buscando…' : 'Buscar con IA'}
        </DosButton>
      )}
      band="var(--accent-3)"
      className={styles.separador}
      hint="Referencia interna: no se descarga ni se exporta"
      title="Revistas"
    >
      <div className={styles.stack} data-campo="magazine">
        <div className={styles.busqueda}>
          <span className={styles.rotulo}>Apariciones en revistas</span>
          <OriginChip source="manual" status={appearances.length > 0 || game.magazine === 'linked' ? 'manual' : 'empty'} />
        </div>
        {game.magazine === 'linked' ? (
          <div className={styles.fila}>
            <span className={styles.filaTexto}><span className={styles.nombre}>{game.magazineName}</span></span>
            <DosButton onClick={async () => { await setMagazine(game.id, ''); await refrescar(); }} variant="danger-small">Desvincular</DosButton>
          </div>
        ) : null}
        {appearances.length > 0 ? (
          <ul className={styles.lista}>
            {appearances.map((a) => {
              const links = buildMagazineLinks(a);
              return (
                <li className={styles.fila} key={a.id}>
                  <span className={styles.filaTexto}>
                    <span className={styles.nombre}>{a.magazineName}</span>
                    <span className={styles.meta}>
                      {[a.issueNumber ? `N° ${a.issueNumber}` : '', a.date, a.contentType, a.appearanceType].filter(Boolean).join(' · ')}
                    </span>
                  </span>
                  <span className={styles.acciones}>
                    {links.archiveOrg ? <DosButton onClick={() => window.open(links.archiveOrg, '_blank')} variant="ghost-small">Archive.org</DosButton> : null}
                    {links.retroCdn ? <DosButton onClick={() => window.open(links.retroCdn, '_blank')} variant="ghost-small">Retro CDN</DosButton> : null}
                    <DosButton onClick={() => handleRemoveAppearance(a.id)} variant="danger-small">Eliminar</DosButton>
                  </span>
                </li>
              );
            })}
          </ul>
        ) : (
          <p className={styles.vacio}>
            Sin cobertura en revistas guardada. «Buscar con IA» propone en qué revistas salió el juego; al vincular una queda solo como referencia interna, no se descarga ni va en el bundle.
          </p>
        )}

        {searching ? (
          <div className={styles.busqueda}>
            <Spinner />
            <span className={styles.meta}>Identificando apariciones en revistas…</span>
          </div>
        ) : null}
        {results.length > 0 ? (
          <div className={styles.stack}>
            <span className={styles.rotulo}>Resultados</span>
            <ul className={styles.lista}>
              {results.map((result, idx) => (
                <li className={styles.fila} key={result.url || idx}>
                  <span className={styles.filaTexto}>
                    <span className={styles.nombre}>{result.title}</span>
                    <span className={styles.meta}>{result.magazine}</span>
                  </span>
                  <span className={styles.acciones}>
                    {result.url ? <DosButton onClick={() => window.open(result.url, '_blank')} variant="ghost-small">Abrir</DosButton> : null}
                    {result.links?.archiveOrg ? <DosButton onClick={() => window.open(result.links!.archiveOrg, '_blank')} variant="ghost-small">Archive.org</DosButton> : null}
                    {result.links?.retroCdn ? <DosButton onClick={() => window.open(result.links!.retroCdn, '_blank')} variant="ghost-small">Retro CDN</DosButton> : null}
                    {result.appearance ? <DosButton onClick={() => handleVincular(result)} variant="primary-small">Vincular</DosButton> : null}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {searched && !searching && results.length === 0 ? <p className={styles.meta}>La búsqueda no devolvió revistas para este juego.</p> : null}
      </div>
    </Card>
  );
}
