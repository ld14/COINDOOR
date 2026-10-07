# Entrega a COINDOOR — reemplazar el `contract.json` derivado

_Para el autor: estos son los pasos para que COINDOOR deje de mantener
`contract.json` a mano, ahora que ATTRACT lo publica de verdad
([`ADR-0039`](../../decisions/0039-publicar-contrato-de-datos.md))._

## 1 · Generar el contrato real

Desde la raíz de este repo:

```bash
python -m attract.contrato D:\Juegos\COINDOOR\frontend\src\lib\domain\contract.json
```

(o sin ruta, `python -m attract.contrato`, para verlo por stdout antes de
escribirlo).

## 2 · Confirmar los cambios contra la copia vieja

La copia que COINDOOR tenía (derivada a mano el 2026-08-11) le faltaban tres
cosas, que ahora van a aparecer:

- `metadataFields.optional` suma `x-procedencia` (ADR-0026 de este repo).
- `richDataFields.optional` suma `gallery` (ADR-0030) y `guia` (ADR-0037).
- `assets.video.extensions` suma `.mov`.

Nada de esto debería romper el `contract-policy.test.ts` de COINDOOR — esos
tests comparan `fielddefs.json` **contra** `contract.json`, no al revés, así
que agregar claves nuevas al contrato no les hace fallar nada hasta que
`fielddefs.json` quiera usarlas.

## 3 · Correr los tests de paridad de COINDOOR

```bash
cd D:\Juegos\COINDOOR\frontend
npm test -- contract-policy parity
```

## 4 · Decidir si `fielddefs.json` necesita campos nuevos

`gallery`/`guia`/`x-procedencia` quedan disponibles en el contrato, pero
**no es obligatorio que COINDOOR los use ya** — son campos opcionales, un
juego sin ellos sigue siendo válido de los dos lados. Si en algún momento
COINDOOR quiere exponer un formulario para `guia` (el bloque que pide
[`027/pedido-coindoor.md`](../027-como-se-juega/pedido-coindoor.md)), ahí sí
hace falta sumarlo a `fielddefs.json` con su propia política de completitud
— eso es trabajo de COINDOOR, no de este repo.

## Mantenimiento futuro

Cada vez que ATTRACT cambie la forma del contrato (nuevo campo de
`data.json`, nuevo asset nativo, etc.), `CONTRATO_VERSION` en
`src/attract/contrato.py` sube a mano. Repetir el paso 1 y comparar la
versión es la señal de que la copia de COINDOOR quedó vieja — esa lógica de
aviso es de COINDOOR (su propio `ADR-0001`), no de este comando.
