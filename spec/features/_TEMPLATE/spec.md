# NNN · <Nombre de la feature>

**Estado:** borrador   <!-- borrador | aprobada | en curso | implementada -->

<!-- GUÍA: el spec responde QUÉ y POR QUÉ. Nada de implementación: eso es plan.md.
No escribas plan.md hasta que este documento esté cerrado. Objetivo: ~30 líneas. -->

## Qué hace

<Qué recibe, qué produce, y qué queda explícitamente fuera de su responsabilidad
aunque parezca cercano (enlaza a la feature que sí lo cubre).>

## Por qué

<Qué se desbloquea con esto. Si nace de un problema detectado en producción o en
otra feature, dilo y enlaza.>

## Criterios de aceptación

<!-- Verificables por un test o por inspección directa. Si no sabrías escribir el
test, el criterio está mal redactado. -->

- [ ] Dado <contexto>, cuando <acción>, entonces <resultado observable>.
- [ ] <Caso límite: entrada vacía, corrupta, ausente>.
- [ ] <Qué NO debe romperse: el fallo produce error explícito, no salida parcial>.

## Fuera de alcance

- <Cosa cercana que NO incluye> — eso es la feature [NNN-<slug>](../NNN-<slug>/spec.md).
- <Cosa que alguien podría asumir y no está>.
