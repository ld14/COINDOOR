# 012 · Instalar en ATTRACT

**Estado:** implementada

Decisión en [`ADR-0021`](../../decisions/0021-instalar-bundle-por-subproceso.md). La ruta
de ATTRACT que usa esta feature se configura en
[013 · Configuración](../013-configuracion/spec.md), no en `.env`
([`ADR-0022`](../../decisions/0022-configuracion-no-sensible-en-archivo-propio.md)).

## Qué hace

**Recibe** un juego que ya tiene un export generado (feature [001](../001-export-bundle/spec.md))
y **dispara**, por subproceso, el instalador que ya existe del lado de ATTRACT
(`install-coindoor-wsl.sh`) sobre ese `.zip` y la librería local configurada. Muestra si
terminó bien o mal.

**No** reimplementa la instalación: no lee `bundle.json`, no escribe
`metadata.pegasus.txt`, no resuelve identidad ni corre `doctor` con su propia lógica —
todo eso es responsabilidad exclusiva del script de ATTRACT, tal como manda
[`ADR-0001`](../../decisions/0001-contrato-coindoor-attract.md). COINDOOR solo lo invoca
y reporta su código de salida.

## Por qué

Hoy, después de exportar, instalar en la librería local significa copiar la ruta del
`.zip` a mano y correr `./install-coindoor-wsl.sh <ruta> library/` en otra terminal. Es el
mismo comando, con la misma forma, cada vez — la clase de fricción repetida que vale la
pena resolver en un producto de un usuario, un juego por vez (ver
[`ADR-0021`](../../decisions/0021-instalar-bundle-por-subproceso.md) para por qué esto no
choca con que la instalación quedó fuera de alcance de la feature 001).

## Criterios de aceptación

- [x] Dado un juego recién exportado y la ruta de ATTRACT configurada en Configuración
      con un checkout válido, cuando se toca "Cargar en ATTRACT", entonces el backend
      corre `<ATTRACT_DIR>/install-coindoor-wsl.sh <bundle> <ATTRACT_DIR>/library` y, si
      termina con código 0, la pantalla muestra que se instaló.
- [x] Dado el mismo caso pero el script termina con código distinto de 0, la pantalla
      muestra su salida (stdout + stderr) como texto de diagnóstico, sin intentar
      interpretarla.
- [x] Dado un juego sin ningún export previo (no existe el `.zip` en `games/exports/`),
      la acción falla explícito pidiendo exportar primero — nunca genera un export nuevo
      por su cuenta.
- [x] Dada la ruta de ATTRACT sin configurar, o apuntando a una carpeta sin
      `install-coindoor-wsl.sh`, la acción falla explícito nombrando qué falta — nunca
      falla en silencio ni oculta el botón.
- [x] La acción es síncrona: no aparece como job con `jobId` ni con barra de progreso
      (ver `plan.md` §Enfoque).
- [x] El botón vive en la pantalla de resultado del export (`/exportar/:gameId`), junto a
      "Volver a Juegos" y "Exportar otro".

La salida de diagnóstico puede contener bytes no UTF-8 al cruzar WSL y Windows.
Eso nunca debe provocar un HTTP 500 ni cambiar el veredicto del código de salida;
los caracteres inválidos se muestran como reemplazos.

## Fuera de alcance

- **Reimplementar la lógica de instalación** (merge de `metadata.pegasus.txt`, copia de
  `media/`, `doctor` sobre lo instalado) — eso vive y se mantiene en `../attract`.
- **Elegir entre varios destinos de instalación.** Una sola ruta de ATTRACT por
  instalación de COINDOOR — eso es lo que dice
  [`ADR-0021`](../../decisions/0021-instalar-bundle-por-subproceso.md) que se revisaría
  si aparece una segunda máquina real.
- **macOS o Windows nativo.** El instalador tiene esas variantes
  (`install-coindoor.sh`/`.ps1`), pero cablearlas es trabajo futuro si aparece esa
  máquina — hoy el único entorno real es WSL.
- **Generar el export si no existe.** Eso es la feature [001](../001-export-bundle/spec.md);
  esta feature solo instala uno que ya está en disco.
- **Progreso o cancelación.** No es un job (ver `plan.md`).
