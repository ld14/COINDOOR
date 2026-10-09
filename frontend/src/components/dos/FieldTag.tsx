import { OriginChip } from './OriginChip';

export type FieldTagStatus = 'manual' | 'suggested' | 'empty';

interface FieldTagProps {
  required?: boolean;
  source?: string;
  status?: FieldTagStatus;
}

/** Alias histórico de {@link OriginChip}; los usos nuevos deberían importar OriginChip. */
export function FieldTag({ required, source, status = 'empty' }: FieldTagProps) {
  return <OriginChip required={required} source={source} status={status} />;
}
