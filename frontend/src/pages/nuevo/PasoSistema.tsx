import { ChoiceCards, DosButton } from '@/components/dos';
import type { System, Tratamiento } from '@/lib/domain/types';
import type { Deteccion } from './utils';
import styles from './NuevoJuego.module.css';

interface Props {
  sistemas: System[];
  cargando: boolean;
  systemId: string;
  onSystem: (id: string) => void;
  tratamiento: Tratamiento;
  onTratamiento: (valor: Tratamiento) => void;
  deteccion: Deteccion | null;
  onNuevoSistema: () => void;
}

export function PasoSistema({ sistemas, cargando, systemId, onSystem, tratamiento, onTratamiento, deteccion, onNuevoSistema }: Props) {
  const nombre = (id: string) => sistemas.find((s) => s.id === id)?.name ?? id;
  // El sistema de un candidato puede no estar en `sistemas.json` (carpeta huérfana):
  // sin esta opción el alta se iría a un sistema que el usuario no eligió.
  const desconocido = Boolean(systemId) && sistemas.length > 0 && !sistemas.some((s) => s.id === systemId);
  const opciones = [
    ...sistemas.map((s) => ({ value: s.id, label: s.name, subtitle: s.shortName })),
    ...(desconocido ? [{ value: systemId, label: systemId, subtitle: 'sin sistema declarado' }] : []),
  ];

  return (
    <div className={styles.stack}>
      {deteccion ? (
        <p className={styles.detected}>
          <span className={styles.chip}>Detectado</span>
          Por la carpeta <code className={styles.mono}>{deteccion.carpeta}/</code> se propone {nombre(deteccion.systemId)} +{' '}
          {deteccion.tratamiento === 'copiar' ? 'Copiar' : 'Descomprimir'}. Podés cambiarlo.
        </p>
      ) : null}
      <h3 className={styles.subhead}>Sistema</h3>
      {cargando ? <p className={styles.hint}>Cargando sistemas…</p> : null}
      {opciones.length > 0 ? <ChoiceCards ariaLabel="Sistema" onChange={onSystem} options={opciones} value={systemId} /> : null}
      <div>
        <DosButton onClick={onNuevoSistema} size="sm" type="button" variant="ghost">+ Nuevo sistema</DosButton>
      </div>
      <h3 className={styles.subhead}>Tratamiento</h3>
      <ChoiceCards
        ariaLabel="Tratamiento"
        onChange={(valor) => onTratamiento(valor as Tratamiento)}
        options={[
          { value: 'copiar', label: 'Copiar', subtitle: 'romset' },
          { value: 'descomprimir', label: 'Descomprimir', subtitle: 'archivos sueltos' },
        ]}
        value={tratamiento}
      />
    </div>
  );
}
