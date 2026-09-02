import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Fix UnicodeEncodeError on Windows CI runners (e.g. GitHub Actions cp1252)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser(description="PyInstaller build script for LoL OP Checker")
    parser.add_argument(
        "--name",
        type=str,
        default="LoL-OP-Checker",
        help="出力するexeファイル名 (デフォルト: LoL-OP-Checker)"
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="コンソールウィンドウを表示する（デバッグ用。デフォルトは非表示）"
    )
    parser.add_argument(
        "--onedir",
        action="store_true",
        help="単一実行ファイルではなくフォルダ形式で出力する"
    )
    parser.add_argument(
        "--icon",
        type=str,
        default=None,
        help="アプリケーションのアイコンファイルパス (.ico)"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="ビルド前に既存の build / dist フォルダをクリーンアップする"
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    src_dir = project_root / "src"
    entry_point = src_dir / "main.py"
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"
    spec_file = project_root / f"{args.name}.spec"

    if not entry_point.exists():
        print(f"[ERROR] Entry point not found: {entry_point}", file=sys.stderr)
        sys.exit(1)

    print("========================================")
    print("  LoL OP Checker - PyInstaller Build")
    print("========================================")
    print(f"Project root:  {project_root}")
    print(f"Entry point:   {entry_point}")
    print(f"Output name:   {args.name}")
    print(f"Window mode:   {'Console' if args.console else 'GUI (No Console)'}")
    print(f"Package mode:  {'Folder (onedir)' if args.onedir else 'Single File (onefile)'}")
    print("========================================\n")

    # クリーンアップ
    if args.clean:
        print("[INFO] Cleaning up previous build artifacts...")
        if dist_dir.exists():
            shutil.rmtree(dist_dir, ignore_errors=True)
        if build_dir.exists():
            shutil.rmtree(build_dir, ignore_errors=True)
        if spec_file.exists():
            spec_file.unlink(missing_ok=True)

    # PyInstaller コマンド引数の構築
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        str(entry_point),
        "--name", args.name,
        "--paths", str(src_dir),
        "--clean",
        "--noconfirm",
        "--distpath", str(dist_dir),
        "--workpath", str(build_dir),
        "--specpath", str(project_root),
    ]

    if args.onedir:
        cmd.append("--onedir")
    else:
        cmd.append("--onefile")

    if args.console:
        cmd.append("--console")
    else:
        cmd.append("--noconsole")

    if args.icon:
        icon_path = Path(args.icon).resolve()
        if icon_path.exists():
            cmd.extend(["--icon", str(icon_path)])
        else:
            print(f"[WARN] 指定されたアイコンファイルが見つかりません: {args.icon}")

    print(f"[INFO] Running command: {' '.join(cmd)}\n")

    start_time = time.time()
    try:
        result = subprocess.run(cmd, cwd=project_root)
        elapsed_time = time.time() - start_time
        if result.returncode == 0:
            print("\n========================================")
            print("  [SUCCESS] Build completed successfully!")
            print(f"  Output directory: {dist_dir}")
            print(f"  Elapsed time:     {elapsed_time:.2f} s")
            print("========================================")
        else:
            print(f"\n[ERROR] Build failed (exit code: {result.returncode}, elapsed time: {elapsed_time:.2f} s)", file=sys.stderr)
            sys.exit(result.returncode)
    except FileNotFoundError:
        print("[ERROR] Failed to execute Python or PyInstaller.", file=sys.stderr)
        print("Install PyInstaller or run with: uv run --with pyinstaller scripts/build.py", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
