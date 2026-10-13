import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def check_inputs(spec):
    for entry in [spec["source"], spec["target"], spec["candidate"], *spec["context"]]:
        path = Path(entry["path"])
        if digest(path) != entry["sha256"]:
            raise ValueError(f"Version conflict: {path}")
    if spec["source"]["sha256"] is None or spec["candidate"]["sha256"] is None:
        raise ValueError("Source and candidate must exist")


def blocks(text):
    return [line.strip() for line in text.splitlines() if line.strip()]


def publish(spec):
    target = Path(spec["target"]["path"])
    candidate = Path(spec["candidate"]["path"])
    source = Path(spec["source"]["path"])
    if target.resolve() in {candidate.resolve(), source.resolve()}:
        raise ValueError("Target must differ from source and candidate")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.with_name(target.name + ".publish.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        check_inputs(spec)
        content = candidate.read_bytes()
        if hashlib.sha256(content).hexdigest() != spec["candidate"]["sha256"]:
            raise ValueError("Candidate changed during publication")
        source_blocks = blocks(source.read_text(encoding="utf-8"))
        target_blocks = blocks(content.decode("utf-8"))
        if len(source_blocks) != len(target_blocks):
            raise ValueError("Source/candidate block count differs")
        baseline = blocks(target.read_text(encoding="utf-8")) if target.exists() else None
        allowed = spec.get("allowed_blocks")
        if baseline is not None and allowed is not None:
            if len(baseline) != len(target_blocks):
                raise ValueError("Existing target/candidate block count differs")
            changed = {index for index, pair in enumerate(zip(baseline, target_blocks))
                       if pair[0] != pair[1]}
            if not changed.issubset(set(allowed)):
                raise ValueError("Candidate edits blocks outside the approved scope")
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            if target.exists():
                temporary.chmod(target.stat().st_mode & 0o777)
            check_inputs(spec)
            os.replace(temporary, target)
            temporary = None
            published = digest(target)
            if published != spec["candidate"]["sha256"]:
                raise ValueError("Target changed immediately after publication")
            return {"target": str(target), "previous_sha256": spec["target"]["sha256"],
                    "published_sha256": published, "blocks": len(target_blocks)}
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Publish a coordinator-approved translation candidate")
    parser.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    try:
        result = publish(spec)
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()