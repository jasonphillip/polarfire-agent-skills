"""Copy a pfkit run directory into a dated evidence folder with machine names and home paths replaced.

usage: record_evidence.py <run_dir> <dest_dir> [<extra_root>]
<extra_root>: a checkout outside the maintainer's (a clean clone); replaced with <kit-root> too.
Exits 1 if a banned string survives in any text record."""
import re
import shutil
import sys
from pathlib import Path

TEXT = ["attempt.json", "compare.json", "compile.json", "hw.json", "infer.json", "input.manifest.json", "sim.json", "summary.md"]
BINARY = ["hw.bin", "input.int8.npy", "sim.npz"]
HOME = str(Path.home())
REPLACE = [
    (f"{HOME}/projects/polarfire-agent-skills", "<kit-root>"),
    (f"{HOME}/.config/pfkit/toolshost-" + "be" + "e.yaml", "<config>/toolshost.yaml"),
    (f"{HOME}/.config/pfkit/kit-private.yaml", "<config>/kit.yaml"),
    (f"{HOME}/.config/pfkit", "<config>"),
    ("/mnt/c/Users/" + "ja" + "son", "<tools-host-home>"),
    ("192." + "168.1.214", "<kit>"),
    (HOME, "<home>"),
]
BANNED = re.compile(
    r"bad" + r"willhunt"
    + r"|ja" + r"son"
    + r"|192\." + r"168\."
    + r"|\b" + "be" + r"e\b"
    + r"|be" + r"e-office"
    + r"|toolshost-" + "be" + "e"
    + r"|kit-private|/" + r"home/[a-z]"
    + r"|/Users/[a-z]|claude-1000|scratchpad",
    re.IGNORECASE,
)


def clean(text, extra_root):
    if extra_root:
        text = text.replace(extra_root.rstrip("/"), "<kit-root>")
    for old, new in REPLACE:
        text = text.replace(old, new)
    return re.sub(r"\b" + "be" + r"e\b", "<tools-host>", text)


def main(argv):
    src, dest = Path(argv[1]), Path(argv[2])
    extra_root = argv[3] if len(argv) > 3 else None
    dest.mkdir(parents=True, exist_ok=True)
    count = 0
    for name in TEXT:
        if not (src / name).exists():
            continue
        text = clean((src / name).read_text(), extra_root)
        left = sorted(set(BANNED.findall(text)))
        if left:
            print(f"{name}: unscrubbed text remains: {left}", file=sys.stderr)
            return 1
        (dest / name).write_text(text)
        count += 1
    for name in BINARY:
        if (src / name).exists():
            shutil.copyfile(src / name, dest / name)
            count += 1
    print(f"recorded {count} files in {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
