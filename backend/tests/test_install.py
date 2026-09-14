from __future__ import annotations

import stat
from pathlib import Path

import pytest

from backend.bundle.install import install_bundle


def _script(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "install-coindoor-wsl.sh"
    path.write_text(f"#!/usr/bin/env bash\n{body}\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


def test_install_bundle_ok_cuando_el_script_sale_cero(tmp_path: Path) -> None:
    script = _script(tmp_path, 'echo "instalado: $1 -> $2"; exit 0')
    bundle = tmp_path / "juego.coindoor.zip"
    bundle.write_bytes(b"zip")

    resultado = install_bundle(script, bundle, tmp_path / "library")

    assert resultado["ok"] is True
    assert resultado["estado"] == "instalado"
    assert "instalado:" in resultado["salida"]


def test_install_bundle_falla_con_salida_del_script(tmp_path: Path) -> None:
    script = _script(tmp_path, 'echo "error: no existe el paquete" >&2; exit 1')
    bundle = tmp_path / "juego.coindoor.zip"
    bundle.write_bytes(b"zip")

    resultado = install_bundle(script, bundle, tmp_path / "library")

    assert resultado["ok"] is False
    assert resultado["estado"] == "error"
    assert "no existe el paquete" in resultado["salida"]


def test_install_bundle_script_inexistente_no_lanza(tmp_path: Path) -> None:
    resultado = install_bundle(
        tmp_path / "no-existe.sh", tmp_path / "juego.coindoor.zip", tmp_path / "library"
    )

    assert resultado["ok"] is False
    assert resultado["estado"] == "no_disponible"


@pytest.mark.parametrize("exit_code", [0, 1])
@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_install_bundle_salida_no_utf8_no_cambia_resultado(
    tmp_path: Path, exit_code: int, stream: str
) -> None:
    redirect = " >&2" if stream == "stderr" else ""
    script = _script(
        tmp_path,
        rf"printf 'instalaci\363n: v\303\241lida\n'{redirect}; exit {exit_code}",
    )

    resultado = install_bundle(script, tmp_path / "juego.zip", tmp_path / "library")

    assert resultado == {
        "ok": exit_code == 0,
        "estado": "instalado" if exit_code == 0 else "error",
        "salida": "instalaci\ufffdn: válida\n",
    }
