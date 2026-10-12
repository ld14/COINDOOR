import type { MouseEvent } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import { DosButton, ProgressBar, StatusBadge } from '@/components/dos';
import type { GameStatus as BadgeStatus } from '@/components/dos';
import { getGame } from '@/lib/api/games';
import type { GameSummary } from '@/lib/api/games';
import { colorDeTitulo, iniciales, progresoDe } from './progreso';
import styles from '../Juegos.module.css';

export type VistaJuegos = 'grilla' | 'lista';

export function badgeDe(game: GameSummary): BadgeStatus {
  if (game.status === 'error') return 'error';
  return game.exportStatus === 'exported' ? 'exported' : game.status;
}

/** Nota bajo la barra y avance; solo pide la ficha completa cuando algo falta o falla. */
export function useResumenJuego(game: GameSummary) {
  const badge = badgeDe(game);
  const needsDetail = badge === 'incomplete' || badge === 'error';
  const detail = useQuery({ queryKey: ['game', game.id], queryFn: () => getGame(game.id), enabled: needsDetail, retry: false });
  const progreso = needsDetail && detail.data ? progresoDe(detail.data) : null;
  let nota: string;
  let porcentaje: number;
  if (badge === 'exported') { nota = 'Exportado'; porcentaje = 100; }
  else if (badge === 'ready') { nota = 'Pendiente de exportar'; porcentaje = 100; }
  else if (!progreso) { nota = detail.isError ? 'Sin datos de avance' : 'Calculando avance…'; porcentaje = 0; }
  else if (badge === 'error') { nota = 'Hay errores para corregir'; porcentaje = progreso.porcentaje; }
  else { nota = `Faltan ${progreso.faltan} obligatorios`; porcentaje = progreso.porcentaje; }
  return { badge, nota, porcentaje };
}

function accion(game: GameSummary, badge: BadgeStatus) {
  if (badge === 'ready') return { label: 'Exportar', to: `/exportar/${game.id}`, variant: 'primary' as const };
  if (badge === 'exported') return { label: 'Abrir', to: `/juegos/${game.id}`, variant: 'secondary' as const };
  return { label: 'Seguir cargando', to: `/juegos/${game.id}`, variant: 'secondary' as const };
}

function Caratula({ game, className }: { game: GameSummary; className: string }) {
  if (game.coverThumbUrl) return <img alt="" className={className} src={game.coverThumbUrl} />;
  return <span aria-hidden="true" className={`${className} ${styles.initials}`} style={{ background: colorDeTitulo(game.title) }}>{iniciales(game.title)}</span>;
}

export function GameCard({ game, vista }: { game: GameSummary; vista: VistaJuegos }) {
  const navigate = useNavigate();
  const { badge, nota, porcentaje } = useResumenJuego(game);
  const act = accion(game, badge);
  const meta = `${game.systemName} · ${game.year || 'Sin Información'}`;
  const barState = badge === 'error' ? 'error' : porcentaje === 100 ? 'ok' : 'active';
  const detalle = `/juegos/${game.id}`;
  // Toda la tarjeta abre la ficha (también si está lista o exportada); los enlaces y botones siguen con su acción.
  const abrir = (event: MouseEvent<HTMLLIElement>) => {
    if ((event.target as HTMLElement).closest('a, button')) return;
    navigate(detalle);
  };
  const action = (
    <DosButton onClick={() => navigate(act.to)} size="sm" variant={act.variant}>{act.label}</DosButton>
  );

  if (vista === 'lista') {
    return (
      <li className={`${styles.row} ${styles.clicable}`} onClick={abrir}>
        <Caratula className={styles.rowThumb} game={game} />
        <span className={styles.rowText}>
          <Link className={styles.gameTitle} to={`/juegos/${game.id}`}>{game.title}</Link>
          <span className={styles.meta}>{meta} · {game.identitySource}</span>
          <span className={styles.note}>{nota}</span>
        </span>
        <span className={styles.rowProgress}><ProgressBar label={`Avance de ${game.title}`} state={barState} value={porcentaje} /></span>
        <StatusBadge status={badge} />
        {action}
      </li>
    );
  }

  return (
    <li className={`${styles.card} ${styles.clicable}`} onClick={abrir}>
      <div className={styles.cover}>
        <Caratula className={styles.coverFill} game={game} />
        <span className={styles.coverBadge}><StatusBadge status={badge} /></span>
      </div>
      <div className={styles.cardBody}>
        <Link className={styles.gameTitle} to={`/juegos/${game.id}`}>{game.title}</Link>
        <span className={styles.meta}>{meta.toUpperCase()}</span>
        <ProgressBar label={`Avance de ${game.title}`} state={barState} value={porcentaje} />
        <span className={styles.note}>{nota}</span>
        {action}
      </div>
    </li>
  );
}
