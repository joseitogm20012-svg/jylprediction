import asyncio, sys
from pathlib import Path

async def main():
    script_path = Path(r"C:\Users\Equipo\Desktop\predecirv2\data\fetch_latest_results.py")
    cwd = Path(r"C:\Users\Equipo\Desktop\predecirv2")

    print(f"Script exists: {script_path.exists()}")
    print(f"Cwd exists: {cwd.exists()}")
    print(f"Python: {sys.executable}")

    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, str(script_path),
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        print(f"Process started, pid={process.pid}")

        count = 0
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            count += 1

        await process.wait()
        print(f"Lines: {count}, exit_code: {process.returncode}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

asyncio.run(main())
