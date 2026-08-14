import subprocess
import sys

import os

def main():
    print("Starting pipeline via wrapper...")
    env = dict(os.environ)
    bin_dir = os.path.dirname(sys.executable)
    if bin_dir:
        env["PATH"] = f"{bin_dir}:{env.get('PATH', '')}"

    proc = subprocess.run(
        [sys.executable, "main.py"],
        input="Rett Syndrome\n",
        text=True,
        capture_output=False,
        env=env
    )
    sys.exit(proc.returncode)

if __name__ == "__main__":
    main()
