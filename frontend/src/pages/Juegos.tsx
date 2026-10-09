import { useQueries } from '@tanstack/react-query';
import { useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { DosButton, DosInput, DosSelect, FilterChips, FilterTabs, SegmentedControl } from '@/components/dos';
import type { FilterChipItem, FilterTabItem } from '@/components/dos';
import { useGames } from '@/hooks/useGames';
import { useRomCandidates } from '@/hooks/useRomCandidates';
import { useSystems } from '@/hooks/useSystems';
import { listGames, type GameSummary } from '@/lib/api/games';
import type { GameStatus } from '@/lib/domain/types';
import { ContinueBand } from './juegos/ContinueBand';
import { GameCard, type VistaJuegos } from './juegos/GameCard';
import styles from './Juegos.module.css';

type TabId = 'todos' | 'carga' | 'listos' | 'exportados' | 'errores';
type Orden = '' | 'titulo' | 'sistema';

interface TabFilter { status: GameStatus | ''; exportStatus: 'pending' | 'exported' | '' }

const tabFilters: Record<TabId, TabFilter> = {
  todos: { status: '', exportStatus: '' },
  carga: { status: 'incomplete', exportStatus: '' },
  listos: { status: 'ready', exportStatus: 'pending' },
  exportados: { status: '', exportStatus: 'exported' },
  errores: { status: 'error', exportStatus: '' },
};

const tabLabels: [TabId, string][] = [
  ['todos', 'Todos'],
  ['carga', 'En carga'],
  ['listos', 'Listos sin exportar'],
  ['exportados', 'Exportados'],
  ['errores', 'Con errores'],
];

function tabActiva(status: string, exportStatus: string): TabId {
  if (exportStatus === 'exported') return 'exportados';
  if (exportStatus === 'pending') return 'listos';
  if (status === 'error') return 'errores';
  if (status === 'incomplete') return 'carga';
  return 'todos';
}

const ordenOptions: { value: Orden; label: string }[] = [
  { value: '', label: 'Orden: por defecto' },
  { value: 'titulo', label: 'Título A–Z (esta página)' },
  { value: 'sistema', label: 'Sistema (esta página)' },
];

const vistaOptions = [
  { value: 'grilla', label: '▦ Grilla' },
  { value: 'lista', label: '☰ Lista' },
];

function ordenar(items: GameSummary[], orden: Orden): GameSummary[] {
  if (!orden) return items;
  const key = (game: GameSummary) => (orden === 'titulo' ? game.title : `${game.systemName} ${game.title}`);
  return [...items].sort((a, b) => key(a).localeCompare(key(b), 'es'));
}

export function Juegos() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const q = params.get('q') ?? '';
  const systemId = params.get('systemId') ?? '';
  const status = (params.get('status') ?? '') as GameStatus | '';
  const rawPage = Number(params.get('page') ?? '1');
  const page = Number.isInteger(rawPage) && rawPage > 0 ? rawPage : 1;
  const rawExportStatus = params.get('exportStatus');
  const exportStatus: TabFilter['exportStatus'] = rawExportStatus === 'pending' || rawExportStatus === 'exported' ? rawExportStatus : '';
  const rawOrden = params.get('orden');
  const orden: Orden = rawOrden === 'titulo' || rawOrden === 'sistema' ? rawOrden : '';
  const vista: VistaJuegos = params.get('vista') === 'lista' ? 'lista' : 'grilla';
  const tab = tabActiva(status, exportStatus);

  const games = useGames({ q, systemId, status, exportStatus, page, perPage: 50 });
  const systems = useSystems();
  const roms = useRomCandidates();
  const totalFichas = useGames({ perPage: 1 });
  const paraExportar = useGames({ status: 'ready', exportStatus: 'pending', perPage: 1 });

  // Contadores de las pestañas (respetan búsqueda y sistema) y de los chips (respetan la búsqueda).
  const tabCounts = useQueries({
    queries: tabLabels.map(([id]) => {
      const query = { q, systemId, ...tabFilters[id], perPage: 1 };
      return { queryKey: ['games', query], queryFn: () => listGames(query) };
    }),
  });
  const systemList = useMemo(() => systems.data ?? [], [systems.data]);
  const systemCounts = useQueries({
    queries: systemList.map((system) => {
      const query = { q, systemId: system.id, status, exportStatus, perPage: 1 };
      return { queryKey: ['games', query], queryFn: () => listGames(query) };
    }),
  });

  const tabItems: FilterTabItem[] = tabLabels.map(([id, label], index) => ({ id, label, count: tabCounts[index]?.data?.total }));
  const chipItems: FilterChipItem[] = systemList.map((system, index) => ({ id: system.id, label: system.name, count: systemCounts[index]?.data?.total }));

  function update(key: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    next.delete('page');
    setParams(next);
  }

  function selectTab(id: string) {
    const filter = tabFilters[id as TabId];
    const next = new URLSearchParams(params);
    for (const [key, value] of Object.entries(filter)) {
      if (value) next.set(key, value);
      else next.delete(key);
    }
    next.delete('page');
    setParams(next);
  }

  function goToPage(nextPage: number) {
    const next = new URLSearchParams(params);
    next.set('page', String(nextPage));
    setParams(next);
  }

  const sinFicha = roms.data?.length;
  const subtitulo = [
    totalFichas.data ? `${totalFichas.data.total} fichas` : null,
    paraExportar.data ? `${paraExportar.data.total} para exportar` : null,
    sinFicha !== undefined ? `${sinFicha} ROMs instalados sin ficha` : null,
  ].filter(Boolean).join(' · ');
  const items = ordenar(games.data?.items ?? [], orden);

  return (
    <div className={styles.page}>
      <header className={styles.head}>
        <div>
          <h1 className={styles.title}>Juegos</h1>
          {subtitulo ? <p className={styles.sub}>{subtitulo}</p> : null}
        </div>
        <div className={styles.headActions}>
          {sinFicha ? <DosButton onClick={() => navigate('/juegos/nuevo')} variant="secondary">Ver {sinFicha} ROMs sin ficha</DosButton> : null}
          <DosButton onClick={() => navigate('/juegos/nuevo')} variant="primary">+ Nuevo juego</DosButton>
        </div>
      </header>

      <FilterTabs aria-label="Filtrar por estado" items={tabItems} onChange={selectTab} value={tab} />

      <div className={styles.toolbar}>
        <DosInput aria-label="Buscar juego" className={styles.search} onChange={(event) => update('q', event.target.value)} placeholder="Buscar" value={q} />
        <FilterChips aria-label="Sistema" items={chipItems} mode="single" onChange={(value) => update('systemId', value[0] ?? '')} value={systemId ? [systemId] : []} />
        <DosSelect aria-label="Ordenar" onChange={(event) => update('orden', event.target.value)} value={orden}>
          {ordenOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </DosSelect>
        <SegmentedControl ariaLabel="Vista" onChange={(value) => update('vista', value === 'lista' ? 'lista' : '')} options={vistaOptions} value={vista} />
      </div>

      <ContinueBand />

      {games.error ? <p className={styles.error}>No se pudieron cargar los juegos.</p> : null}
      {items.length > 0 ? (
        <ul aria-label="Juegos" className={vista === 'lista' ? styles.list : styles.grid}>
          {items.map((game) => <GameCard game={game} key={game.id} vista={vista} />)}
        </ul>
      ) : null}
      {!games.isLoading && games.data?.items.length === 0 ? (
        <p className={styles.empty}>Ningún juego coincide con la búsqueda o los filtros.</p>
      ) : null}

      {games.data ? (
        <nav aria-label="Páginas de juegos" className={styles.pager}>
          <DosButton disabled={page <= 1 || games.isFetching} onClick={() => goToPage(page - 1)}>Anterior</DosButton>
          <span aria-live="polite">{games.data.total} juegos · Página {page} de {Math.max(1, Math.ceil(games.data.total / games.data.perPage))}</span>
          <DosButton disabled={page * games.data.perPage >= games.data.total || games.isFetching} onClick={() => goToPage(page + 1)}>Siguiente</DosButton>
        </nav>
      ) : null}
    </div>
  );
}
