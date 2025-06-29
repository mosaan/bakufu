# Contributing to bakufu

bakufu への貢献をありがとうございます！このドキュメントでは、プロジェクトへの貢献方法について説明します。

## 🚀 開始方法

### 開発環境のセットアップ

1. **uv をインストール**
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **リポジトリをフォーク・クローン**
   ```bash
   git clone https://github.com/mosaan/bakufu.git
   cd bakufu
   ```

3. **依存関係をインストール**
   ```bash
   # 開発用依存関係を含むインストール
   uv sync --all-extra
   ```

4. **動作確認**
   ```bash
   # テスト実行
   uv run pytest
   
   # コード品質チェック
   uv run ruff format
   uv run ruff check
   uv run mypy bakufu
   ```

## 🛠️ 開発ワークフロー

### コード品質の維持

新しい機能を実装した後、または既存のコードを変更した後は、必ず以下の手順を実行してください：

```bash
# 1. コードフォーマット
uv run ruff format

# 2. Lint チェック
uv run ruff check

# 3. 自動修正可能な問題を修正
uv run ruff check --fix

# 4. 型チェック
uv run mypy bakufu

# 5. テスト実行（カバレッジ付き）
uv run pytest --cov=bakufu --cov-report=html --cov-report=term

# 6. 一括実行（推奨）
uv run ruff format && uv run ruff check && uv run mypy bakufu && uv run pytest --cov=bakufu
```

### テストカバレッジ要件

- **全体カバレッジ**: 80% 以上
- **新機能**: 90% 以上
- **コア機能**: 95% 以上

カバレッジが基準を下回る場合は、追加テストを作成してください。

### ブランチ戦略

- `main` - 安定版ブランチ
- `feature/機能名` - 新機能開発
- `fix/修正内容` - バグ修正
- `docs/更新内容` - ドキュメント更新

```bash
# 新機能ブランチの作成例
git checkout -b feature/new-text-processor
git checkout -b fix/template-error-handling
git checkout -b docs/update-readme
```

## 📝 貢献の種類

### 🐛 バグレポート

バグを発見した場合は、[GitHub Issues](https://github.com/mosaan/bakufu/issues) で報告してください。

**必要な情報**:
- bakufu のバージョン
- Python のバージョン
- OS とバージョン
- 再現手順
- 期待される動作
- 実際の動作
- エラーメッセージ（あれば）

**Issue テンプレート**:
```markdown
## 環境
- bakufu バージョン: 
- Python バージョン: 
- OS: 

## 問題の説明
（簡潔な説明）

## 再現手順
1. 
2. 
3. 

## 期待される動作
（期待していた結果）

## 実際の動作
（実際に起こったこと）

## エラーメッセージ
```
（エラーがあれば貼り付け）
```
```

### ✨ 機能要望

新機能の提案は [GitHub Issues](https://github.com/mosaan/bakufu/issues) でお願いします。

**検討事項**:
- 機能の必要性と利用シーン
- 既存機能との整合性
- 実装の複雑さ
- パフォーマンスへの影響

### 🔧 コード貢献

## 📋 Pull Request ガイドライン

### PR 作成前チェックリスト

- [ ] Issue との関連付け完了
- [ ] コード品質チェック通過（ruff + mypy）
- [ ] テスト追加・実行（カバレッジ確認）
- [ ] ドキュメント更新（必要に応じて）
- [ ] CHANGELOG.md 更新（破壊的変更がある場合）

### PR タイトル

以下の形式で記載してください：

```
<type>: <description>

# 例
feat: Add JSON validation for text_process steps
fix: Handle template rendering errors properly
docs: Update API documentation for AI providers
test: Add integration tests for workflow execution
refactor: Simplify error handling in execution engine
```

**Type の種類**:
- `feat` - 新機能
- `fix` - バグ修正
- `docs` - ドキュメント更新
- `test` - テスト追加・修正
- `refactor` - リファクタリング
- `perf` - パフォーマンス改善
- `style` - コードスタイル修正
- `ci` - CI/CD 関連

### PR 説明

```markdown
## 概要
（変更内容の簡潔な説明）

## 変更内容
- 変更点1
- 変更点2

## テスト
- [ ] ユニットテスト追加
- [ ] 統合テスト確認
- [ ] 手動テスト実行

## 関連 Issue
Closes #123

## 破壊的変更
（あれば記載）

## スクリーンショット
（必要あれば）
```

## 🙏 謝辞

bakufu プロジェクトへの貢献をありがとうございます。あなたの貢献により、より多くの人が AI を活用したワークフロー自動化の恩恵を受けることができます。

質問がある場合は、お気軽に Issue や Discussion でお知らせください！