# 条件分岐操作

bakufuの条件分岐操作は、データドリブンな決定に基づく動的なワークフロー実行を可能にします。インテリジェントで適応性のあるワークフローを作成するための強力な分岐ロジックを提供します。

## 概要

条件分岐操作は、新しいステップタイプ`conditional`として実装され、異なる分岐モードを提供します：

- **基本条件分岐**: 二進決定のための単純な`if_true`/`if_false`構造
- **多分岐条件分岐**: 複雑なロジックパスのための複数の`conditions`配列
- **エラーハンドリング**: 条件評価失敗に対する設定可能な戦略
- **ネストサポート**: 条件分岐内での条件分岐ステップ

## 基本構文

```yaml
- id: "step_name"
  type: "conditional"
  condition: "{{ jinja2_expression }}"
  if_true: [真の場合に実行するステップ]
  if_false: [偽の場合に実行するステップ]
```

## 操作タイプ

### 1. 基本的なIf-Else条件分岐

真/偽の分岐を持つ単純な二進決定：

```yaml
- id: "score_check"
  type: "conditional"
  condition: "{{ user_score >= 80 }}"
  if_true:
    - id: "success_message"
      type: "ai_call"
      prompt: "高得点のお祝いメッセージを生成: {{ user_score }}"
  if_false:
    - id: "improvement_message"
      type: "ai_call"
      prompt: "得点への励ましメッセージを生成: {{ user_score }}"
```

### 2. 多分岐条件分岐

順番に評価される複数の条件を持つ複雑なロジック：

```yaml
- id: "grade_classification"
  type: "conditional"
  conditions:
    - condition: "{{ score >= 95 }}"
      name: "excellent"
      steps:
        - id: "excellence_certificate"
          type: "ai_call"
          prompt: "優秀証明書を作成"
    
    - condition: "{{ score >= 80 }}"
      name: "good"
      steps:
        - id: "good_performance"
          type: "ai_call"
          prompt: "良い成績を評価"
    
    - condition: "{{ score >= 60 }}"
      name: "passing"
      steps:
        - id: "basic_pass"
          type: "ai_call"
          prompt: "基本的な合格承認"
    
    - condition: ""
      name: "needs_improvement"
      default: true
      steps:
        - id: "improvement_plan"
          type: "ai_call"
          prompt: "改善計画を作成"
```

### 3. オプション実行（Else分岐なし）

条件が真の場合のみステップを実行：

```yaml
- id: "bonus_feature"
  type: "conditional"
  condition: "{{ enable_premium and user_level > 5 }}"
  if_true:
    - id: "premium_content"
      type: "ai_call"
      prompt: "プレミアムコンテンツを生成"
  # if_falseなし - 条件が偽の場合は何も起こらない
```

## エラーハンドリング

条件評価エラーに対するシステムの応答を設定：

```yaml
- id: "safe_conditional"
  type: "conditional"
  condition: "{{ potentially_undefined_variable > 10 }}"
  on_condition_error: "continue"  # オプション: stop, continue, skip_remaining
  if_true:
    - id: "success_action"
      type: "ai_call"
      prompt: "成功ケース"
  if_false:
    - id: "fallback_action"
      type: "ai_call"
      prompt: "フォールバックケース"
```

### エラーハンドリング戦略

- **`stop`**（デフォルト）: 条件評価エラー時にワークフロー実行を停止
- **`continue`**: 条件を`false`として扱い、`if_false`分岐で続行
- **`skip_remaining`**: このステップを完全にスキップし、次のステップで続行

## 結果アクセス

条件分岐ステップは、以下のプロパティを持つ`ConditionalResult`オブジェクトを返します：

```yaml
# 後続ステップで条件分岐ステップの結果にアクセス
- id: "follow_up"
  type: "ai_call"
  prompt: |
    前の条件分岐結果:
    - 実行された分岐: {{ steps.score_check.executed_branch }}
    - 条件結果: {{ steps.score_check.condition_result }}
    - 出力: {{ steps.score_check.output }}
    - エラー（もしあれば）: {{ steps.score_check.evaluation_error }}
```

### 結果プロパティ

- **`output`**: 実行された分岐からの出力（最後のステップの結果）
- **`condition_result`**: 条件評価のブール結果（`true`/`false`/`null`）
- **`executed_branch`**: 実行された分岐の名前（`"if_true"`, `"if_false"`, 分岐名, または`null`）
- **`evaluation_error`**: 条件評価が失敗した場合のエラーメッセージ（または`null`）

## ネストした条件分岐

条件分岐ステップは、他の条件分岐の分岐内にネストできます：

```yaml
- id: "complex_logic"
  type: "conditional"
  condition: "{{ user_type == 'premium' }}"
  if_true:
    - id: "premium_check"
      type: "conditional"
      condition: "{{ subscription_active }}"
      if_true:
        - id: "full_access"
          type: "ai_call"
          prompt: "フルプレミアムアクセスを付与"
      if_false:
        - id: "renewal_reminder"
          type: "ai_call"
          prompt: "サブスクリプション更新リマインダーを送信"
  if_false:
    - id: "basic_service"
      type: "ai_call"
      prompt: "基本サービスを提供"
```

## ベストプラクティス

### 1. 明確な条件ロジック

説明的な変数名を使用して、明確で読みやすい条件を記述：

