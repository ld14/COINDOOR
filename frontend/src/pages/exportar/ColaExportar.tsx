import { useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Card, DosButton, ProgressBar, Spinner, StatusBadge } from '@/components/dos';
import { useGames } from '@/hooks/useGames';
import { createExport, getExportOptions } from '@/lib/api/export';
import type { GameSummary } from '@/lib/api/games';
import { esperarExport, opcionalesDisponibles } from './seleccion';
import styles from './Exportar.module.css';

type Avance = { estado: 'espera' | 'corriendo' | 'ok' | 'error'; detalle?: string };

/** `/exportar` sin id: los juegos sin exportar, separados en listos y en carga. */
export function ColaExportar() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useGames({ exportStatus: 'pending', perPage: 200 });
  const [avance, setAvance] = useState<Record<string, Avance>>({});
  const [corriendo, setCorriendo] = useState(false);
  const montado = useRef(true);
  useEffect(() => { montado.current = true; return () => { montado.current = false; }; }, []);

  const pendientes = data?.items ?? [];
  const listos = pendientes.filter((game) => game.status === 'ready' && avance[game.id]?.estado !== 'ok');
  const enCarga = pendientes.filter((game) => game.status !== 'ready');
  const hechos = Object.values(avance).filter((a) => a.estado === 'ok').length;
  const total = Object.keys(avance).length;

  async function exportarListos() {
    const lote = listos;
    setCorriendo(true);
    setAvance(Object.fromEntries(lote.map((game) => [game.id, { estado: 'espera' } as Avance])));
    // Uno por vez: el backend arma un bundle a la vez y la latencia no importa.
    for (const game of lote) {
      setAvance((prev) => ({ ...prev, [game.id]: { estado: 'corriendo' } }));
      try {
        const opciones = await getExportOptions(game.id);
        const job = await createExport(game.id, opcionalesDisponibles(opciones));
        await esperarExport(job.runId, undefined, 500, () => !montado.current);
        setAvance((prev) => ({ ...prev, [game.id]: { estado: 'ok' } }));
      } catch (err) {
        setAvance((prev) => ({ ...prev, [game.id]: { estado: 'error', detalle: err instanceof Error ? err.message : 'Error al exportar' } }));
      }
    }
    void queryClient.invalidateQueries({ queryKey: ['games'] });
    setCorriendo(false);
  }

  return (
    <div className={styles.page}>
      <div className={styles.head}>
        <h1>Exportar</h1>
        <p className={styles.sub}>Elegí un juego para ajustar el paquete, o exportá de una vez todos los que están listos.</p>
      </div>
      {isLoading ? <Spinner /> : null}
      {error ? <p className={styles.error} role="alert">No se pudo cargar la cola de exportación.</p> : null}
      {data ? (
        <div className={styles.main}>
          <Card
            actions={(
              <DosButton
                disabled={corriendo || listos.length === 0}
                disabledReason={listos.length === 0 ? 'No hay juegos listos para exportar.' : undefined}
                onClick={() => void exportarListos()}
                size="sm"
                variant="primary"
              >
                {corriendo ? 'Exportando…' : `Exportar los listos (${listos.length})`}
              </DosButton>
            )}
            band="var(--accent-3)"
            hint="completos y sin exportar"
            title="Listos"
          >
            {corriendo && total > 0 ? (
              <div aria-live="polite" className={styles.stack}>
                <ProgressBar label="Cola de exportación" value={(hechos / total) * 100} />
                <p className={styles.meta}>{hechos} de {total} exportados</p>
              </div>
            ) : null}
            <FilasCola avance={avance} juegos={listos} vacio="No hay juegos listos para exportar." />
          </Card>
          <Card band="var(--accent-2)" hint="faltan datos obligatorios" title="En carga">
            <FilasCola avance={avance} juegos={enCarga} vacio="No hay juegos en carga." />
          </Card>
        </div>
      ) : null}
    </div>
  );
}

function FilasCola({ avance, juegos, vacio }: { avance: Record<string, Avance>; juegos: GameSummary[]; vacio: string }) {
  if (juegos.length === 0) return <p className={styles.empty}>{vacio}</p>;
  return (
    <ul className={styles.queueList}>
      {juegos.map((game) => {
        const a = avance[game.id];
        return (
          <li className={styles.queueItem} key={game.id}>
            <Link to={`/exportar/${game.id}`}>{game.title}</Link>
            <span className={styles.queueMeta}>{game.systemName}</span>
            {a?.estado === 'error' ? <span className={styles.error} role="alert">{a.detalle}</span>
              : a?.estado === 'corriendo' ? <span className={styles.queueMeta}>Exportando…</span>
              : a?.estado === 'espera' ? <span className={styles.queueMeta}>En espera</span>
              : <StatusBadge status={game.status} />}
          </li>
        );
      })}
    </ul>
  );
}
