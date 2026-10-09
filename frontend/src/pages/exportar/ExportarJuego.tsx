import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Card, CheckTile, DosButton, ProgressBar, Spinner } from '@/components/dos';
import { useConfig } from '@/hooks/useConfig';
import { useGame } from '@/hooks/useGame';
import {
  createExport,
  getExportOptions,
  installAttract,
  type ExportOptions,
  type ExportResult,
  type InstallResult,
} from '@/lib/api/export';
import {
  GRUPOS,
  esperarExport,
  etapaDe,
  formatBytes,
  grupoDe,
  motivoNoDisponible,
  resumen,
  seleccionInicial,
  todas,
  type Etapa,
} from './seleccion';
import styles from './Exportar.module.css';

type Destino = 'attract' | 'zip';

const ETAPAS: { id: Etapa; texto: string }[] = [
  { id: 'armando', texto: 'Armando' },
  { id: 'verificando', texto: 'Verificando' },
  { id: 'resultado', texto: 'Resultado' },
];

export function ExportarJuego({ gameId }: { gameId: string }) {
  const queryClient = useQueryClient();
  const { data: game } = useGame(gameId);
  const { data: config } = useConfig();
  const attractDir = config?.attractDir ?? null;

  const [options, setOptions] = useState<ExportOptions | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [destinoElegido, setDestino] = useState<Destino | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState(0);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<ExportResult | null>(null);
  const [installing, setInstalling] = useState(false);
  const [installResult, setInstallResult] = useState<InstallResult | null>(null);
  const [installError, setInstallError] = useState('');
  const instaladoAuto = useRef(false);
  const montado = useRef(true);
  useEffect(() => { montado.current = true; return () => { montado.current = false; }; }, []);

  const destino: Destino = destinoElegido ?? (attractDir ? 'attract' : 'zip');

  useEffect(() => {
    let vigente = true;
    setLoading(true);
    setError('');
    getExportOptions(gameId)
      .then((data) => {
        if (!vigente) return;
        setOptions(data);
        setSelected(seleccionInicial(data));
      })
      .catch((err) => { if (vigente) setError(err instanceof Error ? err.message : 'Error al cargar opciones'); })
      .finally(() => { if (vigente) setLoading(false); });
    return () => { vigente = false; };
  }, [gameId]);

  const items = useMemo(() => (options ? todas(options) : []), [options]);
  const total = useMemo(() => resumen(items, selected), [items, selected]);

  const toggle = useCallback((key: string, checked: boolean) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (checked) next.add(key); else next.delete(key);
      return next;
    });
  }, []);

  const quitarOMarcar = useCallback((claves: string[], marcar: boolean) => {
    setSelected((prev) => {
      const next = new Set(prev);
      claves.forEach((key) => { if (marcar) next.add(key); else next.delete(key); });
      return next;
    });
  }, []);

  const instalar = useCallback(async () => {
    setInstalling(true);
    setInstallError('');
    setInstallResult(null);
    try {
      setInstallResult(await installAttract(gameId));
    } catch (err) {
      setInstallError(err instanceof Error ? err.message : 'Error al instalar en ATTRACT');
    } finally {
      setInstalling(false);
    }
  }, [gameId]);

  async function exportar() {
    setError('');
    setProgress(0);
    setRunning(true);
    instaladoAuto.current = false;
    try {
      const job = await createExport(gameId, Array.from(selected));
      const res = await esperarExport(job.runId, setProgress, 500, () => !montado.current);
      void queryClient.invalidateQueries({ queryKey: ['games'] });
      if (montado.current) setResult(res);
    } catch (err) {
      // Un rechazo (ATTRACT doctor, juego incompleto) no deja .zip: se vuelve a la selección.
      if (montado.current) setError(err instanceof Error ? err.message : 'Error al iniciar export');
    } finally {
      if (montado.current) setRunning(false);
    }
  }

  useEffect(() => {
    if (!result || destino !== 'attract' || instaladoAuto.current) return;
    instaladoAuto.current = true;
    void instalar();
  }, [result, destino, instalar]);

  const titulo = game?.identity.title ?? gameId;

  if (result) {
    return (
      <div className={styles.page}>
        <div className={styles.head}><h1>Exportar {titulo}</h1></div>
        <Card band="var(--ok)" title="Resultado">
          <div className={styles.stack} aria-live="polite">
            <p className={styles.ok}>Export completado</p>
            <p className={styles.meta}>Archivo: <span className={styles.mono}>{result.file}</span></p>
            <p className={styles.meta}>Tamaño: <span className={styles.mono}>{(result.bytes / 1024).toFixed(1)} KB</span></p>
            <p className={styles.meta}>Contenido: {result.incluye.join(', ')}</p>
            <div className={styles.toolbar}>
              <Link to="/juegos"><DosButton variant="primary-small">Volver a Juegos</DosButton></Link>
              <Link to="/exportar"><DosButton variant="ghost-small">Exportar otro</DosButton></Link>
              <DosButton disabled={installing} onClick={() => void instalar()} variant="ghost-small">
                {installing ? 'Instalando…' : 'Cargar en ATTRACT'}
              </DosButton>
            </div>
            {installing ? <Spinner /> : null}
            {installResult ? <p className={styles.ok}>Instalado en ATTRACT.</p> : null}
            {installError ? <p className={styles.error} role="alert">{installError}</p> : null}
          </div>
        </Card>
      </div>
    );
  }

  if (running) {
    const etapa = etapaDe(progress);
    const actual = ETAPAS.findIndex((e) => e.id === etapa);
    return (
      <div className={styles.page}>
        <div className={styles.head}><h1>Exportar {titulo}</h1></div>
        <Card band="var(--accent)" title="En progreso">
          <div aria-live="polite" className={styles.stack}>
            <Spinner />
            <ol className={styles.stages}>
              {ETAPAS.map((e, i) => (
                <li
                  aria-current={i === actual ? 'step' : undefined}
                  className={[styles.stage, i < actual ? styles.stageDone : '', i === actual ? styles.stageNow : ''].filter(Boolean).join(' ')}
                  key={e.id}
                >
                  {i < actual ? '✓ ' : ''}{e.texto}
                </li>
              ))}
            </ol>
            <ProgressBar label="Progreso del export" value={progress} />
            <p className={styles.meta}>{progress}% completado</p>
          </div>
        </Card>
      </div>
    );
  }

  const sinSeleccion = selected.size === 0;
  // El backend todavía no expone la fecha del último export; si aparece en la ficha, se muestra.
  const exportadoEl = (game as { exportedAt?: string } | undefined)?.exportedAt;

  return (
    <div className={styles.page}>
      <div className={styles.head}>
        <h1>Exportar {titulo}</h1>
        <p className={styles.sub}>Elegí qué viaja en el paquete y adónde va.</p>
      </div>
      {loading ? <Spinner /> : null}
      {error ? <p className={styles.error} role="alert">{error}</p> : null}
      {options ? (
        <div className={styles.cols}>
          <div className={styles.main}>
            {GRUPOS.map((grupo) => {
              const delGrupo = items.filter((o) => grupoDe(o) === grupo.id);
              if (delGrupo.length === 0) return null;
              const r = resumen(delGrupo, selected);
              const quitables = delGrupo.filter((o) => !o.required && o.disponible).map((o) => o.key);
              const hayTildados = quitables.some((key) => selected.has(key));
              const conteo = `${r.elegidos} de ${r.total} · ${formatBytes(r.bytes)}`;
              return (
                <Card
                  actions={quitables.length > 0 ? (
                    <DosButton onClick={() => quitarOMarcar(quitables, !hayTildados)} size="sm" variant="secondary">
                      {hayTildados ? 'Quitar todo' : 'Marcar todo'}
                    </DosButton>
                  ) : undefined}
                  band={grupo.banda}
                  hint={grupo.ayuda ? `${grupo.ayuda} · ${conteo}` : conteo}
                  key={grupo.id}
                  title={grupo.titulo}
                >
                  <ul className={styles.tiles}>
                    {delGrupo.map((opt) => {
                      const disponible = opt.disponible;
                      const bloqueado = opt.required || !disponible;
                      return (
                        <li key={opt.key}>
                          <CheckTile
                            checked={opt.required ? true : selected.has(opt.key)}
                            disabled={bloqueado}
                            disabledReason={!disponible ? motivoNoDisponible(opt) : undefined}
                            label={opt.label}
                            meta={<span className={styles.size}>{formatBytes(opt.bytes)}</span>}
                            onChange={(checked) => toggle(opt.key, checked)}
                          />
                        </li>
                      );
                    })}
                  </ul>
                </Card>
              );
            })}
          </div>

          <aside className={styles.side}>
            <Card className={styles.pack}>
              <h3>Paquete</h3>
              <div aria-live="polite" className={styles.total}>
                <strong>{formatBytes(total.bytes)}</strong>
                <span>{total.elegidos} {total.elegidos === 1 ? 'elemento' : 'elementos'}</span>
              </div>
              <fieldset className={styles.dest}>
                <legend>Destino</legend>
                <label className={[styles.destOption, destino === 'attract' ? styles.destOn : '', !attractDir ? styles.destOff : ''].filter(Boolean).join(' ')}>
                  <input
                    checked={destino === 'attract'}
                    disabled={!attractDir}
                    name="destino"
                    onChange={() => setDestino('attract')}
                    type="radio"
                  />
                  <span className={styles.destText}>
                    <b>Cargar en ATTRACT</b>
                    <small>{attractDir ? `${attractDir} ✓` : 'falta configurar la ruta'}</small>
                  </span>
                </label>
                <label className={[styles.destOption, destino === 'zip' ? styles.destOn : ''].filter(Boolean).join(' ')}>
                  <input checked={destino === 'zip'} name="destino" onChange={() => setDestino('zip')} type="radio" />
                  <span className={styles.destText}>
                    <b>Descargar .zip</b>
                    <small>para copiar a mano</small>
                  </span>
                </label>
              </fieldset>
              <DosButton
                disabled={sinSeleccion}
                disabledReason={sinSeleccion ? 'No hay nada seleccionado.' : undefined}
                onClick={() => void exportar()}
                variant="primary"
              >
                {destino === 'attract' ? '⇪ Exportar a ATTRACT' : '⇪ Generar .zip'}
              </DosButton>
              {exportadoEl ? (
                <p className={styles.note}>Exportado por última vez el {formatFecha(exportadoEl)}. Se reemplaza esa versión.</p>
              ) : null}
            </Card>
          </aside>
        </div>
      ) : null}
    </div>
  );
}

function formatFecha(iso: string): string {
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return iso;
  return `${String(fecha.getDate()).padStart(2, '0')}/${String(fecha.getMonth() + 1).padStart(2, '0')}`;
}
