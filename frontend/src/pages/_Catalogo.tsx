import { useState } from 'react';
import { Banner, DosButton, DosInput, DosSelect, DosTextarea, FieldTag, MenuBar, Modal, Panel, ProgressBar, SectionHeader, Spinner, StatusBadge, StatusBar, SunkenBox } from '@/components/dos';
import styles from './_Catalogo.module.css';

export function Catalogo() {
  const [open, setOpen] = useState(false);

  return (
    <div className={styles.catalog}>
      <h1>Catálogo interno de primitivas</h1>
      <Banner>Banner: revisar contrato ATTRACT antes de exportar.</Banner>
      <div className={styles.grid}>
        <Panel><SectionHeader>Panel y SunkenBox</SectionHeader><SunkenBox>Área hundida</SunkenBox></Panel>
        <Panel><SectionHeader>Botones</SectionHeader><div className={styles.stack}>
          <div className={styles.row}><DosButton variant="primary">Primario</DosButton><DosButton variant="primary-small">Primario chico</DosButton></div>
          <div className={styles.row}><DosButton>Ghost</DosButton><DosButton variant="ghost-small">Ghost chico</DosButton><DosButton variant="danger-small">Borrar</DosButton></div>
          <div className={styles.row}><DosButton pressed>Presionado</DosButton><DosButton disabled>No disponible</DosButton></div>
        </div></Panel>
        <Panel><SectionHeader>Campos</SectionHeader><div className={styles.stack}>
          <DosInput aria-label="Input de catálogo" defaultValue="Golden Axe" />
          <DosSelect aria-label="Select de catálogo" defaultValue="arcade"><option value="arcade">Arcade</option><option value="dos">MS-DOS</option></DosSelect>
          <DosTextarea aria-label="Textarea de catálogo" defaultValue="Sinopsis del juego." />
        </div></Panel>
        <Panel><SectionHeader>Estados</SectionHeader><div className={styles.stack}>
          <div className={styles.row}><StatusBadge status="ready" /><StatusBadge status="incomplete" /><StatusBadge status="error" /></div>
          <div className={styles.row}><FieldTag status="manual" /><FieldTag status="suggested" /><FieldTag status="empty" /></div>
        </div></Panel>
        <Panel><SectionHeader>Progreso</SectionHeader><div className={styles.stack}><ProgressBar value={42} /><Spinner /></div></Panel>
        <Panel><SectionHeader>Modal</SectionHeader><DosButton onClick={() => setOpen(true)} variant="primary-small">Abrir modal</DosButton></Panel>
        <Panel><SectionHeader>Preview</SectionHeader><div className={styles.preview}>carátula · 3:4</div></Panel>
        <Panel className={styles.menuPreview}><SectionHeader>MenuBar</SectionHeader><MenuBar /></Panel>
        <Panel className={styles.statusPreview}><SectionHeader>StatusBar</SectionHeader><StatusBar /></Panel>
      </div>
      <Modal onClose={() => setOpen(false)} open={open} title="Modal de catálogo">
        <div className={styles.stack}>
          <DosInput aria-label="Campo dentro del modal" defaultValue="Foco atrapado" />
          <div className={styles.row}><DosButton onClick={() => setOpen(false)} variant="primary">Aceptar</DosButton><DosButton onClick={() => setOpen(false)}>Cancelar</DosButton></div>
        </div>
      </Modal>
    </div>
  );
}
