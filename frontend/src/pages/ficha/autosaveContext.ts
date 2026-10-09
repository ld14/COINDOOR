import { createContext, useContext } from 'react';

/** Lo que las secciones de la ficha pueden pedirle al andamiaje (ver contrato en FichaPage.tsx, puntos 4 y 6). */
export interface FichaAutosaveApi {
  /** Marca una sección como sucia cuando el cambio no emitió un evento nativo `input`/`change`. */
  markDirty: (seccion: string) => void;
  /** Acepta la sugerencia de un campo: pasa a `manual` conservando valor y `source`. */
  aceptar: (clave: string) => void;
}

export const FichaAutosaveContext = createContext<FichaAutosaveApi>({
  markDirty: () => undefined,
  aceptar: () => undefined,
});

export function useFichaAutosave(): FichaAutosaveApi {
  return useContext(FichaAutosaveContext);
}
