# ステップタイプ解説

Bakufuで利用可能な各ステップタイプの詳細な説明と使用方法を解説します。

## 基本ステップタイプ

### 1. AI呼び出し（ai_call）

AIモデルを呼び出してテキスト生成を行います。

```yaml
- id: ai_step
  type: ai_call
  prompt: "{{ 動的なプロンプト }}"
  provider: "gemini/gemini-2.0-flash"  # オプション
  temperature: 0.7  # オプション
```

**主要パラメータ**:
- `prompt`: AIに送信するプロンプト（Jinja2テンプレート使用可能）
- `provider`: 使用するAIプロバイダー
- `temperature`: 創造性レベル（0.0-1.0）

### 2. テキスト処理（text_process）

テキストの変換、分割、抽出などを行います。

```yaml
- id: text_step
  type: text_process
  method: split|replace|parse_as_json|extract_between_marker
  input: "{{ 処理対象テキスト }}"
  # メソッド固有のパラメータ
```

**利用可能なメソッド**:
- `split`: テキストを区切り文字で分割
- `replace`: 文字列の置換
- `parse_as_json`: JSON形式として解析
- `extract_between_marker`: マーカー間のテキスト抽出
- `regex_extract`: 正規表現による抽出
- `csv_parse`: CSV形式として解析（カスタム区切り文字対応）
- `tsv_parse`: TSV形式として解析
- `yaml_parse`: YAML形式として解析
- `format`: Jinja2テンプレートを使用したテキスト形式化

## 高度なステップタイプ

### 3. 条件分岐（conditional）

条件に基づいて処理を分岐させます。

```yaml
- id: conditional_step
  type: conditional
  condition: "{{ 条件式 }}"
  if_true:
    - id: true_action
      type: ai_call
      prompt: "条件が真の場合の処理"
  if_false:
    - id: false_action
      type: ai_call
      prompt: "条件が偽の場合の処理"
```

**多分岐条件**:
```yaml
- id: multi_branch
  type: conditional
  conditions:
    - condition: "{{ score >= 90 }}"
      name: "excellent"
      steps: [...]
    - condition: "{{ score >= 70 }}"
      name: "good"
      steps: [...]
    - condition: ""
      name: "needs_improvement"
      default: true
      steps: [...]
```

### 4. コレクション操作（collection）

配列やリストデータの処理を行います。

#### Map操作 - 各要素を変換
```yaml
- id: map_operation
  type: collection
  operation: map
  input: "{{ データ配列 }}"
  steps:
    - id: transform_item
      type: ai_call
      prompt: "項目を処理: {{ item }}"
```

#### Filter操作 - 条件で絞り込み
```yaml
- id: filter_operation
  type: collection
  operation: filter
  input: "{{ データ配列 }}"
  condition: "{{ item.score > 70 }}"
```

#### Reduce操作 - 集約処理
```yaml
- id: reduce_operation
  type: collection
  operation: reduce
  input: "{{ データ配列 }}"
  initial_value: ""
  steps:
    - id: combine
      type: ai_call
      prompt: "{{ acc }}と{{ item }}を結合"
```

### Collection固有の高度な設定

Collection ステップでは、以下の固有パラメータが利用可能です：

#### 詳細エラーハンドリング
```yaml
- id: collection_with_error_handling
  type: collection
  operation: map
  input: "{{ データ配列 }}"
  error_handling:
    on_item_failure: skip|stop|retry  # デフォルト: skip
    on_condition_error: skip_item|stop|default_false  # デフォルト: skip_item
    max_retries_per_item: 2  # デフォルト: 2
    preserve_errors: true  # デフォルト: true
  steps: [...]
```

#### 並行処理設定
```yaml
- id: parallel_collection
  type: collection
  operation: map
  input: "{{ データ配列 }}"
  concurrency:
    max_parallel: 5  # 最大並行数
    batch_size: 10   # バッチサイズ
    delay_between_batches: 1.0  # バッチ間の遅延（秒）
  steps: [...]
```

### 5. 条件分岐固有の設定

Conditional ステップでは、条件評価エラーに対する追加の制御が可能です：

```yaml
- id: conditional_with_error_handling
  type: conditional
  condition: "{{ 複雑な条件式 }}"
  on_condition_error: stop|continue|skip_remaining  # デフォルト: stop
  if_true:
    - id: true_action
      type: ai_call
      prompt: "条件が真の場合の処理"
  if_false:
    - id: false_action
      type: ai_call
      prompt: "条件が偽の場合の処理"
```


## ステップ設定の共通パラメータ

### 基本エラーハンドリング（全ステップ共通）

すべてのステップタイプで利用可能な共通パラメータ：

```yaml
- id: any_step
  type: ai_call  # または他の任意のステップタイプ
  prompt: "処理内容"
  on_error: stop|continue|skip_remaining  # デフォルト: stop
  description: "ステップの説明（オプション）"
```

**`on_error` の動作**:
- `stop`: エラー時にワークフロー全体を停止（デフォルト）
- `continue`: エラーを無視して次のステップに進む
- `skip_remaining`: 残りのステップをスキップしてワークフロー終了

## ステップ間のデータ受け渡し

### 前のステップの結果を参照
```yaml
- id: step1
  type: ai_call
  prompt: "最初の処理"

- id: step2
  type: ai_call
  prompt: "前の結果を使用: {{ steps.step1.output }}"
```

### 複数ステップの結果を統合
```yaml
- id: summary
  type: ai_call
  prompt: |
    以下の結果を統合してください:
    分析1: {{ steps.analysis1.output }}
    分析2: {{ steps.analysis2.output }}
    分析3: {{ steps.analysis3.output }}
```

## ワークフローレベルの出力設定

出力設定はワークフローレベルでのみ設定可能です（個別ステップレベルでは不可）：

```yaml
# workflow.yaml
name: "サンプルワークフロー"
description: "出力形式を指定したワークフロー"

# ワークフロー全体の出力設定
output:
  format: json|text|yaml  # デフォルト: text
  template: "カスタム出力テンプレート（オプション）"

inputs:
  # ...

steps:
  # ...
```

## 実例参照

各ステップタイプの詳細な実例は、以下を参照してください：

- **[examples/](../../examples/)** - 実際のワークフローファイル
- **[機能リファレンス](../03-features/README.md)** - 各機能の詳細仕様
- **[実用例](../06-examples/README.md)** - ユースケース別の使用例

---

📖 [ユーザーガイド目次に戻る](README.md)