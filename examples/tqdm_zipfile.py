import zipfile
from typing import IO, Literal

from tqdm import tqdm

class ZipFile(zipfile.ZipFile):
    def open(self,
             name: str | zipfile.ZipInfo,
             mode: Literal["r", "w"]="r",
             pwd: bytes | None=None,
             *,
             force_zip64: bool=False) -> IO[bytes]:
        f = super().open(name, mode, pwd=pwd, force_zip64=force_zip64)

        if mode == "r":
            if not isinstance(name, zipfile.ZipInfo):
                name = zipfile.ZipInfo(name)
            return tqdm.wrapattr(f, "read", total=name.compress_size, desc=f"Decompressing {name.filename}") # type: ignore
        elif mode == "w":
            if not isinstance(name, zipfile.ZipInfo):
                return f
            else:
                return tqdm.wrapattr(f, "write", total=name.file_size, desc=f"Compressing {name.filename}") # type: ignore
        else:
            raise ValueError('open() requires mode "r" or "w"')

if __name__ == "__main__":
    import pathlib
    import shutil

    input_path = pathlib.Path("input.txt")
    zip_path = pathlib.Path("a.zip")
    extract_dir = pathlib.Path("extract")

    extract_dir.mkdir()

    with input_path.open( "w", encoding="utf-8") as f:
        f.write("A\n" * 50 * 1024)

    with ZipFile(zip_path, "x") as zf:
        zf.write("input.txt")

    with ZipFile(zip_path, "r") as zf:
        zf.read("input.txt")
        zf.extract("input.txt", extract_dir)

    input_path.unlink()
    zip_path.unlink()
    shutil.rmtree(extract_dir)
