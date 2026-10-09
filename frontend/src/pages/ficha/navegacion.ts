import { anclaSeccion, type PendienteFicha } from '@/hooks/useFichaProgress';

/**
 * Helpers de DOM de la ficha: scroll a una sección o a un campo concreto.
 * Viven acá (y no en cada componente) para que píldoras, StepNav, "Siguiente pendiente" y el atajo
 * `N` resuelvan el destino de la misma manera.
 */

const SELECTOR_CONTROL = 'input:not([type="hidden"]):not([type="file"]), textarea, select, button';
const MS_RESALTADO = 1600;

function sinMovimiento(): boolean {
  return typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function desplazar(el: HTMLElement, block: ScrollLogicalPosition) {
  // jsdom no implementa scrollIntoView.
  el.scrollIntoView?.({ behavior: sinMovimiento() ? 'auto' : 'smooth', block });
}

/** Marca un elemento un momento (atributo `data-resaltado`, estilado en ficha.module.css). */
export function resaltar(el: HTMLElement) {
  el.setAttribute('data-resaltado', 'true');
  window.setTimeout(() => el.removeAttribute('data-resaltado'), MS_RESALTADO);
}

export function irASeccion(clave: string): HTMLElement | null {
  const el = document.getElementById(anclaSeccion(clave));
  if (!el) return null;
  desplazar(el, 'start');
  return el;
}

/** El control de un campo: `data-campo="<clave>"` si la sección lo expone; si no, por rótulo accesible. */
export function buscarCampo(raiz: ParentNode, pendiente: Pick<PendienteFicha, 'campo' | 'etiquetas'>): HTMLElement | null {
  if (pendiente.campo) {
    const porClave = [...raiz.querySelectorAll<HTMLElement>('[data-campo]')].find((el) => el.dataset.campo === pendiente.campo);
    if (porClave) return porClave;
  }
  const rotulados = [...raiz.querySelectorAll<HTMLElement>('[aria-label]')];
  for (const etiqueta of pendiente.etiquetas) {
    const hallado = rotulados.find((el) => el.getAttribute('aria-label') === etiqueta);
    if (hallado) return hallado;
  }
  return null;
}

/**
 * Lleva a un pendiente: scroll al campo (o a su sección si no se lo encuentra) y lo resalta.
 * Con `enfocar` además pone el foco en el control, para empezar a escribir.
 */
export function irAPendiente(raiz: ParentNode, pendiente: PendienteFicha, enfocar: boolean): HTMLElement | null {
  const campo = buscarCampo(raiz, pendiente);
  if (!campo) {
    const seccion = irASeccion(pendiente.seccion);
    if (seccion) resaltar(seccion);
    return seccion;
  }
  desplazar(campo, 'center');
  resaltar(campo);
  if (enfocar) {
    const control = campo.matches(SELECTOR_CONTROL) ? campo : campo.querySelector<HTMLElement>(SELECTOR_CONTROL);
    control?.focus({ preventScroll: true });
  }
  return campo;
}

/** El pendiente de sugerencia cuyo campo contiene al elemento con foco, si lo hay. */
export function sugerenciaEnFoco(raiz: ParentNode, activo: Element | null, sugerencias: PendienteFicha[]): PendienteFicha | null {
  if (!(activo instanceof HTMLElement)) return null;
  return sugerencias.find((s) => {
    const campo = buscarCampo(raiz, s);
    return campo !== null && (campo === activo || campo.contains(activo));
  }) ?? null;
}
