import { Panel, SectionHeader, SunkenBox } from '@/components/dos';
import type { Game } from '@/lib/domain/types';
import styles from '../ReadPages.module.css';

export function CabinetSection({ game }: { game: Game }) {
  const cabinet = game.cabinet;
  const hasData = cabinet?.resolution || cabinet?.orientation || cabinet?.controls;

  return (
    <Panel>
      <SectionHeader>GABINETE</SectionHeader>
      <SunkenBox className={styles.stack}>
        {hasData ? (
          <>
            <div className={styles.fieldTop}>
              <span className={styles.name}>Especificaciones</span>
            </div>
            <div className={styles.cheatLedger}>
              {cabinet?.resolution ? (
                <div className={styles.cheatEntry}>
                  <span>Resolución</span>
                  <span className={styles.meta}>{cabinet.resolution}</span>
                </div>
              ) : null}
              {cabinet?.orientation ? (
                <div className={styles.cheatEntry}>
                  <span>Orientación</span>
                  <span className={styles.meta}>{cabinet.orientation}</span>
                </div>
              ) : null}
              {cabinet?.controls ? (
                <div className={styles.cheatEntry}>
                  <span>Controles</span>
                  <span className={styles.meta}>{cabinet.controls}</span>
                </div>
              ) : null}
              {cabinet?.buttons ? (
                <div className={styles.cheatEntry}>
                  <span>Botones</span>
                  <span className={styles.meta}>{cabinet.buttons}</span>
                </div>
              ) : null}
            </div>
            {cabinet?.button_list.length ? (
              <>
                <div className={styles.fieldTop}>
                  <span className={styles.name}>Mapa de botones</span>
                </div>
                <div className={styles.cheatLedger}>
                  {cabinet.button_list.map((btn, idx) => (
                    <div className={styles.cheatEntry} key={`${btn.control}-${idx}`}>
                      <span>{btn.action}</span>
                      <code>{btn.control}</code>
                      <span className={styles.meta}>{btn.color}</span>
                    </div>
                  ))}
                </div>
              </>
            ) : null}
          </>
        ) : (
          <p className={styles.empty}>Sin Información</p>
        )}
        <p className={styles.meta}>
          Fuente: Arcade Database (motoschifo) — adb.arcadeitalia.net · Historia (C) arcade-history.com
        </p>
      </SunkenBox>
    </Panel>
  );
}
