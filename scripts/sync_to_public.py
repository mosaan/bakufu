#!/usr/bin/env python3
"""
公開用リポジトリ同期スクリプト

内部開発リポジトリから公開用リポジトリへファイルを選択的にコピーします。
設定ファイル(public_sync_config.yaml)に基づいて動作します。
"""

import argparse
import fnmatch
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml


class PublicRepoSyncer:
    """公開用リポジトリ同期クラス"""

    def __init__(self, config_path: Path, source_dir: Path, target_dir: Path):
        self.config_path = config_path
        self.source_dir = source_dir.resolve()
        self.target_dir = target_dir.resolve()
        self.config = self._load_config()
        self.logger = self._setup_logger()

    def _load_config(self) -> dict[str, Any]:
        """設定ファイルを読み込む"""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_path}") from None
        except yaml.YAMLError as e:
            raise ValueError(f"設定ファイルの解析に失敗しました: {e}") from e

    def _setup_logger(self) -> logging.Logger:
        """ロガーを設定する"""
        logger = logging.getLogger("public_sync")
        logger.setLevel(
            getattr(logging, self.config.get("sync_settings", {}).get("log_level", "INFO"))
        )

        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def _matches_pattern(self, file_path: Path, patterns: list[str]) -> bool:
        """ファイルパスがパターンにマッチするかチェック"""
        relative_path = file_path.relative_to(self.source_dir)
        relative_path_str = str(relative_path).replace("\\", "/")  # Windows対応

        for pattern in patterns:
            # fnmatchを使用したグロブパターンマッチング
            if fnmatch.fnmatch(relative_path_str, pattern):
                return True
            # パターンがディレクトリの場合、その下のファイルもマッチ
            if pattern.endswith("/**") and relative_path_str.startswith(pattern[:-3]):
                return True

        return False

    def _should_include_file(self, file_path: Path) -> bool:
        """ファイルを含めるべきかどうか判定"""
        include_patterns = self.config.get("include_patterns", [])
        exclude_patterns = self.config.get("exclude_patterns", [])

        # まず除外パターンをチェック
        if self._matches_pattern(file_path, exclude_patterns):
            return False

        # 次に含めるパターンをチェック
        return self._matches_pattern(file_path, include_patterns)

    def _collect_files_to_sync(self) -> list[Path]:
        """同期対象のファイルを収集"""
        files_to_sync = []

        self.logger.info(f"ソースディレクトリをスキャン中: {self.source_dir}")

        for root, dirs, files in os.walk(self.source_dir):
            root_path = Path(root)

            # ディレクトリレベルでの除外チェック
            dirs_to_remove = []
            for dir_name in dirs:
                dir_path = root_path / dir_name
                if not self._should_include_file(dir_path):
                    dirs_to_remove.append(dir_name)

            # 除外ディレクトリを削除(os.walkが再帰しないようにする)
            for dir_name in dirs_to_remove:
                dirs.remove(dir_name)

            # ファイルレベルでのチェック
            for file_name in files:
                file_path = root_path / file_name
                if self._should_include_file(file_path):
                    files_to_sync.append(file_path)

        self.logger.info(f"同期対象ファイル数: {len(files_to_sync)}")
        return files_to_sync

    def _copy_file(self, source_file: Path, dry_run: bool = False) -> bool:
        """ファイルをコピー"""
        relative_path = source_file.relative_to(self.source_dir)
        target_file = self.target_dir / relative_path

        # ターゲットディレクトリが存在しない場合は作成
        target_file.parent.mkdir(parents=True, exist_ok=True)

        # 差分チェック(設定で有効な場合)
        if (
            self.config.get("sync_settings", {}).get("incremental", True)
            and target_file.exists()
            and source_file.stat().st_mtime <= target_file.stat().st_mtime
        ):
            self.logger.debug(f"スキップ(変更なし): {relative_path}")
            return False

        if dry_run:
            self.logger.info(f"[DRY RUN] コピー予定: {relative_path}")
            return True

        try:
            shutil.copy2(source_file, target_file)
            self.logger.info(f"コピー完了: {relative_path}")
            return True
        except Exception as e:
            self.logger.error(f"コピー失敗: {relative_path} - {e}")
            return False

    def _create_public_gitignore(self, dry_run: bool = False):
        """公開用.gitignoreファイルを作成"""
        gitignore_content = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
logs/
*.log

# Runtime data
pids/
*.pid
*.seed
*.pid.lock

# Development tools
.mypy_cache/
.ruff_cache/

# Local configuration
.env.local
.env.production
bakufu.yml.local
"""

        gitignore_path = self.target_dir / ".gitignore"

        if dry_run:
            self.logger.info(f"[DRY RUN] .gitignore作成予定: {gitignore_path}")
            return

        try:
            with open(gitignore_path, "w", encoding="utf-8") as f:
                f.write(gitignore_content)
            self.logger.info(f".gitignore作成完了: {gitignore_path}")
        except Exception as e:
            self.logger.error(f".gitignore作成失敗: {e}")

    def sync(self, dry_run: bool = False) -> bool:
        """同期を実行"""
        self.logger.info("=== 公開用リポジトリ同期開始 ===")
        self.logger.info(f"ソース: {self.source_dir}")
        self.logger.info(f"ターゲット: {self.target_dir}")

        if dry_run:
            self.logger.info("*** DRY RUN モード - 実際のファイル操作は行いません ***")

        # ターゲットディレクトリが存在しない場合は作成
        if not dry_run:
            self.target_dir.mkdir(parents=True, exist_ok=True)

        # 同期対象ファイルを収集
        files_to_sync = self._collect_files_to_sync()

        if not files_to_sync:
            self.logger.warning("同期対象のファイルが見つかりませんでした")
            return False

        # ファイルをコピー
        copied_count = 0
        for file_path in files_to_sync:
            if self._copy_file(file_path, dry_run):
                copied_count += 1

        # .gitignoreファイルを作成
        self._create_public_gitignore(dry_run)

        self.logger.info("=== 同期完了 ===")
        self.logger.info(f"処理済みファイル: {copied_count}/{len(files_to_sync)}")

        return True


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="内部リポジトリから公開用リポジトリへファイルを同期します"
    )
    parser.add_argument(
        "--target",
        "-t",
        type=Path,
        required=True,
        help="ターゲットディレクトリ(公開用リポジトリのパス)",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=Path(__file__).parent / "public_sync_config.yaml",
        help="設定ファイルのパス(デフォルト: ./public_sync_config.yaml)",
    )
    parser.add_argument(
        "--source",
        "-s",
        type=Path,
        default=Path(__file__).parent.parent,
        help="ソースディレクトリ(デフォルト: スクリプトの親ディレクトリ)",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="ドライランモード(実際のファイル操作を行わない)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細ログを出力")

    args = parser.parse_args()

    # ログレベル設定
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # パスの検証
    if not args.source.exists():
        print(f"エラー: ソースディレクトリが存在しません: {args.source}", file=sys.stderr)
        sys.exit(1)

    if not args.config.exists():
        print(f"エラー: 設定ファイルが存在しません: {args.config}", file=sys.stderr)
        sys.exit(1)

    try:
        # 同期を実行
        syncer = PublicRepoSyncer(args.config, args.source, args.target)
        success = syncer.sync(dry_run=args.dry_run)

        if success:
            print("同期が正常に完了しました")
            sys.exit(0)
        else:
            print("同期中にエラーが発生しました", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
