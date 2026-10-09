import { useState } from 'react';
import { ActionBar, CheckTile, FilterChips, FilterTabs, NextPendingCard, StepNav } from '@/components/dos/nav';
import type { PendingItem, StepNavItem } from '@/components/dos/nav';
import styles from './NavDemo.module.css';

const STEPS: StepNavItem[] = [
  { id: 'identidad', label: 'Identidad', status: 'complete' },
  { id: 'objetivo', label: 'Objetivo', status: 'blocking', hint: 'Objetivo obligatorio' },
  { id: 'imagenes', label: 'Imágenes', status: 'review', hint: '5 sugeridos' },
  { id: 'texto', label: 'Texto' },
];

const PENDING: PendingItem[] = [
  { id: 'rev', label: 'Revisar 5 imágenes sugeridas', severity: 'review', step: 3 },
  { id: 'obj', label: 'Objetivo del juego', severity: 'required', step: 2 },
  { id: 'car', label: 'Carátula', severity: 'required', step: 3 },
];

const TABS = [
  { id: 'all', label: 'Todos', count: 128 },
  { id: 'wip', label: 'En carga', count: 7 },
  { id: 'ready', label: 'Listos sin exportar', count: 12 },
  { id: 'done', label: 'Exportados', count: 106 },
  { id: 'err', label: 'Con errores', count: 3 },
];

const SYSTEMS = [
  { id: 'arcade', label: 'Arcade', count: 90 },
  { id: 'dos', label: 'MS-DOS', count: 30 },
  { id: 'snes', label: 'SNES', count: 8 },
];

/** Demo de las primitivas de navegación en todos sus estados. */
export function NavDemo() {
  const [active, setActive] = useState('texto');
  const [tab, setTab] = useState('all');
  const [multi, setMulti] = useState<string[]>(['arcade']);
  const [single, setSingle] = useState<string[]>([]);
  const [video, setVideo] = useState(true);
  const [manual, setManual] = useState(false);
  const [last, setLast] = useState('—');

  return (
    <div className={styles.demo}>
      <section className={styles.block}>
        <h3 className={styles.title}>StepNav (en curso · completa · bloquea · revisar)</h3>
        <StepNav activeId={active} items={STEPS} onSelect={setActive} />
      </section>
      <section className={styles.block}>
        <h3 className={styles.title}>CheckTile (sin tildar · tildado · deshabilitado con motivo)</h3>
        <div className={styles.stack}>
          <CheckTile checked={manual} label="Manual" meta="4,2 MB" onChange={setManual} />
          <CheckTile checked={video} label="Video" meta="12 MB" onChange={setVideo} />
          <CheckTile checked={false} disabled disabledReason="no hay trucos" label="Trucos" />
        </div>
      </section>
      <section className={styles.block}>
        <h3 className={styles.title}>FilterTabs</h3>
        <FilterTabs items={TABS} onChange={setTab} value={tab} />
      </section>
      <section className={styles.block}>
        <h3 className={styles.title}>FilterChips (multi · single)</h3>
        <div className={styles.stack}>
          <FilterChips items={SYSTEMS} onChange={setMulti} value={multi} />
          <FilterChips items={SYSTEMS} mode="single" onChange={setSingle} value={single} />
        </div>
      </section>
      <section className={styles.block}>
        <h3 className={styles.title}>NextPendingCard (con cola · sin pendientes) — último destino: {last}</h3>
        <div className={styles.side}>
          <NextPendingCard items={PENDING} onGo={(item) => setLast(item.label)} />
          <NextPendingCard items={[]} onGo={() => undefined} shortcut={null} />
        </div>
      </section>
      <section className={styles.block}>
        <h3 className={styles.title}>ActionBar (Exportar bloqueado · habilitado)</h3>
        <div className={styles.stack}>
          <ActionBar
            exportDisabledReason="faltan 3"
            onExport={() => undefined}
            onSaveDraft={() => undefined}
            percent={60}
            requiredCount={3}
            reviewCount={6}
            shortcuts={[{ keys: 'Enter', label: 'aceptar sugerencia' }, { keys: 'N', label: 'siguiente pendiente' }]}
          />
          <ActionBar onExport={() => undefined} onSaveDraft={() => undefined} percent={100} />
        </div>
      </section>
    </div>
  );
}
