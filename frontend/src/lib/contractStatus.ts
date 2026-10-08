import contract from '@/lib/domain/contract.json';

export interface ContractStatus {
  ok: boolean;
  /** "v1" cuando la versión es `attract-1`; vacío si no se pudo leer. */
  version: string;
  /** Texto del indicador, p. ej. "Contrato ATTRACT v1". */
  label: string;
  /** Qué está mal con el contrato vendoreado; solo existe si `ok` es false. */
  problem?: string;
}

interface ContractShape {
  version?: unknown;
  metadataFields?: { required?: unknown };
  assets?: unknown;
}

/** Evalúa el contrato vendoreado (`contract.json`). Es un dato local, no un pedido
 * de red: un problema acá significa que el bundle que se arme saldría con un
 * contrato roto, por eso el Banner solo aparece en ese caso.
 */
export function contractStatusOf(source: ContractShape): ContractStatus {
  const match = typeof source.version === 'string' ? /^attract-(\d+)$/.exec(source.version) : null;
  if (!match) {
    return { ok: false, version: '', label: 'Contrato ATTRACT', problem: 'No se pudo leer la versión del contrato ATTRACT vendoreado.' };
  }
  const version = `v${match[1]}`;
  const label = `Contrato ATTRACT ${version}`;
  const required = source.metadataFields?.required;
  if (!Array.isArray(required) || required.length === 0 || !source.assets || typeof source.assets !== 'object') {
    return { ok: false, version, label, problem: `El contrato ATTRACT ${version} vendoreado está incompleto: faltan campos obligatorios o assets.` };
  }
  return { ok: true, version, label };
}

export const contractStatus: ContractStatus = contractStatusOf(contract);
