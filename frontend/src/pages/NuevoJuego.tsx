import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, DosButton, StepNav } from '@/components/dos';
import type { StepNavItem } from '@/components/dos';
import { useGameMutations } from '@/hooks/useGameMutations';
import { useRomCandidates } from '@/hooks/useRomCandidates';
import { useSystems } from '@/hooks/useSystems';
import { uploadRom, startPrecarga, startPrecargaMsdos } from '@/lib/api/games';
import type { RomCandidate } from '@/lib/api/roms';
import type { Identity, Tratamiento } from '@/lib/domain/types';
import { soportaArcadeDb, soportaMsdos, soportaPrecarga } from '@/lib/domain/arcade';
import { absolutePath, ABSOLUTE_PATH_MESSAGE } from '@/lib/domain/validation';
import { NuevoSistemaModal } from './nuevo/NuevoSistemaModal';
import { PasoArchivo, type ModoArchivo } from './nuevo/PasoArchivo';
import { PasoIdentidad } from './nuevo/PasoIdentidad';
import { PasoSistema } from './nuevo/PasoSistema';
import { ResumenAlta } from './nuevo/ResumenAlta';
import { detectarPorCarpeta, type Deteccion } from './nuevo/utils';
import styles from './nuevo/NuevoJuego.module.css';

const emptyIdentity: Identity = {
  title: '',
  year: '',
  developer: '',
  publisher: '',
  genre: '',
  players: '',
  format: '',
};

const PASOS = [
  { id: '1', label: 'Archivo' },
  { id: '2', label: 'Sistema y tratamiento' },
  { id: '3', label: 'Identidad' },
  { id: '4', label: 'Abrir la ficha' },
];

const TITULOS: Record<string, string> = {
  '1': 'Elegí el archivo',
  '2': 'Sistema y tratamiento',
  '3': 'Identidad',
  '4': 'Abrir la ficha',
};

