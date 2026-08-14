# Decisiones de arquitectura (ADRs)

Registro de decisiones técnicas **con las alternativas que se descartaron**.

## Por qué existe

El código dice *qué* hace. El ADR dice *por qué no hace otra cosa*. Sin él, dentro
de seis meses alguien —tú, o Claude— vuelve a proponer justo lo que ya descartaste.

## Reglas

- **Un ADR por decisión.** Numerado, secuencial, un número nunca se reutiliza.
- **Los ADRs no se editan.** Si cambias de opinión, creas uno nuevo y marcas el
  anterior con `superseded-by: NNNN`. Esa inmutabilidad es lo que les da valor:
  un ADR editado es documentación; un ADR superseded es historia.
- **Solo va aquí lo que tuvo alternativas reales.** Si no descartaste nada, es
  una convención: va en `../constitution/`.
- **Al aceptarse**, la conclusión sube a `../constitution/` (y si descarta algo,
  a §Límites duros de `tech-stack.md`). El ADR conserva el *porqué*.
- **Si una decisión se revierte durante la implementación**, es un ADR — no un
  párrafo añadido al `plan.md` de la feature.

## Crear uno

```
/new-adr <título de la decisión>
```

## Índice

| # | Título | Estado | Fecha |
|---|---|---|---|
| [0001](0001-contrato-coindoor-attract.md) | Contrato de ATTRACT como dato versionado + doble validación | accepted | 2026-08-10 |
| [0002](0002-procedencia-interna.md) | La procedencia de cada campo vive solo en COINDOOR | accepted | 2026-08-10 |
| [0003](0003-bundle-por-juego.md) | Cada juego se entrega como un `.zip` instalable y compartible | accepted | 2026-08-10 |
| [0004](0004-coindoor-fuente-identidad-no-mame.md) | COINDOOR es la fuente de identidad de las plataformas sin catálogo | accepted | 2026-08-10 |
| [0005](0005-contrato-vendoreado-vs-politica-propia.md) | El contrato vendoreado y la política de completitud son archivos distintos | accepted | 2026-08-11 |
| [0006](0006-fuentes-externas-multiproveedor.md) | Varios proveedores por campo, con resultados parciales | superseded por [0013](0013-sin-scraping-ni-catalogo-pago.md) | 2026-08-11 |
| [0007](0007-fastapi-como-framework-backend.md) | FastAPI como framework de backend, no Django ni Flask | accepted | 2026-08-11 |
| [0008](0008-persistencia-en-archivos.md) | Un `game.json` por juego, sin base de datos | accepted | 2026-08-11 |
| [0009](0009-proceso-local-en-loopback.md) | Un proceso local en loopback, que sustituye a la autenticación | accepted | 2026-08-11 |
| [0010](0010-jobs-en-proceso.md) | Trabajos largos en hilos del propio proceso, sin cola ni worker | accepted | 2026-08-11 |
| [0011](0011-fielddefs-json-compartido.md) | La política de completitud es JSON compartido entre TS y Python | accepted | 2026-08-11 |
| [0012](0012-verificacion-attract-por-subproceso.md) | Verificar el export con `attract doctor` por subproceso, sin parsear | accepted | 2026-08-11 |
| [0013](0013-sin-scraping-ni-catalogo-pago.md) | Sugerencias sin scraping ni catálogos de terceros — solo IA y referencias | accepted | 2026-08-13 |

Los seis últimos salen del análisis de arquitectura de
[`docs/arquitectura/`](../../docs/arquitectura/README.md), que conserva la comparación
completa de alternativas con sus criterios.
