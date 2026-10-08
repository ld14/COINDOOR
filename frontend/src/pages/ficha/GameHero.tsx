import { useState } from 'react';
import { Link } from 'react-router-dom';
import { DosButton, DosInput, DosSelect, Panel, StatusBadge, SunkenBox } from '@/components/dos';
import { useDominantColors } from '@/hooks/useDominantColors';
import type { computeGameStatus } from '@/lib/domain/completeness';
import type { Game, System, Tratamiento } from '@/lib/domain/types';
import type { AccentSlot } from './types';
import styles from '../ReadPages.module.css';

export function GameHero({ game, systems, missing, onSaveAll, onSystemChange, onMarkReady, onSaveTratamiento, onSaveRomRef, onUploadRom, onExport, onPickColor, proximoAcento, status }: { game: Game; systems: System[]; missing: string[]; onSaveAll: () => void; onSystemChange: (systemId: string) => void; onMarkReady: () => void; onSaveTratamiento: (tratamiento: string) => void; onSaveRomRef: (romRef: string) => void; onUploadRom: (file: File) => void; onExport: () => void; onPickColor: (hex: string) => void; proximoAcento: AccentSlot; status: ReturnType<typeof computeGameStatus> }) {
  const coverUrl = game.images.caratula?.url;
  const heroMedia = coverUrl ?? game.video.video?.url;
  const { colors } = useDominantColors(coverUrl, 4);
  const [tratamiento, setTratamiento] = useState(game.tratamiento || 'copiar');
  const [romPath, setRomPath] = useState(game.romRef || '');
  const [romFile, setRomFile] = useState<File | null>(null);

  const romFileName = romFile?.name || (game.romRef ? game.romRef.split('/').pop() || game.romRef : '');

  const handleSaveTratamiento = () => {
    onSaveTratamiento(tratamiento);
    if (romFile) {
      onUploadRom(romFile);
    } else if (romPath !== game.romRef) {
      onSaveRomRef(romPath);
    }
  };

  return (
    <div className={styles.gameHero}>
      <div className={styles.heroPreview}>
        {heroMedia ? <img alt={game.identity.title} className={styles.previewImage} src={heroMedia} /> : `${game.identity.title} · carátula pendiente`}
      </div>
      <div className={styles.heroRight}>
        <Link className={styles.backLink} to="/juegos">&lt;&lt; Juegos</Link>
        <h1 className={styles.title}>{game.identity.title}</h1>
        <Panel className={styles.heroPanel}>
          <SunkenBox className={styles.heroFields}>
            <DosSelect
              aria-label="Plataforma"
              className={styles.systemSelect}
              value={game.systemId}
              onChange={(e) => onSystemChange(e.target.value)}
            >
              {systems.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </DosSelect>
            <StatusBadge status={status} />
            {colors.length > 0 ? (
              <div className={styles.colorPalette}>
                <span className={styles.paletteLabel}>
                  Colores predominantes
                  <span className={styles.paletteHint}> — clic: acento {proximoAcento === 0 ? 'primario' : 'secundario'}</span>
                </span>
                <div className={styles.swatches}>
                  {colors.map((color) => (
                    <button
                      aria-label={`Usar ${color.hex} como acento ${proximoAcento === 0 ? 'primario' : 'secundario'}`}
                      className={styles.colorSwatch}
                      key={color.hex}
                      onClick={() => onPickColor(color.hex)}
                      type="button"
                    >
                      <span className={styles.colorBlock} style={{ backgroundColor: color.hex }} />
                      <span className={styles.colorHex}>{color.hex}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
            <div className={styles.tratamientoField}>
              <span className={styles.label}>Tratamiento</span>
              <div className={styles.tratamientoRow}>
                <DosSelect aria-label="Tratamiento" className={styles.tratamientoSelect} value={tratamiento} onChange={(e) => setTratamiento(e.target.value as Tratamiento)}>
                  <option value="copiar">Copiar (romset)</option>
                  <option value="descomprimir">Descomprimir (archivos sueltos)</option>
                </DosSelect>
              </div>
            </div>
            <div className={styles.tratamientoField}>
              <span className={styles.label}>Archivo del juego</span>
              {romFileName ? (
                <div className={styles.romInfo}>
                  <span className={styles.romName}>{romFileName}</span>
                </div>
              ) : (
                <span className={styles.empty}>No adjunto</span>
              )}
              <div className={styles.tratamientoRow}>
                <label className={styles.romUpload}>
                  <input
                    type="file"
                    accept=".zip,.nes,.sms,.gb,.gbc,.gba,.gen,.smc,.sfc,.pce,.ngp,.ngpc,.col,.sg"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) setRomFile(file);
                    }}
                  />
                  <span className={styles.romUploadBtn}>Adjuntar archivo</span>
                </label>
              </div>
              <div className={styles.tratamientoRow}>
                <DosInput
                  aria-label="Path del ROM"
                  className={styles.romPathInput}
                  placeholder="O ingresar path del archivo..."
                  value={romPath}
                  onChange={(e) => setRomPath(e.target.value)}
                />
              </div>
            </div>
          </SunkenBox>
          <div className={styles.heroToolbar}>
            <DosButton onClick={handleSaveTratamiento} variant="primary-small">Guardar</DosButton>
            <DosButton onClick={onSaveAll} variant="ghost-small">Guardar todo</DosButton>
            <DosButton onClick={onMarkReady} variant="ghost-small">Marcar como listo</DosButton>
          </div>
          {status === 'ready' ? (
            <div className={styles.heroToolbar}>
              <DosButton onClick={onExport} variant="ghost-small" className={styles.heroExport}>Exportar</DosButton>
            </div>
          ) : null}
        </Panel>
      </div>
    </div>
  );
}
