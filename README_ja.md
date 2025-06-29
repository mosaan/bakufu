# 🌊 bakufu

**AI-Powered Workflow Automation CLI Tool**

bakufu（瀑布）は、AI を活用した強力なワークフロー自動化ツールです。名前は、連続的な AI 呼び出しの流れを、絶え間ない滝の勢いになぞらえたものです。YAML でワークフローを定義し、複数の AI プロバイダーやテキスト処理機能を組み合わせて、複雑な作業を自動化できます。

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## ✨ 主な機能

### 🤖 AI プロバイダー統合
- **LiteLLM backed**: LiteLLM を使用した複数の AI プロバイダー統合

### 📝 テキスト処理機能
- **正規表現抽出** - パターンマッチングによるデータ抽出
- **テキスト置換** - 文字列・正規表現による変換
- **JSON パース** - スキーマ検証による構造化データ解析
- **Markdown 分割** - セクション別の文書処理

### � 基本的なテキストメソッド
- **split** - カスタム区切り文字と制限による文字列分割
- **extract_between_marker** - 指定したマーカー間のテキスト抽出
- **select_item** - インデックス、スライス、条件による配列要素選択
- **parse_as_json** - 検証とメタデータ付きの JSON パース

### 📊 コレクション操作
- **map** - AI またはテキスト処理を使用したコレクション各要素の変換
- **filter** - 指定条件に合致する要素の選択
- **reduce** - コレクション要素の単一値への集約
- **pipeline** - 複数のコレクション操作の連鎖
- **並列処理** - 設定可能な並行性による同時実行
- **エラーハンドリング** - 失敗処理のための柔軟な戦略（スキップ、停止、リトライ）

### 🔀 条件付き操作
- **conditional** - 動的条件に基づく異なるステップの実行
- **if-else 構造** - シンプルな真偽分岐実行
- **多分岐ロジック** - 複数パスによる複雑な条件評価
- **エラーハンドリング** - 条件評価失敗のための設定可能な戦略
- **ネストサポート** - 条件分岐内での条件ステップ
- **テンプレート統合** - 完全なコンテキストアクセスによる Jinja2 ベースの条件評価

### ✅ AI 出力検証
- **JSON スキーマ検証** - 定義されたスキーマに AI 出力が一致することを保証
- **Pydantic モデル検証** - Pydantic モデルを使用した型安全な検証
- **カスタム検証関数** - カスタムロジックによる柔軟な検証
- **自動リトライロジック** - 検証対応プロンプトによるスマートリトライ
- **出力回復** - 不正な AI レスポンスからの有効データ抽出
- **並列検証** - AI マップ操作とのシームレスな連携

### �🔧 高度な機能
- **Jinja2 テンプレート** - 動的なワークフロー実行
- **エラーハンドリング** - 詳細なエラー情報と復旧提案
- **並列実行** - AI マップ呼び出しによる効率的なタスク処理
- **リアルタイム進捗表示** - 視覚的な進捗バーと実行監視
- **豊富な設定オプション** - プロバイダー固有の細かな調整

### 🔌 MCP（Model Context Protocol）統合
- **MCP サーバー** - 対応クライアント向けの MCP ツールとして bakufu ワークフローを実行
- **動的ツール登録** - すべてのワークフローを個別の MCP ツールとして自動公開
- **統合入力処理** - MCP ツールパラメータでの `@file:` と `@value:` プレフィックスサポート
- **クライアント互換性** - Claude Desktop、Cursor、その他の MCP 対応アプリケーションと動作
- **リアルタイムワークフロー検出** - 新しいワークフローの自動検出と登録

## 🚀 クイックスタート

### インストール

```bash
uv tool install git+https://github.com/mosaan/bakufu.git
```

### 基本的な使い方

1. **設定の初期化**
```bash
# 基本設定を作成
bakufu config init

# API キーを設定
export GOOGLE_API_KEY="your_gemini_api_key"
```

2. **最初のワークフロー実行**
```bash
# Hello World サンプルを実行
bakufu run examples/ja/basic/hello-world.yml --input '{"name": "太郎"}'

# テキスト要約を試す
bakufu run examples/ja/basic/text-summarizer.yml --input '{
  "text": "長いテキストをここに入力...", 
  "max_length": 200
}'
```

3. **ワークフローの検証**
```bash
# YAML ファイルの構文チェック
bakufu validate examples/ja/basic/hello-world.yml

# 詳細なバリデーション
bakufu validate --verbose my-workflow.yml
```

詳細は [docs](docs/README.md) をご覧ください。

##  開発者向け情報

## 🤝 コントリビューション

貢献は大歓迎です！詳細は [CONTRIBUTING.md](./CONTRIBUTING.md) をご覧ください。

### バグレポート・機能要望

[GitHub Issues](https://github.com/mosaan/bakufu/issues) でお気軽にお知らせください。

### 開発に参加

1. Fork してブランチを作成
2. 変更を実装
3. テストを追加・実行
4. Pull Request を作成

## 📄 ライセンス

MIT License - 詳細は [LICENSE](./LICENSE) ファイルをご覧ください。

## 🙏 謝辞

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) - Primary Coder
- [LiteLLM](https://github.com/BerriAI/litellm) - AI プロバイダー統合
- [Jinja2](https://jinja.palletsprojects.com/) - テンプレートエンジン
- [Pydantic](https://pydantic.dev/) - データバリデーション
- [Click](https://click.palletsprojects.com/) - CLI フレームワーク

---

**bakufu で AI を活用したワークフロー自動化をシンプルに始めましょう！** 🚀