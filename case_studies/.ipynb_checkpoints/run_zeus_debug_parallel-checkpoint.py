from pathlib import Path
import subprocess
import sys
import time

project_root = Path.cwd().resolve()

while not (project_root / "main.py").exists():
    if project_root == project_root.parent:
        raise RuntimeError("Could not find QuEP project root containing main.py.")
    project_root = project_root.parent

os.chdir(project_root)

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("Working directory set to:", project_root)

input_modules = [
    "input.Zeus2e16_p00",
    "input.Zeus2e16_p01",
    "input.Zeus2e16_p02",
    "input.Zeus2e16_p03",
    "input.Zeus2e16_p04",
]

processes = []

for module in input_modules:
    cmd = [sys.executable, "main.py", module]

    print(f"Starting: {' '.join(cmd)}", flush=True)

    p = subprocess.Popen(
        cmd,
        cwd=project_root,
    )

    print(f"  PID = {p.pid}", flush=True)
    processes.append((module, p))

print("\nAll jobs launched.\n", flush=True)

# Wait for all processes to finish.
failed = []

while processes:
    still_running = []

    for module, p in processes:
        returncode = p.poll()

        if returncode is None:
            still_running.append((module, p))
        else:
            if returncode == 0:
                print(f"Finished successfully: {module}", flush=True)
            else:
                print(f"FAILED: {module} with return code {returncode}", flush=True)
                failed.append(module)

    processes = still_running
    time.sleep(5)

if failed:
    raise RuntimeError(f"{len(failed)} jobs failed: {failed}")

print("All jobs finished successfully.")