"""Lost & Found dataset access (Zenodo record 14967441, CC BY 4.0).

Never unzips whole archives: the .vrs raw recordings make up most of the 30 GB.
"""
from __future__ import annotations

import fnmatch
import hashlib
import subprocess
import zipfile
from pathlib import Path

RECORD = "14967441"
FILES = {
    "Final_Scan.zip": "0819d8f2b6e91f1dff34780086ead802",
    "Final_Dataset.zip": "14940440b31e3cb957419e73f0099246",
}
# Small files only. Raw .vrs recordings are excluded by construction.
WANTED = ("*.csv", "*.npy", "*.json")


def url(name: str) -> str:
    return f"https://zenodo.org/api/records/{RECORD}/files/{name}/content"


def md5(path: str | Path, chunk: int = 1 << 24) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        while block := f.read(chunk):
            h.update(block)
    return h.hexdigest()


def download(name: str, dest_dir: str | Path = "data/zenodo") -> Path:
    """Resumable download followed by an MD5 check. Raises if the checksum differs."""
    dest = Path(dest_dir) / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["curl", "-L", "-C", "-", "-s", "--fail", "-o", str(dest), url(name)], check=True)
    got = md5(dest)
    if got != FILES[name]:
        raise RuntimeError(f"{name}: md5 {got} != expected {FILES[name]}")
    return dest


def list_zip(path: str | Path) -> list[zipfile.ZipInfo]:
    with zipfile.ZipFile(path) as z:
        return z.infolist()


def select_members(infos: list[zipfile.ZipInfo], recordings: set[str] | None = None,
                   patterns: tuple[str, ...] = WANTED) -> list[str]:
    """Names of small files to extract, optionally restricted to some recording folders."""
    out = []
    for i in infos:
        if i.is_dir() or i.filename.endswith(".vrs"):
            continue
        if not any(fnmatch.fnmatch(i.filename, p) for p in patterns):
            continue
        if recordings is not None and not any(f"/{r}/" in f"/{i.filename}" for r in recordings):
            continue
        out.append(i.filename)
    return out


def extract_members(path: str | Path, members: list[str], out_dir: str | Path) -> None:
    with zipfile.ZipFile(path) as z:
        for m in members:
            z.extract(m, out_dir)
