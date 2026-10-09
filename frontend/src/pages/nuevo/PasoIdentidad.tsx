import { DosInput } from '@/components/dos';
import { FIELDDEFS } from '@/lib/domain/types';
import type { Identity } from '@/lib/domain/types';
import styles from './NuevoJuego.module.css';

interface Props {
  identity: Identity;
  onChange: (identity: Identity) => void;
  precargada: boolean;
}

export function PasoIdentidad({ identity, onChange, precargada }: Props) {
  return (
    <div className={styles.stack}>
      <p className={styles.hint}>
        {precargada
          ? 'Ya viene el título del instalado. Si el catálogo reconoce el juego, el resto se completa al abrir la ficha.'
          : 'No hay datos previos: completá lo que sepas o dejalo para la ficha.'}
      </p>
      <div className={styles.fields}>
        {FIELDDEFS.identity.map(({ key, label }) => (
          <label className={styles.field} key={key}>
            <span className={styles.label}>{label}</span>
            <DosInput aria-label={label} onChange={(event) => onChange({ ...identity, [key]: event.target.value })} value={identity[key as keyof Identity]} />
          </label>
        ))}
      </div>
    </div>
  );
}
