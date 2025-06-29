# 最初のワークフロー

Bakufuの基本的な使い方を学ぶために、簡単なワークフローを作成・実行してみましょう。

## シンプルなHello Worldワークフロー

まず、基本的なワークフローファイルを作成します：

### ファイル作成: `hello-world.yml`

```yaml
title: "Hello World - 最初のワークフロー"
description: "Bakufuの基本的な使い方を学ぶためのシンプルなワークフロー"

input:
  name:
    type: string
    description: "あいさつする相手の名前"
    default: "World"

steps:
  - id: greeting
    type: ai_call
    prompt: |
      こんにちは！{{ input.name }}さん、Bakufuの世界へようこそ！
      
      簡潔で親しみやすいあいさつメッセージを作成してください。

output:
  format: text
  template: "{{ steps.greeting.output }}"
```

### ワークフローの実行

```bash
# 基本的な実行
bakufu run hello-world.yml

# 名前を指定して実行
bakufu run hello-world.yml --input name="田中太郎"

# 結果をファイルに保存
bakufu run hello-world.yml --input name="田中太郎" --output result.txt
```

## ワークフローの構成要素

### 1. 基本情報
- **title**: ワークフローの名前
- **description**: ワークフローの説明

### 2. 入力パラメータ（input）
```yaml
input:
  parameter_name:
    type: string|number|boolean|array|object
    description: "パラメータの説明"
    default: デフォルト値（オプション）
```

### 3. 処理ステップ（steps）
```yaml
steps:
  - id: step_name
    type: ai_call|text_process|conditional|collection
    # ステップ固有の設定
```

### 4. 出力設定（output）
```yaml
output:
  format: text|json|yaml
  template: "{{ 出力テンプレート }}"
```

## より実用的な例：テキスト要約ワークフロー

### ファイル作成: `text-summarizer.yml`

```yaml
title: "テキスト要約ツール"
description: "長いテキストを分かりやすく要約します"

input:
  text:
    type: string
    description: "要約したいテキスト"
  
  length:
    type: string
    description: "要約の長さ（短め、普通、詳細）"
    default: "短め"

steps:
  - id: summarize
    type: ai_call
    prompt: |
      以下のテキストを{{ input.length }}で要約してください：
      
      {{ input.text }}
      
      要約のポイント：
      - 主要な内容を漏らさない
      - 分かりやすい日本語で
      - {{ input.length }}の分量で
      - 重要なキーワードを含める

output:
  format: text
  template: |
    ## 要約結果
    
    {{ steps.summarize.output }}
```

### 実行例

```bash
# ファイルから入力（推奨方法）
bakufu run text-summarizer.yml --input-file-for text=document.txt --input '{"length": "詳細"}'

# 直接JSONで指定
bakufu run text-summarizer.yml --input '{"text": "長いテキストの内容...", "length": "簡潔"}'
```

## ワークフローのテストとデバッグ

### 1. 検証モード
```bash
# ワークフローの構文チェック
bakufu validate text-summarizer.yml

# 詳細な検証
bakufu validate text-summarizer.yml --verbose
```

### 2. ドライランモード
```bash
# 実際にAIを呼び出さずに構造をチェック
bakufu run text-summarizer.yml --dry-run
```

### 3. 詳細ログ
```bash
# 実行過程の詳細を表示
bakufu run text-summarizer.yml --verbose
```

## 次のステップ

基本的なワークフローが動作することを確認したら、以下について学習しましょう：

1. **[ワークフロー作成](../02-user-guide/workflow-creation.md)** - より詳細な作成方法
2. **[機能リファレンス](../03-features/README.md)** - 利用可能な機能の詳細
3. **[実用例](../06-examples/README.md)** - 実際の使用例

## よくある問題

### API キーエラー
```
Error: AI provider not configured properly
```
**解決方法**: [基本設定](configuration.md)でAPIキーの設定を確認

### ファイルが見つからない
```
Error: Workflow file not found
```
**解決方法**: ファイルパスが正しいか確認、カレントディレクトリをチェック

### テンプレートエラー
```
Error: Template rendering failed
```
**解決方法**: 変数名やJinja2構文を確認

---

📖 [はじめに目次に戻る](README.md)