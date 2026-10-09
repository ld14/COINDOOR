import { Card, type CardProps } from './Card';

export type PanelProps = CardProps;

/** Alias histórico de {@link Card}. Sin `title` se comporta como la tarjeta sin encabezado de siempre. */
export function Panel(props: PanelProps) {
  return <Card {...props} />;
}
