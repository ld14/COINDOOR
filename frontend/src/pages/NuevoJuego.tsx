import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DosButton, DosFileInput, DosInput, DosSelect, Panel, SectionHeader, SunkenBox } from '@/components/dos';
import { useGameMutations } from '@/hooks/useGameMutations';
import { useRomCandidates } from '@/hooks/useRomCandidates';
import { useSystems } from '@/hooks/useSystems';
import { uploadRom, startPrecarga, startPrecargaMsdos } from '@/lib/api/games';
import type { RomCandidate } from '@/lib/api/roms';
import type { Identity, RomSource, Tratamiento } from '@/lib/domain/types';
import { soportaMsdos, soportaPrecarga } from '@/lib/domain/arcade';
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

const UNIDADES = ['B', 'KB', 'MB', 'GB'];

function tamano(bytes: number): string {
  if (bytes <= 0) return '';
  let valor = bytes;
  let unidad = 0;
  while (valor >= 1024 && unidad < UNIDADES.length - 1) {
    valor /= 1024;
    unidad += 1;
  }
  const redondeado = valor < 10 && unidad > 0 ? valor.toFixed(1) : String(Math.round(valor));
  return `${redondeado} ${UNIDADES[unidad]}`;
}

export function NuevoJuego() {
  const navigate = useNavigate();
  const systems = useSystems();
  const candidates = useRomCandidates();
  const mutations = useGameMutations();
  const [systemId, setSystemId] = useState('');
  const [romSource, setRomSource] = useState<RomSource>('path');
  const [romRef, setRomRef] = useState('');
  const [romFile, setRomFile] = useState<File | null>(null);
  const [fileFormat, setFileFormat] = useState('');
  const [tratamiento, setTratamiento] = useState<Tratamiento>('copiar');
  const [identity, setIdentity] = useState(emptyIdentity);
  const [error, setError] = useState('');
  const [filtro, setFiltro] = useState('');
  const [elegido, setElegido] = useState('');

  // Esperar a que carguen los sistemas: fijar 'arcade' de arranque dejaba el alta
  // apuntando a un sistema que puede no existir en `sistemas.json`.
  useEffect(() => {
    if (!systemId && systems.data) setSystemId(systems.data[0]?.id ?? '');
  }, [systemId, systems.data]);

  const visibles = useMemo(() => {
    const needle = filtro.trim().toLowerCase();
    const items = candidates.data ?? [];
    if (!needle) return items;
    return items.filter((item) => `${item.title} ${item.name} ${item.systemId}`.toLowerCase().includes(needle));
  }, [candidates.data, filtro]);

  // El sistema de un candidato puede no estar en `sistemas.json` (carpeta huérfana):
  // sin esta opción el selector quedaría en blanco y el alta se iría a un sistema
  // que el usuario no eligió.
  const systemIds = (systems.data ?? []).map((system) => system.id);
  const sistemaDesconocido = Boolean(systemId) && systemIds.length > 0 && !systemIds.includes(systemId);

  function elegirCandidato(candidato: RomCandidate) {
    setElegido(candidato.id);
    setSystemId(candidato.systemId);
    setRomSource('path');
    setRomRef(candidato.path);
    setRomFile(null);
    setFileFormat(candidato.file_format);
    setTratamiento(candidato.tratamiento as Tratamiento);
    setIdentity((actual) => ({ ...actual, title: candidato.title }));
    setError('');
  }

  async function submit() {
    if (!systemId) {
      setError('Creá un sistema antes de cargar juegos.');
      return;
    }
    if (romSource === 'path' && !absolutePath.safeParse(romRef).success) {
      setError(ABSOLUTE_PATH_MESSAGE);
      return;
    }
    if (romSource === 'upload' && !romFile) {
      setError('Seleccioná un archivo para subir.');
      return;
    }
    try {
      setError('');
      const ref = romSource === 'upload' ? romFile!.name : romRef;
      const game = await mutations.createGame.mutateAsync({ systemId, romSource, romRef: ref, file_format: fileFormat, tratamiento, identity });
      if (romSource === 'upload' && romFile) {
        await uploadRom(game.id, romFile);
      }
      // Precarga externa: ArcadeDB para romsets MAME, Launchbox+IA para MSDOS/PC.
      let precargaJobId = '';
      if (soportaPrecarga(systemId)) {
        try {
          const result = soportaMsdos(systemId) ? await startPrecargaMsdos(game.id) : await startPrecarga(game.id);
          precargaJobId = result.jobId;
        } catch {
          // La precarga es best-effort: si falla, el juego se creó igual.
        }
      }
      const query = precargaJobId ? `?precarga=${precargaJobId}` : '';
      navigate(`/juegos/${game.id}${query}`);
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
        <SectionHeader>INSTALADOS SIN FICHA</SectionHeader>
        <SunkenBox className={styles.stack}>
          <p className={styles.subtitle}>Lo que está en games/juegos/ y todavía no tiene metadata. Elegí uno y se precarga el alta.</p>
          <label className={styles.field}>
            <span className={styles.label}>Filtrar</span>
            <DosInput aria-label="Filtrar instalados" onChange={(event) => setFiltro(event.target.value)} placeholder="sf2, mario, mame…" value={filtro} />
          </label>
          {candidates.isLoading ? <p className={styles.subtitle}>Buscando juegos instalados…</p> : null}
          {candidates.isError ? <p className={styles.error}>No se pudo leer la carpeta de juegos.</p> : null}
          {!candidates.isLoading && !candidates.isError && visibles.length === 0 ? (
            <p className={styles.subtitle}>No Disponible</p>
          ) : null}
          {visibles.length > 0 ? (
            <div className={styles.candidatesScroll}>
              {visibles.map((candidato) => (
                <button
                  className={elegido === candidato.id ? `${styles.candidateRow} ${styles.candidateSelected}` : styles.candidateRow}
                  key={`${candidato.systemId}/${candidato.name}`}
                  onClick={() => elegirCandidato(candidato)}
                  type="button"
                >
                  <span className={styles.candidateName}>{candidato.title}</span>
                  <span className={styles.candidateTag}>
                    {candidato.systemId} · {candidato.kind === 'dir' ? 'carpeta' : candidato.file_format || 'archivo'}
                    {tamano(candidato.sizeBytes) ? ` · ${tamano(candidato.sizeBytes)}` : ''}
                  </span>
                  <span className={styles.candidatePath}>{candidato.path}</span>
                </button>
              ))}
            </div>
          ) : null}
        </SunkenBox>
      </Panel>
      <Panel>
        <SectionHeader>ORIGEN</SectionHeader>
        <SunkenBox className={styles.stack}>
          <label className={styles.field}>
            <span className={styles.label}>Sistema</span>
            <DosSelect aria-label="Sistema" onChange={(event) => setSystemId(event.target.value)} value={systemId}>
              <option value="">{systems.isLoading ? 'Cargando sistemas…' : 'Seleccionar sistema'}</option>
              {(systems.data ?? []).map((system) => <option key={system.id} value={system.id}>{system.name}</option>)}
              {sistemaDesconocido ? <option value={systemId}>{systemId} (sin sistema declarado)</option> : null}
            </DosSelect>
          </label>
          <label className={styles.field}>
            <span className={styles.label}>Origen del archivo</span>
            <DosSelect aria-label="Origen del archivo" onChange={(event) => setRomSource(event.target.value as RomSource)} value={romSource}>
              <option value="path">Indicar ruta (juegos pesados)</option>
              <option value="upload">Subir ROM</option>
            </DosSelect>
          </label>
          {romSource === 'path' ? (
            <label className={styles.field}>
              <span className={styles.label}>ROM</span>
              <DosInput aria-label="ROM" onChange={(event) => setRomRef(event.target.value)} placeholder="/roms/arcade/sf2.zip" value={romRef} />
            </label>
          ) : (
            <label className={styles.field}>
              <span className={styles.label}>ROM</span>
              <DosFileInput
                accept=".zip,.nes,.sms,.gb,.gbc,.gba,.gen,.smc,.sfc,.ngp,.pce,.col,.rom,.bin"
                ariaLabel="ROM"
                fileName={romFile?.name}
                onChange={(file) => {
                  setRomFile(file);
                  setRomRef(file?.name ?? '');
                }}
              />
            </label>
          )}
          <label className={styles.field}>
            <span className={styles.label}>Tratamiento</span>
            <DosSelect aria-label="Tratamiento" onChange={(event) => setTratamiento(event.target.value as Tratamiento)} value={tratamiento}>
              <option value="copiar">Copiar (romset)</option>
              <option value="descomprimir">Descomprimir (archivos sueltos)</option>
            </DosSelect>
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
