import { Card, Spinner } from '@/components/dos';
import { useSystems } from '@/hooks/useSystems';
import { NewSystemCard } from './sistemas/NewSystemCard';
import { SystemCard } from './sistemas/SystemCard';
import styles from './sistemas/sistemas.module.css';

export function Sistemas() {
  const { data, error, isLoading } = useSystems();

  return (
    <div className={styles.page}>
      <header className={styles.head}>
        <h1>Sistemas / Plataformas</h1>
        <p className={styles.sub}>Cada juego pertenece a un sistema. El comando de lanzamiento tiene que ser una ruta absoluta.</p>
      </header>

      {isLoading ? <Spinner /> : null}
      {error ? <p className={styles.error}>No se pudieron cargar los sistemas.</p> : null}

      <div className={styles.grid}>
        {(data ?? []).map((system) => <SystemCard key={system.id} system={system} />)}
        <NewSystemCard />
      </div>

      {!isLoading && data?.length === 0 ? (
        <Card><p className={styles.empty}>No hay sistemas cargados.</p></Card>
      ) : null}
    </div>
  );
}
