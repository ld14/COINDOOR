# Insumos del repo ATTRACT

Documentos escritos **desde y para ATTRACT**, conservados acá como material de
referencia. Definen el contrato que COINDOOR tiene que satisfacer.

## Cómo leerlos

**No son features de COINDOOR.** Están redactados con el vocabulario y la estructura
de ATTRACT: hablan de `src/attract/`, de comandos de su CLI y de sus propios ADRs. Si
un documento de acá dice "crear `src/attract/carga.py`", eso pasa en el repo ATTRACT,
no en este.

Lo que sí aportan es el **qué**: qué material necesita un juego para estar completo, en
qué orden se carga, y qué se considera válido. Eso es requisito de COINDOOR y se
traduce a features propias en `spec/features/`.

## Contenido

| Documento | Qué aporta a COINDOOR |
|---|---|
| [`ATTRAC-015-carga-guiada/spec.md`](ATTRAC-015-carga-guiada/spec.md) | Los dos ejes VÁLIDO/COMPLETO y los huecos del proceso actual. |
| [`ATTRAC-015-carga-guiada/plan.md`](ATTRAC-015-carga-guiada/plan.md) | El orden de los siete pasos de carga y sus dependencias. La tabla es la base del formulario. |
| [`ATTRAC-015-carga-guiada/tasks.md`](ATTRAC-015-carga-guiada/tasks.md) | Casos límite que valen como criterios de aceptación de COINDOOR. |

## Advertencias

- **Los enlaces internos no resuelven.** Apuntan a ADRs, guías y `docs/CONVENCION.md` del
  repo ATTRACT, que no están acá. Se leen en `../attract`, que es la referencia
  autoritativa.
- **Tienen al menos dos citas equivocadas de su propio contrato**, detectadas al
  contrastarlos con `../attract/docs/CONVENCION.md`:
  1. `plan.md` §Riesgos dice mitigar la metadata inventada "marcando procedencia
     (`CONVENCION` §3.1)". **§3.1 decide justamente no marcarla.**
  2. `plan.md` §Decisiones invoca el ADR-0004 de ATTRACT como si exigiera que toda
     identidad venga de una autoridad externa. **Ese ADR trata sobre sets merged de MAME**,
     no establece esa regla.

  Verificá contra la fuente antes de apoyarte en cualquier afirmación de estos documentos.
- **`attract carga` no existe.** Está especificado acá pero no implementado; los comandos
  reales son `doctor`, `synopsis`, `ingest`, `rasterize`, `mags` y `mcp`.
- **No editar estos archivos.** Son copia de otro repo; corregirlos acá crea una versión
  divergente. Lo que COINDOOR decide va en `spec/`.
