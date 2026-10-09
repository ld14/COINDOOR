import { forwardRef, useImperativeHandle, useState } from 'react';
import { Card, DosInput, DosSelect } from '@/components/dos';
import type { Game, Tratamiento } from '@/lib/domain/types';
import type { SaveHandle } from './types';
import styles from './ficha.module.css';

interface ArchivoPanelProps {
  game: Game;
  onSaveTratamiento: (tratamiento: string) => void;
  onSaveRomRef: (romRef: string) => void;
  onUploadRom: (file: File) => void;
}

/**
 * «Archivo del juego» (columna lateral): tratamiento (copiar/descomprimir), archivo adjunto y ruta.
 * Es una sección más para el autosave: `data-seccion="archivo"` y `save()` que solo escribe lo que cambió.
 */
export const ArchivoPanel = forwardRef<SaveHandle, ArchivoPanelProps>(function ArchivoPanel({ game, onSaveTratamiento, onSaveRomRef, onUploadRom }, ref) {
  const guardado = (game.tratamiento || 'copiar') as Tratamiento;
  const [tratamiento, setTratamiento] = useState<Tratamiento>(guardado);
  const [romPath, setRomPath] = useState(game.romRef || '');
  const [romFile, setRomFile] = useState<File | null>(null);

  const nombre = romFile?.name || (game.romRef ? game.romRef.split(/[\\/]/).pop() || game.romRef : '');

  useImperativeHandle(ref, () => ({
    save: () => {
      if (tratamiento !== guardado) onSaveTratamiento(tratamiento);
      if (romFile) {
        onUploadRom(romFile);
        setRomFile(null);
      } else if (romPath !== game.romRef) {
        onSaveRomRef(romPath);
      }
    },
  }), [tratamiento, guardado, romFile, romPath, game.romRef, onSaveTratamiento, onSaveRomRef, onUploadRom]);

  return (
    <Card band="var(--accent-3)" title="Archivo del juego">
      <div className={styles.stack}>
        <label className={styles.campo}>
          <span className={styles.etiqueta}>Tratamiento</span>
          <DosSelect aria-label="Tratamiento" onChange={(e) => setTratamiento(e.target.value as Tratamiento)} value={tratamiento}>
            <option value="copiar">Copiar (romset)</option>
            <option value="descomprimir">Descomprimir (archivos sueltos)</option>
          </DosSelect>
        </label>
        <div className={styles.campo}>
          <span className={styles.etiqueta}>Archivo del juego</span>
          {nombre ? <span className={styles.archivoNombre}>{nombre}</span> : <span className={styles.meta}>No adjunto</span>}
          <label className={styles.adjuntar}>
            <input
              accept=".zip,.nes,.sms,.gb,.gbc,.gba,.gen,.smc,.sfc,.pce,.ngp,.ngpc,.col,.sg"
              className={styles.archivoInput}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) setRomFile(file);
              }}
              type="file"
            />
            <span className={styles.adjuntarBoton}>⇄ Adjuntar archivo</span>
          </label>
          <DosInput
            aria-label="Path del ROM"
            data-autosave="blur"
            onChange={(e) => setRomPath(e.target.value)}
            placeholder="O ingresar path del archivo..."
            value={romPath}
          />
        </div>
      </div>
    </Card>
  );
});
