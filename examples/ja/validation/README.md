# AI出力検証の例

このディレクトリには、BakufuのAI出力検証機能を実演する例が含まれています。これらの例は、様々な検証戦略を使用してAIモデルから構造化された信頼性の高い出力を確保する方法を示しています。

## 例

### 1. JSON Schema検証 (`json-schema-validation.yml`)

感情分析のための基本的なJSON Schema検証を実演：

- **機能**: JSON Schema検証、再試行メカニズム、JSON出力強制
- **用途**: 保証された出力形式での構造化感情分析
- **スキーマ**: 感情（列挙）、信頼度（0-1範囲）、要約（最小長）の検証

**使用方法:**
```bash
bakufu run json-schema-validation.yml --text "この製品は素晴らしい！完璧に動作します。"
```

### 2. AI Map Call検証 (`ai-map-validation.yml`)

複数レビューの処理における並列AI Map操作での検証を表示：

- **機能**: 並列検証、エラーハンドリング、集約
- **用途**: 構造化出力による製品レビューの一括処理
- **検証**: 個別レビュー分析 + 全体要約検証

**使用方法:**
```bash
bakufu run ai-map-validation.yml --product_reviews '["素晴らしい製品！", "あまり良くない", "驚くべき品質"]'
```

### 3. 出力回復 (`output-recovery.yml`)

パターン抽出を使用したまとまりのないAI出力からの回復を実演：

- **機能**: パターンベースJSON抽出、部分成功ハンドリング
- **用途**: 冗長なAIレスポンスからの構造化データ抽出
- **回復**: 正規表現を使用してマークダウンコードブロックからJSONを抽出

**使用方法:**
```bash
bakufu run output-recovery.yml --data_request "人気上位5つのプログラミング言語とその人気データを抽出"
```

## 検証設定オプション

### スキーマ検証
```yaml
validation:
  schema:
    type: object
    required: [field1, field2]
    properties:
      field1: { type: string }
      field2: { type: number, minimum: 0 }
```

### 再試行設定
```yaml
validation:
  max_retries: 3
  retry_prompt: "カスタム再試行指示..."
  force_json_output: true
```

### 出力回復
```yaml
validation:
  allow_partial_success: true
  extract_json_pattern: '```json\s*(\{.*?\})\s*```'
```

### Pydanticモデル検証
```yaml
validation:
  pydantic_model: "MyDataModel"  # Pydanticクラスを参照
  max_retries: 2
```

### カスタム検証
```yaml
validation:
  custom_validator: "my_custom_validator"  # カスタム関数を参照
  criteria:
    min_length: 100
    required_keywords: ["重要", "キーワード"]
```

## 主要メリット

1. **信頼性**: AI出力が期待される構造に確実に一致
2. **堅牢性**: 改善されたプロンプトでの自動再試行
3. **柔軟性**: 複数の検証戦略（スキーマ、Pydantic、カスタム）
4. **回復**: まとまりのない出力からのインテリジェントな抽出
5. **パフォーマンス**: 並列Map操作での検証

## ベストプラクティス

1. **シンプルに始める**: 基本的なJSON Schema検証から開始
2. **適切な再試行**: 信頼性とコストのバランスを取るため1-3回の再試行を使用
3. **明確なスキーマ**: 正確で最小限の必須フィールドを定義
4. **回復パターン**: 一般的なAI出力形式の正規表現パターンを使用
5. **エラーハンドリング**: 用途に適した適切な失敗戦略を設定