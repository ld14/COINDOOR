import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { DosButton } from '@/components/dos';
import { useGames } from '@/hooks/useGames';
import { getGame } from '@/lib/api/games';
import { progresoDe } from './progreso';
import styles from '../Juegos.module.css';

const MAX_FALTANTES = 3;

/** Banda "Seguís con X": el primer juego en carga, sin importar los filtros de la pantalla. */
export function ContinueBand() {
  const navigate = useNavigate();
  const incompletos = useGames({ status: 'incomplete', perPage: 1 });
  const game = incompletos.data?.items[0];
  const detail = useQuery({ queryKey: ['game', game?.id], queryFn: () => getGame(game!.id), enabled: !!game, retry: false });
  if (!game) return null;

  const progreso = detail.data ? progresoDe(detail.data) : null;
  const faltantes = progreso?.faltantes ?? [];
  const visibles = faltantes.slice(0, MAX_FALTANTES).join(', ');
  const resto = faltantes.length - MAX_FALTANTES;

  return (
    <section aria-label="Juego en carga" className={styles.band}>
      <p className={styles.bandText}>
        Seguís con <strong>{game.title}</strong>
        {progreso ? ` · ${progreso.porcentaje}%` : ''}
        {visibles ? ` · faltan ${visibles}${resto > 0 ? ` y ${resto} más` : ''}` : ''}
      </p>
      <DosButton onClick={() => navigate(`/juegos/${game.id}`)} variant="primary">Continuar →</DosButton>
    </section>
  );
}
