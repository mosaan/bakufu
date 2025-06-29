# MCP統合サンプル

このディレクトリには、bakufuのModel Context Protocol (MCP)統合機能を実際に体験できるワークフローサンプルが含まれています。

## 利用可能なワークフロー

### 1. 文書解析器 (`document-analyzer.yml`)
MCPの統合入力処理を使用して、柔軟な入力形式で文書を解析します。

**機能:**
- `@file:`プレフィックスによるドキュメント読み込み対応
- 複数の文書形式（テキスト、JSON、マークダウン）対応
- 構造化された解析結果の出力

**MCP使用例:**
```
ユーザー: /path/to/document.txtの文書を解析してください
アシスタント: [execute_document_analyzerを使用し、document="@file:/path/to/document.txt"で実行]
```

### 2. マルチソースコンテンツ作成器 (`multi-source-content-creator.yml`)
MCPの高度な入力処理機能を使用して、複数のソースからデータを組み合わせてコンテンツを作成します。

**機能:**
- ファイル入力と直接JSON値の組み合わせ
- `@value:`プレフィックスの使用例
- 複雑なパラメータ処理のデモンストレーション

**MCP使用例:**
```
ユーザー: data.jsonと要件書.txtを使ってレポートを作成してください
アシスタント: [execute_multi_source_content_creatorを使用し:
  - data_source="@file:/path/to/data.json:json"
  - requirements="@file:/path/to/要件書.txt"
  - output_format="@value:{\"type\": \"report\", \"style\": \"professional\"}"
で実行]
```

### 3. インタラクティブファイル処理器 (`file-processor.yml`)
様々な操作でファイルをインタラクティブに処理し、MCPツール使用に最適化されています。

**機能:**
- 複数の処理操作（要約、抽出、変換）
- 動的な操作選択
- ファイル形式の自動検出

**MCP使用例:**
```
ユーザー: /path/to/file.pdfから重要な情報を抽出してください
アシスタント: [execute_interactive_file_processorを使用し:
  - file_path="@file:/path/to/file.pdf"
  - operation="extract"
  - output_format="key_points"
で実行]
```

## 使い始める

1. **MCPサーバーの開始:**
   ```bash
   python -m bakufu.mcp_server --workflow-dir examples/ja/mcp-integration
   ```

2. **MCPクライアントの設定:**
   bakufuサーバーをMCPクライアント設定に追加します（例：Claude Desktop）。

3. **ツールの使用:**
   ワークフローがMCPツールとしてクライアントアプリケーションで利用可能になります。

## 統合入力形式の例

これらのワークフローはbakufuの統合入力形式を実例で示しています：

- **ファイル読み込み**: `@file:path/to/file.ext:format:encoding`
- **JSON値**: `@value:{"key": "value"}`
- **直接値**: 通常の文字列と数値はそのまま使用

## MCP使用のヒント

1. **ファイルパス**: `@file:`プレフィックスには絶対パスを使用
2. **JSONエスケープ**: `@value:`プレフィックス内でJSONを適切にエスケープ
3. **エラーハンドリング**: ワークフローにはMCPシナリオ向けの包括的なエラーハンドリングを含む
4. **ドキュメント**: 各ワークフローにはMCPクライアント向けの詳細なパラメータ説明がある