export function NuevoJuego() {
  const navigate = useNavigate();
  const systems = useSystems();
  const candidates = useRomCandidates();
  const mutations = useGameMutations();
  const [paso, setPaso] = useState(1);
  const [maximo, setMaximo] = useState(1);
  const [modo, setModo] = useState<ModoArchivo>('instalados');
  const [systemId, setSystemId] = useState('');
  const [romRef, setRomRef] = useState('');
  const [romFile, setRomFile] = useState<File | null>(null);
  const [fileFormat, setFileFormat] = useState('');
  const [tratamiento, setTratamiento] = useState<Tratamiento>('copiar');
  const [identity, setIdentity] = useState(emptyIdentity);
  const [error, setError] = useState('');
  const [filtro, setFiltro] = useState('');
  const [elegido, setElegido] = useState('');
  const [deteccion, setDeteccion] = useState<Deteccion | null>(null);
  // Una vez que el usuario toca sistema o tratamiento, la ruta deja de reproponer.
  const [sistemaManual, setSistemaManual] = useState(false);
  const [precarga, setPrecarga] = useState(true);
  const [creando, setCreando] = useState(false);
  const [modalSistema, setModalSistema] = useState(false);

  const romSource = modo === 'upload' ? 'upload' : 'path';
  const sistemas = systems.data ?? [];

  // Esperar a que carguen los sistemas: fijar 'arcade' de arranque dejaba el alta
  // apuntando a un sistema que puede no existir en `sistemas.json`.
  useEffect(() => {
    if (!systemId && systems.data) setSystemId(systems.data[0]?.id ?? '');
  }, [systemId, systems.data]);

  function elegirCandidato(candidato: RomCandidate) {
    setElegido(candidato.id);
    setSystemId(candidato.systemId);
    setModo('instalados');
    setRomRef(candidato.path);
    setRomFile(null);
    setFileFormat(candidato.file_format);
    setTratamiento(candidato.tratamiento as Tratamiento);
    setDeteccion({ carpeta: candidato.systemId, systemId: candidato.systemId, tratamiento: candidato.tratamiento as Tratamiento });
    setSistemaManual(false);
    setIdentity((actual) => ({ ...actual, title: candidato.title }));
    setError('');
  }

  function cambiarModo(nuevo: ModoArchivo) {
    setModo(nuevo);
    if (nuevo === 'upload') {
      setDeteccion(null);
      setElegido('');
    }
    setError('');
  }

  function cambiarRuta(valor: string) {
    setRomRef(valor);
    setElegido('');
    if (sistemaManual) return;
    const propuesta = detectarPorCarpeta(valor, sistemas);
    setDeteccion(propuesta);
    if (propuesta) {
      setSystemId(propuesta.systemId);
      setTratamiento(propuesta.tratamiento);
    }
  }

  function elegirSistema(id: string) {
    setSystemId(id);
    setSistemaManual(true);
  }

  function elegirTratamiento(valor: Tratamiento) {
    setTratamiento(valor);
    setSistemaManual(true);
  }

  function validarArchivo(): string {
    if (romSource === 'path' && !absolutePath.safeParse(romRef).success) return ABSOLUTE_PATH_MESSAGE;
    if (romSource === 'upload' && !romFile) return 'Seleccioná un archivo para subir.';
    return '';
  }

  function ir(destino: number) {
    setPaso(destino);
    setMaximo((actual) => Math.max(actual, destino));
  }

  function siguiente() {
    if (paso === 1) {
      const problema = validarArchivo();
      if (problema) {
        setError(problema);
        return;
      }
    }
    if (paso === 2 && !systemId) {
      setError('Creá un sistema antes de cargar juegos.');
      return;
    }
    setError('');
    ir(paso + 1);
  }

  function seleccionarPaso(id: string) {
    const destino = Number(id);
    if (destino <= maximo) {
      setError('');
      setPaso(destino);
    }
  }

  async function submit() {
    if (!systemId) {
      setError('Creá un sistema antes de cargar juegos.');
      return;
    }
    const problema = validarArchivo();
    if (problema) {
      setError(problema);
      return;
    }
    try {
      setError('');
      setCreando(true);
      const ref = romSource === 'upload' ? romFile!.name : romRef;
      const game = await mutations.createGame.mutateAsync({ systemId, romSource, romRef: ref, file_format: fileFormat, tratamiento, identity });
      if (romSource === 'upload' && romFile) {
        await uploadRom(game.id, romFile);
      }
      // Precarga externa: ArcadeDB para romsets MAME, Launchbox+IA para MSDOS/PC.
      let precargaJobId = '';
      if (precarga && soportaPrecarga(systemId)) {
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
    } finally {
      setCreando(false);
    }
  }

  const items: StepNavItem[] = PASOS.map((p, index) => ({
    id: p.id,
    label: p.label,
    status: index + 1 < paso || (index + 1 <= maximo && index + 1 !== paso && index + 1 < 4) ? 'complete' : 'current',
  }));

  const nombreSistema = sistemas.find((s) => s.id === systemId)?.name ?? systemId;
  const archivo = romSource === 'upload' ? romFile?.name ?? '' : romRef;
  const precargaLabel = !soportaPrecarga(systemId)
    ? null
    : soportaArcadeDb(systemId) ? 'Precargar ArcadeDB al crear' : 'Precargar LaunchBox + IA al crear';

  return (
    <div className={styles.page}>
      <header>
        <h1 className={styles.title}>Alta de un juego</h1>
        <p className={styles.subtitle}>Se parte del archivo de ROM. Si el sistema lo reconoce, la identidad viene del catálogo; si no, se declara a mano.</p>
      </header>
      <StepNav activeId={String(paso)} aria-label="Pasos del alta" items={items} onSelect={seleccionarPaso} />
      <div className={styles.layout}>
        <Card number={paso} title={TITULOS[String(paso)]}>
          {paso === 1 ? (
            <PasoArchivo
              candidatos={candidates.data}
              cargando={candidates.isLoading}
              elegido={elegido}
              fallo={candidates.isError}
              filtro={filtro}
              modo={modo}
              onElegir={elegirCandidato}
              onFiltro={setFiltro}
              onModo={cambiarModo}
              onRomFile={(file) => {
                setRomFile(file);
                setRomRef(file?.name ?? '');
                setElegido('');
                setDeteccion(null);
              }}
              onRomRef={cambiarRuta}
              romFile={romFile}
              romRef={romRef}
            />
          ) : null}
          {paso === 2 ? (
            <PasoSistema
              cargando={systems.isLoading}
              deteccion={deteccion}
              onNuevoSistema={() => setModalSistema(true)}
              onSystem={elegirSistema}
              onTratamiento={elegirTratamiento}
              sistemas={sistemas}
              systemId={systemId}
              tratamiento={tratamiento}
            />
          ) : null}
          {paso === 3 ? <PasoIdentidad identity={identity} onChange={setIdentity} precargada={Boolean(identity.title)} /> : null}
          {paso === 4 ? (
            <p className={styles.hint}>
              Revisá el resumen de la derecha. Al crear la ficha se abre para seguir cargando; la precarga corre en segundo plano y no frena el alta.
            </p>
          ) : null}
          {error ? <p className={styles.error} role="alert">{error}</p> : null}
          <div className={styles.nav}>
            <DosButton disabled={paso === 1} onClick={() => { setError(''); setPaso(paso - 1); }} type="button" variant="ghost">← Atrás</DosButton>
            {paso < 4 ? <DosButton onClick={siguiente} type="button" variant="primary">Siguiente →</DosButton> : null}
          </div>
        </Card>
        <ResumenAlta
          archivo={archivo}
          creando={creando}
          onCrear={() => void submit()}
          onPrecarga={setPrecarga}
          precarga={precarga}
          precargaLabel={precargaLabel}
          sistema={nombreSistema}
          titulo={identity.title}
          tratamiento={tratamiento === 'copiar' ? 'Copiar (romset)' : 'Descomprimir (archivos sueltos)'}
        />
      </div>
      <NuevoSistemaModal
        onClose={() => setModalSistema(false)}
        onCreated={(system) => {
          setSystemId(system.id);
          setSistemaManual(true);
          setModalSistema(false);
        }}
        open={modalSistema}
      />
    </div>
  );
}
