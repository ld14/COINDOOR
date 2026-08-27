from __future__ import annotations

from pathlib import Path

from backend.lib.media import ext_de_archivo, ext_por_magic

# Cabecera real del mp4 que sirve ArcadeDB: box de 0x20 bytes. El detector viejo
# solo aceptaba 0x18 y 0x1c, asi que este archivo se exportaba como ".bin".
MP4_ARCADEDB = b"\x00\x00\x00\x20ftypisom\x00\x00\x02\x00"
MP4_BOX_CHICO = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00"
PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
JPG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x02\x00"


def test_mp4_se_detecta_por_ftyp_sin_importar_el_tamano_del_box() -> None:
    assert ext_por_magic(MP4_ARCADEDB) == ".mp4"
    assert ext_por_magic(MP4_BOX_CHICO) == ".mp4"


def test_detecta_imagenes_y_desconoce_lo_que_no_es_media() -> None:
    assert ext_por_magic(PNG) == ".png"
    assert ext_por_magic(JPG) == ".jpg"
    assert ext_por_magic(b"<?php echo 1;") == ""
    assert ext_por_magic(b"") == ""


def test_extension_del_nombre_gana_sobre_el_contenido(tmp_path: Path) -> None:
    archivo = tmp_path / "video.mp4"
    archivo.write_bytes(MP4_ARCADEDB)
    assert ext_de_archivo(archivo, "video") == ".mp4"


def test_nombre_enganoso_cae_al_contenido(tmp_path: Path) -> None:
    # Caso Super Pang: ArcadeDB lo bajaba como ``video.php``.
    archivo = tmp_path / "video.php"
    archivo.write_bytes(MP4_ARCADEDB)
    assert ext_de_archivo(archivo, "video") == ".mp4"

    con_hash = tmp_path / "caratula.b8uycgdntcg6il6wunv8pwhajs"
    con_hash.write_bytes(PNG)
    assert ext_de_archivo(con_hash, "images") == ".png"


def test_archivo_irreconocible_o_ausente_cae_a_bin(tmp_path: Path) -> None:
    raro = tmp_path / "cosa.xyz"
    raro.write_bytes(b"no soy media")
    assert ext_de_archivo(raro, "images") == ".bin"
    assert ext_de_archivo(tmp_path / "no-existe", "images") == ".bin"
