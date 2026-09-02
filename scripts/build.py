import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

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
        print(f"[ERROR] エントリーポイントが見つかりません: {entry_point}", file=sys.stderr)
        sys.exit(1)

    print("========================================")
    print("  LoL OP Checker - PyInstaller Build")
    print("========================================")
    print(f"プロジェクトルート: {project_root}")
    print(f"エントリーポイント: {entry_point}")
    print(f"出力ファイル名:     {args.name}")
    print(f"ウィンドウモード:   {'コンソール表示' if args.console else 'GUI (コンソール非表示)'}")
    print(f"パッケージング形式: {'フォルダ (onedir)' if args.onedir else '単一ファイル (onefile)'}")
    print("========================================\n")

    # クリーンアップ
    if args.clean:
        print("[INFO] 過去のビルド成果物を削除中...")
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

    print(f"[INFO] 実行コマンド: {' '.join(cmd)}\n")

    start_time = time.time()
    try:
        result = subprocess.run(cmd, cwd=project_root)
        elapsed_time = time.time() - start_time
        if result.returncode == 0:
            print("\n========================================")
            print("  [SUCCESS] ビルドが正常に完了しました！")
            print(f"  出力先:     {dist_dir}")
            print(f"  所要時間:   {elapsed_time:.2f} 秒")
            print("========================================")
        else:
            print(f"\n[ERROR] ビルド中にエラーが発生しました (終了コード: {result.returncode}, 所要時間: {elapsed_time:.2f} 秒)", file=sys.stderr)
            sys.exit(result.returncode)
    except FileNotFoundError:
        print("[ERROR] PythonまたはPyInstallerの実行に失敗しました。", file=sys.stderr)
        print("以下のコマンドでPyInstallerをインストール、または uv で実行してください:", file=sys.stderr)
        print("  uv run --with pyinstaller scripts/build.py", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
