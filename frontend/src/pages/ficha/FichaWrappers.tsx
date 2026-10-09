import { ActionBar, NextPendingCard, StepNav } from '@/components/dos';
import { stepsDe, type FichaProgress, type PendienteFicha } from '@/hooks/useFichaProgress';

/**
 * Los tres controles de navegación de la ficha, cableados a `useFichaProgress`.
 * Son finos a propósito: la lógica (qué falta, en qué orden) vive en el hook y el scroll en FichaPage.
 */

export function FichaStepNav({ progress, activeId, onSelect }: { progress: FichaProgress; activeId?: string; onSelect: (clave: string) => void }) {
  return <StepNav activeId={activeId} aria-label="Secciones de la ficha" items={stepsDe(progress)} onSelect={onSelect} />;
}

export function FichaNextPending({ progress, onGo }: { progress: FichaProgress; onGo: (pendiente: PendienteFicha) => void }) {
  return (
    <NextPendingCard
      items={progress.cola}
      onGo={(item) => {
        const pendiente = progress.cola.find((p) => p.id === item.id);
        if (pendiente) onGo(pendiente);
      }}
    />
  );
}

interface FichaActionBarProps {
  progress: FichaProgress;
  /** Errores de formato: bloquean el export igual que los obligatorios. */
  erroresDeFormato: number;
  onSaveDraft: () => void;
  onExport: () => void;
}

export function FichaActionBar({ progress, erroresDeFormato, onSaveDraft, onExport }: FichaActionBarProps) {
  const faltan = progress.faltantes.length;
  const motivo = faltan > 0 ? `faltan ${faltan}` : erroresDeFormato > 0 ? `${erroresDeFormato} error(es) de formato` : undefined;
  return (
    <ActionBar
      exportDisabledReason={motivo}
      onExport={onExport}
      onSaveDraft={onSaveDraft}
      percent={progress.percent}
      requiredCount={faltan}
      reviewCount={progress.sugerencias.length}
      shortcuts={[
        { keys: 'Enter', label: 'aceptar sugerencia' },
        { keys: 'N', label: 'siguiente pendiente' },
      ]}
    />
  );
}
