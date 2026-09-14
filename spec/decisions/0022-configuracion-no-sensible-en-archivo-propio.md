---
id: 0022
title: Configuración no sensible en un archivo propio, editable desde una pantalla nueva
status: accepted
date: 2026-09-12
supersedes: null
superseded-by: null
tags: [backend, frontend, proceso]
---

# 0022 — Configuración no sensible en un archivo propio, editable desde una pantalla nueva

## Contexto

[`ADR-0021`](0021-instalar-bundle-por-subproceso.md) agregó `COINDOOR_ATTRACT_DIR` como
variable de entorno en `.env`, siguiendo el único mecanismo de configuración que existía
hasta ahora (`tech-stack.md`: *"Configuración | pydantic-settings + `.env` fuera del
repo"*). En la práctica, eso significa editar un archivo a mano y reiniciar el proceso
cada vez que cambia — exactamente la fricción que motivó, unos ADRs antes, automatizar el
paso de instalar.

`.env` tiene sentido para credenciales (claves de IA, del buscador): son secretos que no
deben viajar ni mostrarse. `COINDOOR_ATTRACT_DIR` no es un secreto — es una ruta local de
esta máquina, del mismo tipo que ya vive en `sistemas.json` (`launchCmd`). Tratarla como
si fuera una credencial le hereda una fricción que no le corresponde.

## Decisión

**Los ajustes no sensibles de esta instalación de COINDOOR viven en un archivo propio,
`configuracion.json` en `data_dir`**, con el mismo patrón que `sistemas.json`
(`ConfigStore`, escritura atómica vía `store/archivo.py`, validado con Pydantic). Se edita
desde una pantalla nueva, `/configuracion`, con el mismo look de `Sistemas`.

Hoy el único campo es `attractDir` (reemplaza a `COINDOOR_ATTRACT_DIR`: la variable de
entorno se da de baja, no coexiste con el archivo — dos fuentes de verdad para el mismo
valor es la clase de complejidad que `tech-stack.md` pide no sumar). Queda abierto a sumar
más campos no sensibles después, sin cambiar de mecanismo.

**Las credenciales (`AI_PRIMARY_*`, `AI_BACKUP_*`, `SEARCH_*`) siguen exclusivamente en
`.env`.** No se muestran en ninguna pantalla. La app corre en loopback
([`ADR-0009`](0009-proceso-local-en-loopback.md)), pero eso no borra el riesgo de mostrar
una clave en texto plano en una UI que alguien puede compartir pantalla o fotografiar; y
duplicar el mecanismo de secretos (una parte en `.env`, otra en un JSON) es peor que tener
uno solo, ya documentado en `backend/CLAUDE.md`.

## Alternativas consideradas

### A. Dejar todo en `.env`, editado a mano

- A favor: cero código nuevo.
- En contra: es la fricción concreta que motivó este ADR — cambiar una ruta exige abrir
  un archivo de texto y reiniciar el proceso.
- **Descartada porque:** el pedido explícito fue tener una pantalla para esto.

### B. Una sola pantalla que edita todo `.env`, credenciales incluidas

- A favor: un solo lugar para toda la configuración, sin distinguir tipos.
- En contra: expone claves de API en una UI — más superficie de exposición (captura de
  pantalla, compartir pantalla) que un archivo de texto que nadie abre por accidente.
- **Descartada porque:** el costo de exposición no tiene contrapartida real hoy;
  `COINDOOR_ATTRACT_DIR` es el único dato no sensible con fricción real. Si aparece una
  necesidad concreta de rotar credenciales seguido desde la UI, se revisita.

### C. Guardar `attractDir` también en `.env`, pero escrito por el backend

- A favor: un solo mecanismo de persistencia (`.env`) para todo.
- En contra: `.env` lo carga `pydantic-settings` una sola vez al arrancar
  (`Settings()`); reescribirlo en caliente no cambia el proceso corriendo, así que
  igual haría falta reiniciar — no resuelve la fricción original.
- **Descartada porque:** un archivo propio leído en cada pedido (como ya hace
  `SystemsStore`) aplica el cambio sin reiniciar, que es el punto del pedido.

## Consecuencias

**Positivas**

- La fricción que motivó el pedido desaparece: cambiar la ruta de ATTRACT es un campo y
  un botón "Guardar", sin editar archivos ni reiniciar.
- Un solo patrón de store para configuración no sensible (`sistemas.json`,
  `configuracion.json`), consistente con [`ADR-0008`](0008-persistencia-en-archivos.md).
- Las credenciales no ganan una segunda ruta de exposición.

**Coste asumido**

- `COINDOOR_ATTRACT_DIR` deja de leerse: quien ya la tenía en su `.env` tiene que
  cargarla una vez más desde la pantalla. Aceptable porque el ADR que la introdujo es de
  esta misma sesión de trabajo, sin uso real todavía.
- Dos archivos de configuración (`.env` para secretos, `configuracion.json` para el
  resto) en vez de uno. Es el costo de no mezclar ambos tipos de dato.

**Qué habría que revisar si esto se replantea**

- Si aparecen varios campos no sensibles con relaciones entre sí (no solo valores
  sueltos), puede que `configuracion.json` necesite su propia migración de versión más
  allá del `version: 1` genérico de hoy.
- Si se pide editar credenciales desde la UI, es un ADR nuevo — el argumento de
  exposición de este documento tendría que revisarse explícitamente, no asumirse
  superado.

## Referencias

- [`ADR-0021`](0021-instalar-bundle-por-subproceso.md) — por qué existe `attractDir`.
- [`ADR-0008`](0008-persistencia-en-archivos.md) — persistencia en archivos, sin base de
  datos.
- `backend/store/sistemas.py` — el patrón que este ADR reutiliza.
- `backend/CLAUDE.md` §Variables de entorno — documenta qué sigue siendo credencial.
