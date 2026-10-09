/** Texto de una línea por ítem → array de strings (sin vacíos ni espacios sobrantes). */
export function lineasAItems(texto: string): string[] {
  return texto.split(/\r?\n/).map((linea) => linea.trim()).filter((linea) => linea.length > 0);
}

/** Array de strings → texto de una línea por ítem. */
export function itemsALineas(items: string[]): string {
  return items.join('\n');
}
