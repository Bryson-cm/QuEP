"""
Utilities for running QuEP single-particle debug cases in parallel on a multi-core PC.

This module is intended for the workflow where a larger case is split into several
single-particle input files, for example:

    input/Zeus2e16_p00.py
    input/Zeus2e16_p01.py
    input/Zeus2e16_p02.py

Each input file is run as an independent subprocess using:

    python main.py input.Zeus2e16_p00
    python main.py input.Zeus2e16_p01
    ...

This is useful for debugging because each particle trajectory produces its own
output and debug object, and a failed trajectory does not necessarily prevent the
others from running.

Typical usage from a small case-study script:

    from include.parallel_case_runner_pc import run_debug_cases

    run_debug_cases(
        core_name="Zeus2e16",
        max_parallel=5,
    )

This automatically finds all files matching:

    input/Zeus2e16_p*.py

Notes
-----
This module controls subprocess-level parallelism only. It does not control any
multiprocessing pool that may exist inside main.py. For the intended
single-particle debug inputs, main.py should not normally create a multiprocessing
pool, so the relevant parallelism is simply the number of subprocesses launched
at the same time.

The module assumes it is being used inside the QuEP repository, whose root
directory contains main.py.
"""

from pathlib import Path
import os
import re
import subprocess
import sys
import time


def find_project_root():
    """
    Find the QuEP project root by walking upward until main.py is found.
    """
    project_root = Path.cwd().resolve()

    while not (project_root / "main.py").exists():
        if project_root == project_root.parent:
            raise RuntimeError("Could not find QuEP project root containing main.py.")
        project_root = project_root.parent

    return project_root


def find_input_modules(core_name, project_root):
    """
    Find input modules matching:

        input/<core_name>_p00.py
        input/<core_name>_p01.py
        input/<core_name>_p02.py
        ...

    Parameters
    ----------
    core_name : str
        Base name of the input files, e.g. "Zeus2e16" or "ATF2e16".

    project_root : pathlib.Path
        Path to the QuEP project root.

    Returns
    -------
    list[str]
        Sorted list of importable input module names.
    """
    input_dir = project_root / "input"

    pattern = re.compile(rf"^{re.escape(core_name)}_p(\d+)\.py$")

    matches = []

    for path in input_dir.glob(f"{core_name}_p*.py"):
        match = pattern.match(path.name)

        if match:
            particle_index = int(match.group(1))
            module_name = f"input.{path.stem}"
            matches.append((particle_index, module_name))

    matches.sort(key=lambda item: item[0])

    if not matches:
        raise RuntimeError(
            f"No input files found matching input/{core_name}_p*.py"
        )

    indices = [index for index, _ in matches]
    expected = list(range(indices[0], indices[-1] + 1))
    missing = sorted(set(expected) - set(indices))

    if missing:
        print(
            "Warning: missing particle indices:",
            ", ".join(f"p{i:02d}" for i in missing),
        )

    return [module_name for _, module_name in matches]


def run_debug_cases(core_name, max_parallel=None):
    """
    Run all available single-particle debug cases matching:

        input/<core_name>_p*.py

    Each matching input file is run as an independent subprocess using:

        python main.py input.<core_name>_pXX

    Parameters
    ----------
    core_name : str
        Base name of the input files, without the particle suffix.
        For example, use "Zeus2e16" for files named:

            input/Zeus2e16_p00.py
            input/Zeus2e16_p01.py

    max_parallel : int or None, optional
        Maximum number of subprocesses to keep active at the same time.

        If None, all matching input files are launched at once.

        The number of input files may exceed max_parallel. The runner will keep
        at most max_parallel jobs active at a time. When one job finishes, the
        next file in the list is started.

    Raises
    ------
    RuntimeError
        If no matching input files are found, or if one or more subprocesses
        exits with a nonzero return code.
    """
    project_root = find_project_root()

    os.chdir(project_root)

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    print("Working directory set to:", project_root)

    input_modules = find_input_modules(core_name, project_root)

    if max_parallel is None:
        max_parallel = len(input_modules)

    if max_parallel < 1:
        raise ValueError("max_parallel must be at least 1.")

    print("\nInput modules found:")
    for module in input_modules:
        print(" ", module)

    print(f"\nMaximum number of simultaneous jobs: {max_parallel}")

    running = []
    failed = []

    def start_job(module):
        """
        Start one QuEP subprocess for a single input module.
        """
        cmd = [sys.executable, "main.py", module]

        print(f"\nStarting: {' '.join(cmd)}", flush=True)

        p = subprocess.Popen(
            cmd,
            cwd=project_root,
        )

        print(f"  PID = {p.pid}", flush=True)

        return module, p

    # Launch jobs while keeping no more than max_parallel active at once.
    for module in input_modules:
        while len(running) >= max_parallel:
            still_running = []

            for running_module, p in running:
                returncode = p.poll()

                if returncode is None:
                    still_running.append((running_module, p))

                elif returncode == 0:
                    print(f"Finished successfully: {running_module}", flush=True)

                else:
                    print(
                        f"FAILED: {running_module} with return code {returncode}",
                        flush=True,
                    )
                    failed.append(running_module)

            running = still_running

            if len(running) >= max_parallel:
                time.sleep(5)

        running.append(start_job(module))

    print("\nAll requested jobs have been launched.\n", flush=True)

    # Wait for remaining jobs to finish.
    while running:
        still_running = []

        for module, p in running:
            returncode = p.poll()

            if returncode is None:
                still_running.append((module, p))

            elif returncode == 0:
                print(f"Finished successfully: {module}", flush=True)

            else:
                print(f"FAILED: {module} with return code {returncode}", flush=True)
                failed.append(module)

        running = still_running

        if running:
            time.sleep(5)

    if failed:
        raise RuntimeError(f"{len(failed)} jobs failed: {failed}")

    print("\nAll jobs finished successfully.")