```yaml
# 良い例
condition: "{{ user_score >= passing_threshold and quiz_completed }}"

# 不明瞭な例
condition: "{{ s >= t and c }}"
```

### 2. エラーハンドリング戦略

ユースケースに適切なエラーハンドリングを選択：

```yaml
# 重要なワークフローの場合 - エラー時に停止
on_condition_error: "stop"

# 堅牢なワークフローの場合 - フォールバックで続行
on_condition_error: "continue"

# オプション機能の場合 - 不確実な場合はスキップ
on_condition_error: "skip_remaining"
```

### 3. 分岐命名

多分岐条件に説明的な名前を使用：

```yaml
conditions:
  - condition: "{{ risk_score > 80 }}"
    name: "high_risk"
    steps: [...]
  
  - condition: "{{ risk_score > 40 }}"
    name: "medium_risk"
    steps: [...]
  
  - condition: ""
    name: "low_risk"
    default: true
    steps: [...]
```

### 4. 結果活用

後続ステップで条件分岐結果を活用：

```yaml
- id: "final_report"
  type: "ai_call"
  prompt: |
    最終レポートを生成:
    決定: {{ steps.risk_assessment.executed_branch }}
    {% if steps.risk_assessment.condition_result %}
    リスクレベル: 高
    {% else %}
    リスクレベル: 低
    {% endif %}
    
    詳細: {{ steps.risk_assessment.output }}
```

## 一般的なパターン

### 1. 機能フラグ

```yaml
- id: "feature_toggle"
  type: "conditional"
  condition: "{{ config.experimental_features_enabled }}"
  if_true:
    - id: "new_feature"
      type: "ai_call"
      prompt: "実験的AIモデルを使用"
  if_false:
    - id: "stable_feature"
      type: "ai_call"
      prompt: "安定版AIモデルを使用"
```

### 2. データ検証

```yaml
- id: "input_validation"
  type: "conditional"
  condition: "{{ input.data | length > 0 and input.format == 'json' }}"
  if_true:
    - id: "process_data"
      type: "text_process"
      method: "parse_as_json"
      input: "{{ input.data }}"
  if_false:
    - id: "validation_error"
      type: "ai_call"
      prompt: "無効な入力のエラーメッセージを生成"
```

### 3. ユーザーパーソナライゼーション

```yaml
- id: "personalized_response"
  type: "conditional"
  conditions:
    - condition: "{{ user.preferences.style == 'formal' }}"
      name: "formal_tone"
      steps:
        - id: "formal_message"
          type: "ai_call"
          prompt: "フォーマルなビジネス応答を生成"
    
    - condition: "{{ user.preferences.style == 'casual' }}"
      name: "casual_tone"
      steps:
        - id: "casual_message"
          type: "ai_call"
          prompt: "カジュアルで親しみやすい応答を生成"
    
    - condition: ""
      name: "default_tone"
      default: true
      steps:
        - id: "balanced_message"
          type: "ai_call"
          prompt: "バランスの取れた専門的な応答を生成"
```

## 他のステップタイプとの統合

条件分岐操作は、他のすべてのbakufuステップタイプとシームレスに連携：

```yaml
steps:
  # 条件前のテキスト処理
  - id: "extract_sentiment"
    type: "text_process"
    method: "parse_as_json"
    input: "{{ sentiment_analysis_result }}"
  
  # 抽出されたデータに基づく条件分岐
  - id: "sentiment_response"
    type: "conditional"
    condition: "{{ steps.extract_sentiment.sentiment == 'positive' }}"
    if_true:
      # ポジティブ感情に対するAI呼び出し
      - id: "positive_response"
        type: "ai_call"
        prompt: "前向きな応答を生成"
    if_false:
      # ネガティブ感情に対するコレクション操作
      - id: "improvement_suggestions"
        type: "collection"
        operation: "map"
        input: "{{ improvement_areas }}"
        steps:
          - id: "suggest_improvement"
            type: "ai_call"
            prompt: "次の改善を提案: {{ item }}"
```

## パフォーマンス考慮事項

### 1. 条件の複雑さ

パフォーマンスと可読性のために条件をシンプルに保つ：

```yaml
# 効率的
condition: "{{ score > threshold }}"

# 非効率的
condition: "{{ complex_calculation(data) and heavy_processing(input) > computed_value() }}"
```

### 2. 分岐ステップ数

ワークフローパフォーマンスのために各分岐のステップ数を考慮：

```yaml
# 分岐での重い処理の場合、並列実行を検討
if_true:
  - id: "parallel_processing"
    type: "collection"
    operation: "map"
    input: "{{ large_dataset }}"
    concurrency:
      max_parallel: 5
    steps:
      - id: "process_item"
        type: "ai_call"
        prompt: "項目を処理: {{ item }}"
```

### 3. エラー回復

ワークフローの中断を最小限に抑えるエラーハンドリングを設計：

```yaml
# 優雅な劣化
- id: "robust_conditional"
  type: "conditional"
  condition: "{{ external_service.available }}"
  on_condition_error: "continue"
  if_true:
    - id: "use_external_service"
      type: "ai_call"
      prompt: "外部サービスで処理"
  if_false:
    - id: "use_fallback_service"
      type: "ai_call"
      prompt: "内部サービスで処理"
```

## 例

完全な動作例については、`examples/`ディレクトリの条件分岐関連ワークフローを参照してください。

---

📖 [機能リファレンス目次に戻る](README.md)