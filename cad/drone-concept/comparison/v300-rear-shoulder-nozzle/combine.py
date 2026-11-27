"""Combine independently checked changes to disjoint v292 parts."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base", "mesh", "shoulders", "leaves", "checks", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    base_hash = digest(args.base)
    mesh = json.loads(args.mesh.read_text())
    assert mesh["fcstd_sha256"] == base_hash
    replacements = {}
    mesh_replacements = {}
    inputs = []
    proof = json.loads(args.checks.read_text())
    assert proof["baseline_fcstd_sha256"] == base_hash
    member_hashes = proof["changed_member_sha256"]
    for candidate in (args.shoulders, args.leaves):
        model = candidate / "candidate.FCStd"
        model_hash = digest(model)
        with ZipFile(args.base) as source, ZipFile(model) as archive:
            if archive.namelist() != source.namelist():
                raise ValueError("Candidate archive members differ from v292")
            members = {name for name in archive.namelist() if archive.read(name) != source.read(name)}
            if not members or members.intersection(replacements) or not members <= member_hashes.keys():
                raise ValueError("Unexpected candidate changes")
            for name in members:
                payload = archive.read(name)
                if hashlib.sha256(payload).hexdigest() != member_hashes[name]:
                    raise ValueError(f"Replayed shape differs from the evaluated BRep: {name}")
                replacements[name] = payload
        local_mesh = json.loads((candidate / "meshes.json").read_text())
        assert local_mesh["fcstd_sha256"] == model_hash
        mesh_replacements.update({item["name"]: item for item in local_mesh["objects"]
                                  if item["name"] + ".Shape.brp" in members})
        inputs.append(model_hash)
    if replacements.keys() != member_hashes.keys():
        raise ValueError("Missing evaluated BRep changes")

    args.output.mkdir(parents=True)
    output = args.output / "candidate.FCStd"
    with ZipFile(args.base) as source, ZipFile(output, "w", ZIP_DEFLATED) as model:
        assert replacements.keys() <= set(source.namelist())
        for name in source.namelist():
            content = replacements[name] if name in replacements else source.read(name)
            model.writestr(name, content)
    mesh["fcstd_sha256"] = digest(output)
    mesh["objects"] = [mesh_replacements.get(item["name"], item) for item in mesh["objects"]]
    (args.output / "meshes.json").write_text(json.dumps(mesh, separators=(",", ":")))
    report = {
        "baseline_fcstd_sha256": base_hash,
        "fcstd_sha256": mesh["fcstd_sha256"],
        "input_fcstd_sha256": inputs,
        "changed_objects": sorted(mesh_replacements),
        "changed_archive_members": sorted(replacements),
    }
    (args.output / "combined.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
