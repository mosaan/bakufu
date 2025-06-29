# AI出力検証機能

bakufuのAI出力検証機能は、AI呼び出しの結果を構造化し、品質を保証するための包括的なソリューションです。

## 📋 目次

- [概要](#概要)
- [検証タイプ](#検証タイプ)
- [基本的な使用方法](#基本的な使用方法)
- [高度な機能](#高度な機能)
- [ベストプラクティス](#ベストプラクティス)
- [トラブルシューティング](#トラブルシューティング)

## 概要

AI出力検証機能により、以下のことが可能になります：

- **構造化出力の保証**: 予期したフォーマットでのAI出力を確実に取得
- **自動再試行**: 検証失敗時の自動的な再実行
- **柔軟な検証方法**: JSON Schema、Pydantic、カスタム関数による検証
- **出力回復**: 不正なレスポンスからの有効データ抽出

## 検証タイプ

### 1. JSON Schema検証

最も一般的な検証方法で、JSON Schemaを使用してAI出力の構造を検証します。

```yaml
steps:
  - id: sentiment_analysis
    type: ai_call
    prompt: |
      以下のテキストの感情分析を行い、JSON形式で回答してください：
      {{ input.text }}
    validation:
      schema:
        type: object
        required: [sentiment, confidence, summary]
        properties:
          sentiment:
            type: string
            enum: [positive, negative, neutral]
          confidence:
            type: number
            minimum: 0
            maximum: 1
          summary:
            type: string
            minLength: 10
      max_retries: 3
      force_json_output: true
```

### 2. Pydantic モデル検証

型安全性を重視する場合、Pydanticモデルによる検証が効果的です。

```yaml
steps:
  - id: user_data_extraction
    type: ai_call
    prompt: |
      ユーザー情報を抽出し、JSON形式で返してください：
      {{ input.user_text }}
    validation:
      pydantic_model: "UserProfile"  # 事前定義されたPydanticクラス
      max_retries: 2
```

### 3. カスタム検証関数

複雑な検証ロジックには、カスタム関数を使用できます。

```yaml
steps:
  - id: marketing_copy
    type: ai_call
    prompt: |
      {{ input.product }}について魅力的なマーケティングコピーを作成してください。
    validation:
      custom_validator: "validate_marketing_copy"
      criteria:
        min_length: 100
        max_length: 500
        required_keywords: ["製品", "メリット"]
      max_retries: 3
```

## 基本的な使用方法

### 最小構成

```yaml
steps:
  - id: simple_validation
    type: ai_call
    prompt: "簡潔な要約を作成してください: {{ input.text }}"
    validation:
      schema:
        type: object
        required: [summary]
        properties:
          summary:
            type: string
            minLength: 20
```

### AI Map Call での検証

並列処理においても検証機能を利用できます：

```yaml
steps:
  - id: batch_analysis
    type: ai_map_call
    input_array: "{{ input.reviews }}"
    prompt: |
      以下のレビューを分析してください：{{ _item }}
      JSON形式で回答してください。
    validation:
      schema:
        type: object
        required: [rating, sentiment]
        properties:
          rating:
            type: integer
            minimum: 1
            maximum: 5
          sentiment:
            type: string
            enum: [positive, negative, neutral]
      max_retries: 2
```

## 高度な機能

### 出力回復機能

AI出力が完全に正しくない場合でも、有効なデータを抽出できます：

```yaml
validation:
  schema:
    type: object
    required: [data]
  allow_partial_success: true
  extract_json_pattern: '```json\s*(\{.*?\})\s*```'
  max_retries: 2
```

### カスタム再試行プロンプト

検証失敗時の再試行プロンプトをカスタマイズできます：

```yaml
validation:
  schema:
    type: object
    required: [result]
  max_retries: 3
  retry_prompt: |
    前回の回答が無効でした。以下の点に注意して再度回答してください：
    - 有効なJSON形式であること
    - 必須フィールドがすべて含まれていること
```

### JSON出力の強制

AI出力を確実にJSON形式にするための指示を自動追加：

```yaml
validation:
  schema:
    type: object
  force_json_output: true
  json_wrapper_instruction: "必ず有効なJSON形式で回答してください。"
```

## 設定オプション

### ValidationConfig 全設定

```yaml
validation:
  # 検証方法（いずれか一つを指定）
  schema: {}                    # JSON Schema
  pydantic_model: "ModelName"   # Pydanticモデル名
  custom_validator: "func_name" # カスタム関数名
  
  # 共通設定
  max_retries: 3               # 最大再試行回数（0-10）
  retry_prompt: "..."          # カスタム再試行プロンプト
  
  # 出力回復
  allow_partial_success: false # 部分的成功を許可
  extract_json_pattern: "..."  # JSON抽出パターン
  
  # 出力強制
  force_json_output: false     # JSON出力の強制
  json_wrapper_instruction: "..." # JSON指示文
  
  # カスタム検証用
  criteria:                    # カスタム検証パラメータ
    key: value
```

## ベストプラクティス

### 1. 段階的な検証

まずはシンプルなJSON Schema検証から始めましょう：

```yaml
# ✅ Good: シンプルから始める
validation:
  schema:
    type: object
    required: [result]
    properties:
      result:
        type: string
```

### 2. 適切な再試行回数

コストと信頼性のバランスを考慮して設定：

```yaml
# ✅ Good: 1-3回の再試行が一般的
validation:
  schema: {...}
  max_retries: 2  # コストを抑えつつ信頼性を確保
```

### 3. 必要最小限のフィールド

スキーマは必要最小限に留めることで成功率を向上：

```yaml
# ✅ Good: 最小限の必須フィールド
validation:
  schema:
    type: object
    required: [main_result]  # 本当に必要なフィールドのみ
    properties:
      main_result:
        type: string
      optional_detail:  # オプションフィールドは required に含めない
        type: string
```

### 4. エラーハンドリング戦略

検証失敗時の適切な戦略を設定：

```yaml
steps:
  - id: critical_data
    type: ai_call
    validation:
      max_retries: 3
    on_error: stop  # 重要なデータは失敗時に停止
    
  - id: optional_enhancement
    type: ai_call
    validation:
      max_retries: 1
    on_error: continue  # 補助的なデータは失敗しても継続
```

## トラブルシューティング

### よくある問題

#### 1. 検証が常に失敗する

**症状**: 再試行回数を使い切って失敗
**原因**: スキーマが厳しすぎる、またはAIプロンプトが不明確
**解決策**:
```yaml
# スキーマを緩くする
validation:
  schema:
    type: object
    required: [essential_field]  # 必須フィールドを最小限に
    properties:
      essential_field:
        type: string
        # minLength などの制約を緩める
```

#### 2. パフォーマンスが悪い

**症状**: 実行時間が長い
**原因**: 再試行回数が多すぎる
**解決策**:
```yaml
validation:
  max_retries: 1  # 再試行回数を減らす
  force_json_output: true  # JSON出力を強制して成功率向上
```

#### 3. コストが高い

**症状**: API呼び出し回数が予想以上
**原因**: 検証失敗による再試行
**解決策**:
```yaml
validation:
  max_retries: 1
  # または出力回復機能を活用
  allow_partial_success: true
  extract_json_pattern: '```json\s*(\{.*?\})\s*```'
```

### デバッグ方法

詳細なログを確認するには：

```bash
# 詳細モードで実行
bakufu run --verbose your-workflow.yml --input '{...}'

# 失敗したステップの詳細を確認
bakufu validate --verbose your-workflow.yml
```

## 実例

### 実用例1: 商品レビュー分析

```yaml
name: "商品レビュー分析"
description: "レビューテキストから構造化データを抽出"

input_parameters:
  - name: reviews
    type: array
    required: true

steps:
  - id: analyze_reviews
    type: ai_map_call
    input_array: "{{ reviews }}"
    prompt: |
      以下の商品レビューを分析し、JSON形式で結果を返してください：
      レビュー: {{ _item }}
      
      以下の情報を抽出してください：
      - rating: 1-5の評価
      - sentiment: positive/negative/neutral
      - key_points: 主要なポイント（配列）
    validation:
      schema:
        type: object
        required: [rating, sentiment, key_points]
        properties:
          rating:
            type: integer
            minimum: 1
            maximum: 5
          sentiment:
            type: string
            enum: [positive, negative, neutral]
          key_points:
            type: array
            items:
              type: string
            minItems: 1
      max_retries: 2
      force_json_output: true
```

### 実用例2: 技術文書の要約

```yaml
name: "技術文書要約"
description: "技術文書を構造化して要約"

steps:
  - id: structured_summary
    type: ai_call
    prompt: |
      以下の技術文書を分析し、構造化された要約を作成してください：
      {{ input.document }}
    validation:
      schema:
        type: object
        required: [title, summary, key_technologies, difficulty_level]
        properties:
          title:
            type: string
            minLength: 5
            maxLength: 100
          summary:
            type: string
            minLength: 50
            maxLength: 500
          key_technologies:
            type: array
            items:
              type: string
            minItems: 1
            maxItems: 10
          difficulty_level:
            type: string
            enum: [beginner, intermediate, advanced]
      max_retries: 3
      retry_prompt: |
        前回の応答が要求される形式と一致しませんでした。
        必ず有効なJSONで、すべての必須フィールドを含めて回答してください。
```

これらの機能を活用することで、より信頼性の高いAIワークフローを構築できます。