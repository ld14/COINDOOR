import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DosButton, DosInput, DosSelect, Panel, SectionHeader, SunkenBox } from '@/components/dos';
import { useGameMutations } from '@/hooks/useGameMutations';
import { useSystems } from '@/hooks/useSystems';
import type { Identity, RomSource } from '@/lib/domain/types';
import { absolutePath, ABSOLUTE_PATH_MESSAGE } from '@/lib/domain/validation';
import styles from './ReadPages.module.css';

const emptyIdentity: Identity = {
  title: '',
  year: '',
  developer: '',
  publisher: '',
  genre: '',
  players: '',
  format: '',
};

export function NuevoJuego() {
  const navigate = useNavigate();
  const systems = useSystems();
  const mutations = useGameMutations();
  const [systemId, setSystemId] = useState('');
  const [romSource, setRomSource] = useState<RomSource>('path');
  const [romRef, setRomRef] = useState('');
  const [identity, setIdentity] = useState(emptyIdentity);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!systemId) setSystemId(systems.data?.[0]?.id ?? 'arcade');
  }, [systemId, systems.data]);

  async function submit() {
    if (!systemId) {
      setError('Creá un sistema antes de cargar juegos.');
      return;
    }
    if (romSource === 'path' && !absolutePath.safeParse(romRef).success) {
      setError(ABSOLUTE_PATH_MESSAGE);
      return;
    }
    try {
      setError('');
      const game = await mutations.createGame.mutateAsync({ systemId, romSource, romRef, identity });
      navigate(`/juegos/${game.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo crear la ficha.');
    }
  }

  return (
    <div className={styles.page}>
      <header>
        <h1 className={styles.title}>Alta de un juego</h1>
        <p className={styles.subtitle}>Se parte del archivo de ROM. Si el sistema lo reconoce, la identidad viene del catálogo; si no, se declara a mano.</p>
      </header>
      <Panel>
        <SectionHeader>ORIGEN</SectionHeader>
        <SunkenBox className={styles.stack}>
          <label className={styles.field}>
            <span className={styles.label}>Sistema</span>
            <DosSelect aria-label="Sistema" onChange={(event) => setSystemId(event.target.value)} value={systemId}>
              <option value="">{systems.isLoading ? 'Cargando sistemas…' : 'Seleccionar sistema'}</option>
              {(systems.data ?? []).map((system) => <option key={system.id} value={system.id}>{system.name}</option>)}
            </DosSelect>
          </label>
          <label className={styles.field}>
            <span className={styles.label}>Origen del archivo</span>
            <DosSelect aria-label="Origen del archivo" onChange={(event) => setRomSource(event.target.value as RomSource)} value={romSource}>
              <option value="path">Indicar ruta (juegos pesados)</option>
              <option value="upload">Subir ROM</option>
            </DosSelect>
          </label>
          <label className={styles.field}>
            <span className={styles.label}>ROM</span>
            <DosInput aria-label="ROM" onChange={(event) => setRomRef(event.target.value)} placeholder="/roms/arcade/sf2.zip" value={romRef} />
          </label>
          {error ? <p className={styles.error}>{error}</p> : null}
        </SunkenBox>
      </Panel>
      <Panel>
        <SectionHeader>IDENTIDAD</SectionHeader>
        <SunkenBox className={styles.fields}>
          {Object.keys(emptyIdentity).map((key) => (
            <label className={styles.field} key={key}>
              <span className={styles.label}>{key}</span>
              <DosInput aria-label={key} onChange={(event) => setIdentity({ ...identity, [key]: event.target.value })} value={identity[key as keyof Identity]} />
            </label>
          ))}
        </SunkenBox>
        <DosButton onClick={() => void submit()} variant="primary">Crear ficha</DosButton>
      </Panel>
    </div>
  );
}
