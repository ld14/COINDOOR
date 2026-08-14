import { useSearchParams, useNavigate } from 'react-router-dom';
import { DosInput, DosSelect, Panel, StatusBadge, SunkenBox } from '@/components/dos';
import { useGames } from '@/hooks/useGames';
import { useSystems } from '@/hooks/useSystems';
import type { GameStatus } from '@/lib/domain/types';
import styles from './ReadPages.module.css';

const statusOptions: { value: GameStatus | ''; label: string }[] = [
  { value: '', label: 'Todos los estados' },
  { value: 'ready', label: 'Listo' },
  { value: 'incomplete', label: 'Incompleto' },
  { value: 'error', label: 'Con errores' },
];

export function Juegos() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const q = params.get('q') ?? '';
  const systemId = params.get('systemId') ?? '';
  const status = (params.get('status') ?? '') as GameStatus | '';
  const page = Number(params.get('page') ?? '1');
  const games = useGames({ q, systemId, status, page, perPage: 50 });
  const systems = useSystems();

  function update(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    next.delete('page');
    setParams(next);
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Juegos</h1>
      </div>
      <div className={styles.filters}>
        <DosInput aria-label="Buscar juego" onChange={(event) => update('q', event.target.value)} placeholder="Buscar" value={q} />
        <DosSelect aria-label="Sistema" onChange={(event) => update('systemId', event.target.value)} value={systemId}>
          <option value="">Todos los sistemas</option>
          {(systems.data ?? []).map((system) => <option key={system.id} value={system.id}>{system.name}</option>)}
        </DosSelect>
        <DosSelect aria-label="Estado" onChange={(event) => update('status', event.target.value)} value={status}>
          {statusOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </DosSelect>
      </div>

      {games.error ? <p className={styles.error}>No se pudieron cargar los juegos.</p> : null}
      <Panel>
        <SunkenBox className={styles.list}>
          {(games.data?.items ?? []).map((game) => (
            <button className={styles.gameRow} key={game.id} onClick={() => navigate(`/juegos/${game.id}`)} type="button">
              {game.coverThumbUrl ? <img alt="" className={styles.thumbImage} src={game.coverThumbUrl} /> : <span className={styles.thumb}>{initials(game.title)}</span>}
              <span>
                <span className={styles.rowMain}><span className={styles.gameTitle}>{game.title}</span></span>
                <span className={styles.meta}>{game.systemName} · {game.year || 'Sin Información'} · {game.identitySource}</span>
              </span>
              <StatusBadge status={game.status} />
            </button>
          ))}
          {!games.isLoading && games.data?.items.length === 0 ? (
            <p className={styles.empty}>Ningún juego coincide con la búsqueda o los filtros.</p>
          ) : null}
        </SunkenBox>
      </Panel>
    </div>
  );
}

function initials(title: string) {
  return title.split(' ').map((part) => part[0]).join('').slice(0, 3).toUpperCase();
}
