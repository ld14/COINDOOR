import { useSearchParams, useNavigate } from 'react-router-dom';
import { DosButton, DosInput, DosSelect, Panel, StatusBadge, SunkenBox } from '@/components/dos';
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

const exportOptions = [
  { value: '', label: 'Todos' },
  { value: 'pending', label: 'Pendientes de exportar' },
  { value: 'exported', label: 'Exportados' },
] as const;

export function Juegos() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const q = params.get('q') ?? '';
  const systemId = params.get('systemId') ?? '';
  const status = (params.get('status') ?? '') as GameStatus | '';
  const rawPage = Number(params.get('page') ?? '1');
  const page = Number.isInteger(rawPage) && rawPage > 0 ? rawPage : 1;
  const rawExportStatus = params.get('exportStatus');
  const exportStatus = rawExportStatus === 'pending' || rawExportStatus === 'exported' ? rawExportStatus : '';
  const games = useGames({ q, systemId, status, exportStatus, page, perPage: 50 });
  const systems = useSystems();

  function update(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    next.delete('page');
    setParams(next);
  }

  function goToPage(nextPage: number) {
    const next = new URLSearchParams(params);
    next.set('page', String(nextPage));
    setParams(next);
  }

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.title}>Juegos</h1>
      </div>
      <div aria-label="Filtrar por exportación" className={styles.filters} role="group">
        {exportOptions.map((option) => (
          <DosButton aria-pressed={exportStatus === option.value} key={option.value} onClick={() => update('exportStatus', option.value)} pressed={exportStatus === option.value}>
            {option.label}
          </DosButton>
        ))}
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
                <span className={styles.exportState}>{game.exportStatus === 'exported' ? 'Exportado' : 'Pendiente de exportar'}</span>
              </span>
              <StatusBadge status={game.status} />
            </button>
          ))}
          {!games.isLoading && games.data?.items.length === 0 ? (
            <p className={styles.empty}>Ningún juego coincide con la búsqueda o los filtros.</p>
          ) : null}
        </SunkenBox>
      </Panel>
      {games.data ? (
        <nav aria-label="Páginas de juegos" className={styles.filters}>
          <DosButton disabled={page <= 1 || games.isFetching} onClick={() => goToPage(page - 1)}>Anterior</DosButton>
          <span aria-live="polite">{games.data.total} juegos · Página {page} de {Math.max(1, Math.ceil(games.data.total / games.data.perPage))}</span>
          <DosButton disabled={page * games.data.perPage >= games.data.total || games.isFetching} onClick={() => goToPage(page + 1)}>Siguiente</DosButton>
        </nav>
      ) : null}
    </div>
  );
}

function initials(title: string) {
  return title.split(' ').map((part) => part[0]).join('').slice(0, 3).toUpperCase();
}
