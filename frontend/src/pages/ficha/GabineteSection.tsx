import { Card } from '@/components/dos';
import type { Game } from '@/lib/domain/types';
import styles from './gabinete.module.css';

/** Gabinete (columna lateral, solo lectura): especificaciones y mapa de botones del juego arcade. */
export function CabinetSection({ game }: { game: Game }) {
  const cabinet = game.cabinet;
  const specs = [
    ['Resolución', cabinet?.resolution],
    ['Orientación', cabinet?.orientation],
    ['Controles', cabinet?.controls],
    ['Botones', cabinet?.buttons ? String(cabinet.buttons) : ''],
  ].filter((spec): spec is [string, string] => !!spec[1]);
  const botones = cabinet?.button_list ?? [];

  return (
    <Card band="var(--accent-3)" title="Gabinete">
      <div className={styles.stack}>
        {specs.length > 0 || botones.length > 0 ? (
          <>
            {specs.length > 0 ? (
              <dl className={styles.specs}>
                {specs.map(([nombre, valor]) => (
                  <div className={styles.spec} key={nombre}>
                    <dt>{nombre}</dt>
                    <dd>{valor}</dd>
                  </div>
                ))}
              </dl>
            ) : null}
            {botones.length > 0 ? (
              <table className={styles.tabla}>
                <caption className={styles.rotulo}>Mapa de botones</caption>
                <thead>
                  <tr><th scope="col">Acción</th><th scope="col">Control</th><th scope="col">Color</th></tr>
                </thead>
                <tbody>
                  {botones.map((btn, idx) => (
                    <tr key={`${btn.control}-${idx}`}>
                      <td>{btn.action}</td>
                      <td><code>{btn.control}</code></td>
                      <td>{btn.color}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : null}
          </>
        ) : (
          <p className={styles.vacio}>Sin información de gabinete para este juego.</p>
        )}
        <p className={styles.meta}>
          Fuente: Arcade Database (motoschifo) — adb.arcadeitalia.net · Historia (C) arcade-history.com
        </p>
      </div>
    </Card>
  );
}
