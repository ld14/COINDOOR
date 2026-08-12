# 004 · Dominio, contrato y datos mock

**Estado:** hecho

## Qué hace

**Recibe** el contrato de ATTRACT y la política de completitud de COINDOOR. **Produce**
los dos archivos de datos que gobiernan todo el sistema —`contract.json` y
`fielddefs.json`—, las funciones de dominio que los consumen en TypeScript **y** en Python,
y un mock server con los diez juegos del seed.

Es la feature que **aplica los deltas D1–D5** sobre el paquete de diseño: `review` y
`cheats` pasan a ser estructuras, aparece `accent2`, y desaparece el estado `broken`.

**No** dibuja ninguna pantalla: eso son las Fases 3 y 4.

## Por qué

Es la Fase 2 del roadmap, y es donde vive la regla que sostiene el producto: **qué
significa que un juego esté completo**. Esa regla se evalúa en dos lados —el cliente para
dar feedback sin round-trip, el servidor para hacerla cumplir— y por eso los datos que la
alimentan tienen que ser **un solo archivo**, no dos copias
([`ADR-0011`](../../decisions/0011-fielddefs-json-compartido.md)).

Sin esto, las pantallas se construyen sobre tipos inventados y los deltas se aplican tarde,
cuando ya hay componentes escritos contra la forma vieja.

## Criterios de aceptación

- [x] Existe `lib/domain/contract.json`, con su versión y procedencia. Si ATTRACT todavía
      no lo publica, se deriva de `CONVENCION` y `goldnaxe`, queda documentado, y **no se
      edita a mano después**.
- [x] Existe `lib/domain/fielddefs.json` con `key`, `label`, `ratio` y `required` por
      campo, y **referencia** claves del contrato mediante un mapeo explícito UI ↔ contrato
      en vez de redefinirlas.
- [x] **Un test falla si los dos archivos divergen**: los assets de `fielddefs.json` deben
      mapear a assets del contrato, y los campos de identidad/texto/acento deben mapear a
      campos del contrato o a datos ricos explícitos.
- [x] `missingRequired` devuelve exactamente los 7 campos de identidad, carátula, póster,
      sinopsis y el color de acento primario. **Nada más bloquea nunca.**
- [x] `computeGameStatus` respeta la prioridad fija: `errors > 0` → `error`; faltantes → `incomplete`; si no → `ready`. Un juego con error de formato es `error` **aunque además esté completo**.
- [x] **Las implementaciones de TypeScript y Python dan el mismo resultado** sobre los diez
      juegos del seed.
- [x] `review` y `cheats` son estructuras, no texto: `ReviewField` con `score: number | null`
      y `cats` **parcial**, y `CheatsField` con grupos de nombre libre (delta D1).
      `Reseña` y `Trucos` quedan solo como labels de UI.
- [x] Una categoría de reseña vacía es un valor legítimo y **no** cuenta como faltante.
- [x] Existen `accentValue` y `accent2Value`, y **solo el primario es obligatorio**
      (delta D2).
- [x] El estado `broken` de revista **no existe** en ningún tipo ni en el seed (delta D3).
- [x] La validación de `launchCmd` rechaza rutas relativas y acepta POSIX y Windows, con el
      mensaje literal del diseño.
- [x] El mock server sirve los diez juegos del seed y los cuatro sistemas, uno de ellos con
      cabecera inválida a propósito.
- [x] El seed ejercita un caso de borde en lugar de `Contra · vínculo de revista roto`, que
      bajo el delta D3 ya no ejercita nada.

## Fuera de alcance

- **Las pantallas.** Fases 3 y 4 del roadmap.
- **La API real.** El mock server responde el contrato; implementarlo es la feature
  [005](../005-esqueleto-backend/spec.md).
- **La lógica de export y de proveedores.** Features
  [001](../001-export-bundle/spec.md) y [002](../002-sugerencias-multiproveedor/spec.md).
- **Publicar el contrato desde ATTRACT.** Es trabajo del otro repo
  ([`ADR-0001`](../../decisions/0001-contrato-coindoor-attract.md)); acá se vendorea a mano.
