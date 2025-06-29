# テキスト処理ワークフロー

このディレクトリには、様々なテキスト処理タスクを自動化するワークフローが含まれています。v1.1.0で基本テキスト処理メソッドが追加されました。

## 🆕 v1.1.0の新機能 - 基本テキスト処理メソッド

基本的なテキスト操作機能を提供する4つの重要なメソッドが追加されました：

- **新メソッド**: `split`, `extract_between_marker`, `select_item`, `parse_as_json`
- **機能強化**: 包括的なスキーマ検証、メタデータ生成、柔軟な入力形式対応
- **改善**: エラーハンドリング向上、詳細な検証結果、パフォーマンス最適化

## 📁 含まれるワークフロー

### json-extractor.yml
**目的**: テキストからJSONデータを抽出・整形  
**機能**:
- テキストからJSONを抽出
- 指定フィールドの取得
- 構造化されたデータの表示

**使用例**:
```bash
bakufu run examples/text-processing/json-extractor.yml --input '{
  "text": "ユーザーデータ: {\"name\": \"田中太郎\", \"age\": 30, \"city\": \"東京\"}",
  "field_path": "name"
}'
```

### markdown-processor.yml
**目的**: Markdown文書の分析・処理  
**機能**:
- セクション分割
- 構造分析
- セクション別要約生成
- 目次作成

**使用例**:
```bash
bakufu run examples/text-processing/markdown-processor.yml --input '{
  "markdown_text": "# 概要\n\nプロジェクト概要...\n\n## 詳細\n\n詳細な説明...",
  "summary_length": 80
}'
```

### basic-text-methods-demo.yml **（v1.1.0新機能）**
**目的**: v1.1.0の新しい基本テキスト処理メソッドの包括的なデモンストレーション  
**機能**:
- カスタム区切り文字と制限を使った文字列分割
- 特定マーカー間のテキスト抽出（XML、HTMLなど）
- インデックス、スライス、条件による配列要素選択
- 検証とメタデータ生成付きJSON解析
- 複数のテキスト処理メソッドの統合

**使用例**:
```bash
bakufu run examples/ja/text-processing/basic-text-methods-demo.yml --input '{
  "csv_data": "りんご,バナナ,オレンジ,ぶどう,キウイ",
  "xml_content": "<商品><商品情報><名前>ノートパソコン</名前><価格>99000</価格></商品情報></商品>",
  "json_data": "{\"ユーザー\": [{\"名前\": \"田中\", \"年齢\": 30}]}"
}'
```

## 💡 活用シーン

### v1.1.0 基本テキスト処理
- **データ処理**: CSVや構造化テキストの柔軟な分割・解析
- **コンテンツ抽出**: XML/HTML文書からの特定コンテンツ抽出
- **配列操作**: プログラム的な配列要素選択とフィルタリング
- **JSON検証**: スキーマサポート付きJSONデータの解析・検証

### 既存機能
- **文書管理**: 長いマニュアルの要約作成
- **データ抽出**: APIレスポンスからの必要情報抽出
- **コンテンツ分析**: ブログ記事やレポートの構造分析
- **ドキュメント変換**: 形式変換や整理
- **ログ分析**: システムログの処理と構造化データ抽出

## 🔧 新メソッドリファレンス

### split
カスタム区切り文字と最大分割数制限を使った文字列分割
```yaml
method: "split"
separator: ","
max_splits: 3
```

### extract_between_marker  
指定した開始/終了マーカー間のテキスト抽出（単一・複数モード対応）
```yaml
method: "extract_between_marker"
begin: "<名前>"
end: "</名前>"
extract_all: true
```

### select_item
インデックス、スライス記法、条件式による配列要素選択
```yaml
method: "select_item"
index: 0  # または slice: "1:3" または condition: "len(item) > 5"
```

### parse_as_json
スキーマ検証とメタデータ生成付きJSON解析
```yaml
method: "parse_as_json"
schema_file: "schema.json"
format_output: true
```