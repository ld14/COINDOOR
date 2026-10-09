/** `source` de un campo cuyo texto lo produjo la IA («IA», «ArcadeDB · traducido por IA»…). */
export function esFuenteIA(source?: string): boolean {
  return !!source && /(^|[^a-z0-9])ia([^a-z0-9]|$)/i.test(source);
}
