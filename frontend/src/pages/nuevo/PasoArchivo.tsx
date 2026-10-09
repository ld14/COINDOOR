import { useMemo } from 'react';
import { DosFileInput, DosInput, SegmentedControl } from '@/components/dos';
import type { RomCandidate } from '@/lib/api/roms';
import type { RomSource } from '@/lib/domain/types';
import { tamano } from './utils';
import styles from './NuevoJuego.module.css';

export type ModoArchivo = 'instalados' | RomSource;

interface Props {
  modo: ModoArchivo;
  onModo: (modo: ModoArchivo) => void;
  candidatos: RomCandidate[] | undefined;
  cargando: boolean;
  fallo: boolean;
  filtro: string;
  onFiltro: (valor: string) => void;
  elegido: string;
  onElegir: (candidato: RomCandidate) => void;
  romRef: string;
  onRomRef: (valor: string) => void;
  romFile: File | null;
  onRomFile: (file: File | null) => void;
}

export function PasoArchivo({ modo, onModo, candidatos, cargando, fallo, filtro, onFiltro, elegido, onElegir, romRef, onRomRef, romFile, onRomFile }: Props) {
  const visibles = useMemo(() => {
    const needle = filtro.trim().toLowerCase();
    // Un mismo ROM no puede aparecer dos veces aunque el listado lo repita.
    const vistos = new Set<string>();
    return (candidatos ?? []).filter((item) => {
      const clave = `${item.systemId}/${item.name}`;
      if (vistos.has(clave)) return false;
      vistos.add(clave);
      return !needle || `${item.title} ${item.name} ${item.systemId}`.toLowerCase().includes(needle);
    });
  }, [candidatos, filtro]);

  return (
    <div className={styles.stack}>
      <SegmentedControl
        ariaLabel="Origen del archivo"
        onChange={(valor) => onModo(valor as ModoArchivo)}
        options={[
          { value: 'instalados', label: 'Instalados' },
          { value: 'path', label: 'Indicar ruta' },
          { value: 'upload', label: 'Subir ROM' },
        ]}
        value={modo}
      />
      {modo === 'instalados' ? (
        <>
          <p className={styles.hint}>Lo que está en games/juegos/ y todavía no tiene ficha. Elegí uno y se precarga el alta.</p>
          <label className={styles.field}>
            <span className={styles.label}>Filtrar</span>
            <DosInput aria-label="Filtrar instalados" onChange={(event) => onFiltro(event.target.value)} placeholder="sf2, mario, mame…" value={filtro} />
          </label>
          {cargando ? <p className={styles.hint}>Buscando juegos instalados…</p> : null}
          {fallo ? <p className={styles.error}>No se pudo leer la carpeta de juegos.</p> : null}
          {!cargando && !fallo && visibles.length === 0 ? <p className={styles.hint}>No Disponible</p> : null}
          {visibles.length > 0 ? (
            <div className={styles.romGrid}>
              {visibles.map((candidato) => (
                <button
                  aria-pressed={elegido === candidato.id}
                  className={[styles.romCard, elegido === candidato.id ? styles.romSelected : ''].filter(Boolean).join(' ')}
                  key={`${candidato.systemId}/${candidato.name}`}
                  onClick={() => onElegir(candidato)}
                  type="button"
                >
                  <span className={styles.romType}>{candidato.kind === 'dir' ? 'DIR' : 'ZIP'}</span>
                  <span className={styles.romName}>{candidato.title}</span>
                  <span className={styles.romMeta}>
                    {candidato.systemId} · {candidato.kind === 'dir' ? 'carpeta' : candidato.file_format || 'archivo'}
                    {tamano(candidato.sizeBytes) ? ` · ${tamano(candidato.sizeBytes)}` : ''}
                  </span>
                  <span className={styles.romPath}>{candidato.path}</span>
                </button>
              ))}
            </div>
          ) : null}
        </>
      ) : null}
      {modo === 'path' ? (
        <label className={styles.field}>
          <span className={styles.label}>Ruta del ROM (juegos pesados)</span>
          <DosInput aria-label="ROM" className={styles.mono} onChange={(event) => onRomRef(event.target.value)} placeholder="/roms/arcade/sf2.zip" value={romRef} />
        </label>
      ) : null}
      {modo === 'upload' ? (
        <label className={styles.field}>
          <span className={styles.label}>Archivo ROM</span>
          <DosFileInput
            accept=".zip,.nes,.sms,.gb,.gbc,.gba,.gen,.smc,.sfc,.ngp,.pce,.col,.rom,.bin"
            ariaLabel="ROM"
            fileName={romFile?.name}
            onChange={onRomFile}
          />
        </label>
      ) : null}
    </div>
  );
}
