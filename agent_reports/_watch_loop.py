"""Watch loop for the 9pm presentation PDF regenerator daemon."""
import os
import time
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path("/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185")
REPORTS = ROOT / "agent_reports"
LOG = REPORTS / "_regen_log.txt"
PDF = REPORTS / "9pm_presentation.pdf"

# Deadline: 21:00:00 PDT today. Stop regen at 20:59:30 to be safe.
END_UNIX = 1778558400          # 21:00:00 PDT 2026-05-11
LAST_SAFE_BUILD = END_UNIX - 30  # 20:59:30


def log(msg):
    stamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{stamp}] {msg}\n"
    with open(LOG, "a") as f:
        f.write(line)
    print(line.rstrip())


def snapshot_dir():
    """Return a frozenset of (name, mtime, size) tuples for files in agent_reports/ (and figs)."""
    out = []
    for p in sorted(REPORTS.iterdir()):
        if p.is_file():
            st = p.stat()
            out.append((p.name, int(st.st_mtime), st.st_size))
    figs = REPORTS / "figs"
    if figs.is_dir():
        for p in sorted(figs.iterdir()):
            if p.is_file():
                st = p.stat()
                out.append(("figs/" + p.name, int(st.st_mtime), st.st_size))
    return frozenset(out)


def build_pdf():
    """Run make_pdf.py with the project venv. Falls back to last good PDF on crash."""
    backup = PDF.with_suffix(".bak.pdf")
    if PDF.exists():
        try:
            backup.write_bytes(PDF.read_bytes())
        except Exception as e:
            log(f"backup failed: {e}")
    cmd = [
        "bash", "-c",
        "cd " + str(ROOT) + " && source .venv/bin/activate && "
        "python agent_reports/make_pdf.py",
    ]
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    dt = time.time() - t0
    if res.returncode != 0:
        log(f"BUILD FAILED ({dt:.1f}s) rc={res.returncode}")
        log("stderr: " + res.stderr.strip().replace("\n", " | ")[:500])
        if backup.exists():
            PDF.write_bytes(backup.read_bytes())
            log("restored from backup")
        return False
    log(f"build ok ({dt:.1f}s) -> {PDF.name} ({PDF.stat().st_size//1024} KB)")
    return True


def main():
    log("daemon start")
    known = snapshot_dir()
    last_build = time.time()
    log(f"initial known files: {len(known)}")

    while time.time() < LAST_SAFE_BUILD:
        remaining = LAST_SAFE_BUILD - time.time()
        if remaining < 5:
            break
        time.sleep(min(45, remaining))
        if time.time() >= LAST_SAFE_BUILD:
            break
        cur = snapshot_dir()
        diff = cur ^ known
        if diff:
            new_names = sorted({n for (n, _, _) in (cur - known)})
            log(f"change detected: {len(diff)} entries; new/modified: {new_names[:6]}")
            if build_pdf():
                known = cur
                last_build = time.time()
        elif (time.time() - last_build) > 150:
            log("periodic regen (no file changes)")
            if build_pdf():
                last_build = time.time()

    # Final regen: always run one more right before deadline
    if time.time() < END_UNIX - 5:
        log("FINAL regen before deadline")
        build_pdf()
    log(f"daemon stop. final size: {PDF.stat().st_size//1024} KB")


if __name__ == "__main__":
    main()
