export type SaveHandle = { save: () => void };
/** 0 = acento primario, 1 = secundario. */
export type AccentSlot = 0 | 1;
export type PresentationHandle = SaveHandle & { setAccent: (slot: AccentSlot, value: string) => void };
