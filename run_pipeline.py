import subprocess
import sys

def main():
    print("Starting pipeline via wrapper...")
    proc = subprocess.run(
        [sys.executable, "main.py"],
        input="Rett Syndrome\n",
        text=True,
        capture_output=False
    )
    sys.exit(proc.returncode)

if __name__ == "__main__":
    main()
