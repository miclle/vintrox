"""Transplant the two screened BReps into the display-preserving FCStd."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

LOOP_MEMBERS = {"UnderbodyLoop0.Shape.brp", "UnderbodyLoop1.Shape.brp"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--screen", type=Path, required=True)
    args = parser.parse_args()
    candidate = args.screen / "candidate.FCStd"
    mesh = args.screen / "meshes.json"
    restored = args.screen / "display.FCStd"
    check = json.loads((args.screen / "candidate-check.json").read_text())
    old_hash = digest(candidate)
    if check["baseline_fcstd_sha256"] != digest(args.base) or check["fcstd_sha256"] != old_hash:
        raise ValueError("Build report does not match the supplied FCStd files")
    with mesh.open("rb") as stream:
        if stream.read(120).count(old_hash.encode()) != 1:
            raise ValueError("Mesh export does not match the screen FCStd")

    with ZipFile(args.base) as baseline, ZipFile(candidate) as generated:
        replacements = {name: generated.read(name) for name in LOOP_MEMBERS}
        with ZipFile(restored, "w", ZIP_DEFLATED) as output:
            for name in baseline.namelist():
                contents = replacements[name] if name in replacements else baseline.read(name)
                output.writestr(name, contents)
    with ZipFile(args.base) as baseline, ZipFile(restored) as saved:
        names = baseline.namelist()
        differences = {name for name in names if baseline.read(name) != saved.read(name)}
        if names != saved.namelist() or differences != LOOP_MEMBERS:
            raise ValueError("Restoring the display changed unexpected FCStd members")

    model_hash = digest(restored)
    with mesh.open("r+b") as stream:
        header = stream.read(120)
        stream.seek(0)
        stream.write(header.replace(old_hash.encode(), model_hash.encode()))
    check["headless_fcstd_sha256"] = old_hash
    check["fcstd_sha256"] = model_hash
    check["changed_fcstd_archive_members"] = sorted(differences)
    (args.screen / "display-check.json").write_text(json.dumps(check, indent=2) + "\n")


if __name__ == "__main__":
    main()
