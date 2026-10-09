import { useState } from 'react';
import { Banner } from '@/components/dos/Banner';
import { Card } from '@/components/dos/Card';
import { DosButton } from '@/components/dos/DosButton';
import { DosInput } from '@/components/dos/DosInput';
import { DosSelect } from '@/components/dos/DosSelect';
import { DosTextarea } from '@/components/dos/DosTextarea';
import { FieldTag } from '@/components/dos/FieldTag';
import { Modal } from '@/components/dos/Modal';
import { OriginChip } from '@/components/dos/OriginChip';
import { Panel } from '@/components/dos/Panel';
import { ProgressBar } from '@/components/dos/ProgressBar';
import { SectionHeader } from '@/components/dos/SectionHeader';
import { Spinner } from '@/components/dos/Spinner';
import { StatusBadge } from '@/components/dos/StatusBadge';
import { SunkenBox } from '@/components/dos/SunkenBox';
import styles from './BaseDemo.module.css';

/** Demo de las primitivas base del rediseño Flyer, en todos sus estados. */
export function BaseDemo() {
  const [open, setOpen] = useState(false);

  return (
    <div className={styles.demo}>
      <Card band="var(--accent)" hint="todas las variantes y tamaños" number={1} title="DosButton">
        <div className={styles.stack}>
          <div className={styles.row}>
            <DosButton variant="primary">Primary</DosButton>
            <DosButton variant="secondary">Secondary</DosButton>
            <DosButton variant="ghost">Ghost</DosButton>
            <DosButton variant="danger">Danger</DosButton>
          </div>
          <div className={styles.row}>
            <DosButton size="sm" variant="primary">Primary sm</DosButton>
            <DosButton size="sm" variant="secondary">Secondary sm</DosButton>
            <DosButton size="sm" variant="ghost">Ghost sm</DosButton>
            <DosButton size="sm" variant="danger">Danger sm</DosButton>
          </div>
          <div className={styles.row}>
            <DosButton variant="primary-small">primary-small</DosButton>
            <DosButton variant="ghost-small">ghost-small</DosButton>
            <DosButton variant="danger-small">danger-small</DosButton>
            <DosButton pressed variant="secondary">Pressed</DosButton>
          </div>
          <div className={styles.row}>
            <DosButton disabled variant="primary">Exportar (faltan 3)</DosButton>
            <DosButton disabled disabledReason="Faltan 3 campos obligatorios" variant="primary">Con motivo en title</DosButton>
            <DosButton disabled variant="secondary">Secondary</DosButton>
            <DosButton disabled variant="ghost">Ghost</DosButton>
          </div>
        </div>
      </Card>

      <Card band="var(--accent-3)" hint="estado del juego" number={2} title="StatusBadge">
        <div className={styles.row}>
          <StatusBadge status="incomplete" />
          <StatusBadge status="ready" />
          <StatusBadge status="error" />
          <StatusBadge status="exported" />
        </div>
      </Card>

      <Card band="var(--accent-2)" hint="DESIGN_SPEC §3" number={3} title="OriginChip">
        <div className={styles.row}>
          <OriginChip status="empty" />
          <OriginChip required status="empty" />
          <OriginChip status="suggested" />
          <OriginChip source="arcadedb" status="manual" />
          <OriginChip source="mame" status="manual" />
          <OriginChip source="manual" status="manual" />
          <OriginChip status="manual" />
          <FieldTag status="manual" />
        </div>
      </Card>

      <Card band="var(--ok)" hint="invalid + errorMessage" number={4} title="Campos">
        <div className={styles.grid}>
          <label className={styles.field}>Normal<DosInput placeholder="Ej.: 1993" /></label>
          <label className={styles.field}>Con valor<DosInput defaultValue="Golden Axe" /></label>
          <label className={styles.field}>Deshabilitado<DosInput defaultValue="No editable" disabled /></label>
          <label className={styles.field}>Inválido<DosInput defaultValue="19x3" errorMessage="Año inválido: 4 dígitos" /></label>
          <label className={styles.field}>Select<DosSelect defaultValue="arcade"><option value="arcade">Arcade</option><option value="dos">MS-DOS</option></DosSelect></label>
          <label className={styles.field}>Select inválido<DosSelect errorMessage="Elegí un sistema" defaultValue=""><option value="">—</option><option value="arcade">Arcade</option></DosSelect></label>
          <label className={styles.field}>Textarea<DosTextarea placeholder="Ej.: Tres héroes recorren…" /></label>
          <label className={styles.field}>Textarea inválido<DosTextarea errorMessage="Hex incompleto: 6 dígitos" invalid /></label>
        </div>
      </Card>

      <Card band="var(--warn)" hint="píldora con relleno por estado" number={5} title="ProgressBar y Spinner">
        <div className={styles.stack}>
          <ProgressBar value={0} />
          <ProgressBar value={45} />
          <ProgressBar state="ok" value={100} />
          <ProgressBar state="error" value={60} />
          <div className={styles.row}><Spinner /> Cargando…</div>
        </div>
      </Card>

      <Card band="var(--error)" number={6} title="Banner, SunkenBox, SectionHeader y Panel">
        <div className={styles.stack}>
          <Banner>Revisar el contrato ATTRACT antes de exportar.</Banner>
          <SunkenBox>Caja hundida: fondo surface-2, borde line-soft.</SunkenBox>
          <SectionHeader>SectionHeader (encabezado de página)</SectionHeader>
          <Panel>Panel: alias de Card sin encabezado.</Panel>
        </div>
      </Card>

      <Card actions={<DosButton size="sm" variant="secondary">↻ Sugerir todo</DosButton>} band="var(--surface-inverse)" hint="sin número ni acciones también vale" title="Card con acciones">
        Contenido de la tarjeta.
      </Card>

      <Card band="var(--accent)" number={8} title="Modal">
        <div className={styles.row}>
          <DosButton onClick={() => setOpen(true)} variant="primary">Abrir modal</DosButton>
        </div>
      </Card>
      <Modal band="var(--accent-3)" onClose={() => setOpen(false)} open={open} size="small" title="Modal de ejemplo">
        <p>Esc, el botón Cerrar o un click afuera lo cierran.</p>
        <DosButton onClick={() => setOpen(false)} variant="secondary">Entendido</DosButton>
      </Modal>
    </div>
  );
}
