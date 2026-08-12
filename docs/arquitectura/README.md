# Análisis de arquitectura — agosto 2026

Análisis técnico completo del proyecto y elección del stack de front-end y back-end, con
la comparación de alternativas que no cabe en un ADR.

| Formato | Dónde |
|---|---|
| Documento completo, con formato | [`technical-architecture-recommendation.html`](technical-architecture-recommendation.html) — abrilo en el navegador |
| Misma versión, en línea | <https://claude.ai/code/artifact/12a32ee0-b434-4f55-a97a-67ce03f5cab8> |

**Qué es y qué no.** Es el trabajo previo del que salieron los ADRs
[0007](../../spec/decisions/0007-fastapi-como-framework-backend.md) a
[0012](../../spec/decisions/0012-verificacion-attract-por-subproceso.md). **Las decisiones
mandan desde los ADRs y desde `spec/constitution/`, no desde acá.** Este documento se
conserva porque contiene la comparación aplicada —criterio por criterio, alternativa por
alternativa— que el formato de ADR resume.

No se edita. Si una decisión cambia, se supersede su ADR.

---

## Qué se decidió

| Capa | Elección | ADR |
|---|---|---|
| Frontend | Vite + React 18 + TS `strict` + TanStack Query v5, sin librerías de componentes | — (ya estaba en la constitución) |
| Framework backend | FastAPI + Uvicorn + Pydantic v2 | [0007](../../spec/decisions/0007-fastapi-como-framework-backend.md) |
| Persistencia | **Sin base de datos.** Un `game.json` por juego | [0008](../../spec/decisions/0008-persistencia-en-archivos.md) |
| Ejecución y seguridad | Un proceso en `127.0.0.1`, que sirve API + frontend | [0009](../../spec/decisions/0009-proceso-local-en-loopback.md) |
| Trabajos largos | `ThreadPoolExecutor` en proceso, cancelable | [0010](../../spec/decisions/0010-jobs-en-proceso.md) |
| Política de completitud | `fielddefs.json`, compartido entre TS y Python | [0011](../../spec/decisions/0011-fielddefs-json-compartido.md) |
| Verificación con ATTRACT | Subproceso, código de salida, sin parsear | [0012](../../spec/decisions/0012-verificacion-attract-por-subproceso.md) |
| Infraestructura | **Ninguna.** Sin Docker, Redis, colas, storage, CDN ni monitoring | 0009, 0010 |

---

## Lo que hay que arrastrar del análisis

Dos cosas del documento **no** quedaron cerradas en un ADR y siguen pendientes.

### Contradicciones del paquete de diseño

`docs/claude_diseño/data-model.md` §1 y §6 son anteriores a los deltas y a las features
001–002. El resumen accionable está en
[`tech-stack.md`](../../spec/constitution/tech-stack.md) §Contradicciones abiertas; el
detalle, con qué interpretación es más probable y por qué, en §16.1 del documento.

Dos siguen **sin decidir** y hacen falta antes de la feature 001:

- **`identitySource` tiene dos valores y la realidad tiene tres.** Una identidad resuelta
  por ScreenScraper por hash es `catalog` en la UI pero tiene que exportarse como
  `declarada`, porque `install` solo sabe consultar MAME.
- **`players` es `string` en la UI y número en el bundle.** `"1-2"` no es un entero.

### Dos hallazgos en el código de ATTRACT

Verificados leyendo `src/attract/doctor.py`, no la documentación. Los dos afectan a la
feature [001](../../spec/features/001-export-bundle/spec.md):

1. **`attract doctor` no tiene salida legible por máquina.** Imprime texto y devuelve
   `0` o `1`. Resuelto en
   [`ADR-0012`](../../spec/decisions/0012-verificacion-attract-por-subproceso.md): se usa
   el código de salida y se muestra el `stdout` literal, sin parsear.
2. **El staging con forma de bundle no cubre el bloque `game:`.** `chk_metadata` solo
   corre sobre archivos `*.pegasus.txt`, y el bundle no lleva ninguno por diseño. Por eso
   el staging se arma **con forma de librería**, con un `metadata.pegasus.txt` temporal
   que se descarta antes de comprimir. Si no, `verificado: true` promete más de lo que
   entrega.

---

## Índice del documento

1. Executive Summary · 2. Project Understanding · 3. Functional Requirements ·
4. Non-Functional Requirements · 5. Recommended Stack · 6. Architecture Overview ·
7. Frontend Architecture · 8. Backend Architecture · 9. Data Architecture ·
10. Authentication & Authorization · 11. Security Considerations · 12. API Strategy ·
13. Testing Strategy · 14. Infrastructure & Deployment · **15. Alternatives Considered** ·
**16. Risks & Trade-offs** · **17. Open Questions** · 18. Final Recommendation

Las tres en negrita son las que no se pueden reconstruir desde los ADRs.
