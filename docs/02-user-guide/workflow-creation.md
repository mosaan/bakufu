# 📝 ワークフロー作成ガイド

自分だけのワークフローを作成するための詳細ガイドです。基本構造から高度なテンプレート機能まで、実践的な例を交えて説明します。

## 📋 目次

- [ワークフローの基本構造](#ワークフローの基本構造)
- [入力パラメータの定義](#入力パラメータの定義)
- [ステップの種類と使い方](#ステップの種類と使い方)
- [テンプレート機能](#テンプレート機能)
- [出力の設定](#出力の設定)
- [実践的な作成例](#実践的な作成例)
- [ベストプラクティス](#ベストプラクティス)
- [よくある間違いと対処法](#よくある間違いと対処法)

## ワークフローの基本構造

### 最小限の構成

```yaml
# hello.yml
name: "Hello World"
description: "基本的な挨拶生成"

input_parameters:
  - name: "name"
    type: "string"
    required: true

steps:
  - id: "greet"
    type: "ai_call"
    prompt: "{{ input.name }}さんに親しみやすい挨拶をしてください。"

output:
  format: "text"
  template: "{{ steps.greet }}"
```

### 実用的なワークフロー例

基本的なユースケースとしてコンテンツ分析ワークフローがあります：

```yaml
name: "コンテンツ分析ワークフロー"
description: "テキストの包括的な分析と要約を行います"

input_parameters:
  - name: "text"
    type: "string"
    required: true
    description: "分析対象のテキスト"

steps:
  - id: "analyze"
    type: "ai_call"
    prompt: |
      以下のテキストを分析してください：
      {{ input.text }}
    
  - id: "summarize"
    type: "ai_call"
    prompt: |
      分析結果をもとに要約を作成：
      {{ steps.analyze }}

# 出力設定
output:
  format: "text"
  template: |
    # 分析結果
    
    ## 詳細分析
    {{ steps.analyze }}
    
    ## 要約
    {{ steps.summarize }}
    
    ---
    実行時刻: {{ now().strftime('%Y-%m-%d %H:%M:%S') }}
```

## よく使うワークフローパターン

### 1. 単純なAI処理

```yaml
steps:
  - id: "main_process"
    type: "ai_call"
    prompt: "{{ input.request }}について詳しく説明してください"
```

### 2. 複数ステップの処理

```yaml
steps:
  - id: "analyze"
    type: "ai_call"
    prompt: "{{ input.text }}を分析してください"
    
  - id: "improve"
    type: "ai_call"
    prompt: "分析結果: {{ steps.analyze }} をもとに改善案を提示してください"
```

### 3. データの前処理と分析

```yaml
steps:
  - id: "preprocess"
    type: "text_process"
    method: "markdown_split"
    input: "{{ input.document }}"
    
  - id: "analyze_each"
    type: "collection"
    operation: "map"
    input: "{{ steps.preprocess.sections }}"
    steps:
      - id: "section_analysis"
        type: "ai_call"
        prompt: "このセクションを要約: {{ item }}"
```

## 入力パラメータの基本

基本的なユースケースとして以下のパラメータタイプがよく使われます：

```yaml
input_parameters:
  # 必須の文字列
  - name: "content"
    type: "string"
    required: true
    description: "処理対象のテキスト"
    
  # オプションの選択肢
  - name: "mode"
    type: "string"
    required: false
    default: "standard"
    description: "処理モード（quick/standard/detailed）"
```

詳細な仕様については[ワークフロー仕様リファレンス](../07-reference/workflow-specification.md)を参照してください。

## 実際にワークフローを作成してみる

### ステップ1: 基本ファイルの作成

```yaml
# my-workflow.yml
name: "初回作成ワークフロー"
description: "基本的なテキスト処理"

input_parameters:
  - name: "input_text"
    type: "string"
    required: true

steps:
  - id: "process"
    type: "ai_call"
    prompt: "{{ input.input_text }}を分かりやすく要約してください"

output:
  format: "text"
  template: "{{ steps.process }}"
```

### ステップ2: 実行とテスト

```bash
# ワークフローの実行
bakufu run my-workflow.yml --input input_text="テストテキスト"

# 結果の確認
cat output.txt
```

### ステップ3: 改善と拡張

必要に応じてステップを追加し、より複雑なワークフローに発展させます。

## 参考資料

- [ワークフロー仕様リファレンス](../07-reference/workflow-specification.md) - 完全な技術仕様
- [機能リファレンス](../03-features/README.md) - 各機能の詳細
- [実用例](../06-examples/README.md) - より多くの例

---

📖 [ユーザーガイド目次に戻る](README.md)
