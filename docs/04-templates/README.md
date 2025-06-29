# bakufu テンプレートエンジン

bakufuは、ワークフローテンプレートでの動的変数置換にJinja2テンプレートエンジンを使用しています。このドキュメントでは、bakufuで使用可能なテンプレート機能の概要と、効果的な活用方法について説明します。

## 概要

bakufuのテンプレートエンジンは以下の特徴を持ちます：

- **Jinja2ベース**: 強力で柔軟なテンプレート機能
- **カスタムフィルター**: AI処理に特化した独自フィルター
- **カスタム関数**: 日時処理などの便利な関数
- **厳格な変数管理**: 未定義変数はエラーとして検出
- **Unicode対応**: マルチバイト文字の完全サポート

## テンプレート構文

### 基本的な変数参照

```jinja2
{{ variable_name }}
{{ object.property }}
{{ array[0] }}
{{ steps.step_id.output }}
```

### 制御構造

```jinja2
# 条件分岐
{% if condition %}
  内容
{% elif other_condition %}
  別の内容  
{% else %}
  デフォルト内容
{% endif %}

# ループ
{% for item in items %}
  {{ loop.index }}: {{ item }}
{% endfor %}

# 変数定義
{% set variable_name = value %}
```

### コメント

```jinja2
{# これはコメントです #}
```

## エンジン設定

bakufuのテンプレートエンジンは以下の設定で動作します：

### デリミター設定

- 変数: `{{ ... }}`
- ブロック: `{% ... %}`
- コメント: `{# ... #}`

### セキュリティ設定

- **autoescape**: `False` (プロンプト処理のためHTMLエスケープなし)
- **undefined**: `StrictUndefined` (未定義変数はエラー)
- **trim_blocks**: `True` (ブロック後の改行を除去)
- **lstrip_blocks**: `True` (ブロック前の空白を除去)

### 有効な拡張機能

- `jinja2.ext.do`: do文によるサイド効果実行

## 利用可能な機能

### 1. カスタムフィルター

bakufu独自のフィルターが利用可能です：

- `strip_whitespace`: 余分な空白文字を除去
- `truncate_words`: 指定単語数で切り詰め
- `escape_quotes`: クォート文字をエスケープ
- `extract_json`: テキストからJSON部分を抽出
- `tojson`: Unicode対応のJSON変換
- `parse_json_array`: JSON文字列配列をオブジェクト配列に変換

詳細は [カスタムフィルターリファレンス](custom-filters.md) を参照してください。

### 2. カスタム関数

グローバル関数として以下が利用可能です：

- `now()`: 現在の日時を取得

詳細は [カスタム関数リファレンス](custom-functions.md) を参照してください。

### 3. 標準Jinja2機能

Jinja2の標準フィルターと関数も利用できます：

- 文字列操作: `upper`, `lower`, `title`, `capitalize`
- リスト操作: `join`, `sort`, `reverse`, `unique`
- 数値操作: `round`, `abs`, `min`, `max`
- 日付操作: `strftime` (datetimeオブジェクトのメソッド)
- 条件操作: `default`, `select`, `reject`

詳細は [Jinja2標準機能](jinja2-basics.md) を参照してください。

## ワークフローでの使用場面

### 1. プロンプトテンプレート

```yaml
- id: analyze_data
  type: ai_call
  prompt: |
    以下のデータを分析してください:
    ユーザー名: {{ user_name }}
    データ: {{ input_data | tojson }}
    分析日時: {{ now().strftime('%Y-%m-%d %H:%M') }}
```

### 2. 条件分岐での評価

```yaml
- id: conditional_step
  type: conditional
  condition: "{{ user_score >= 80 and user_type == 'premium' }}"
  if_true:
    - id: premium_service
      type: ai_call
      prompt: "プレミアムサービスを提供"
```

### 3. 出力フォーマット

```yaml
output:
  format: text
  template: |
    ## 分析結果レポート
    
    **実行日時**: {{ now().strftime('%Y年%m月%d日 %H時%M分') }}
    **ユーザー**: {{ user_name }}
    
    {{ steps.analysis.output | strip_whitespace }}
```

### 4. 配列・オブジェクト処理

```yaml
- id: process_items
  type: ai_call
  prompt: |
    以下のアイテムを処理してください:
    
    {% for item in items %}
    {{ loop.index }}. {{ item.name }}: {{ item.description | truncate_words(20) }}
    {% endfor %}
```

## エラーハンドリング

### 1. 未定義変数エラー

```yaml
# エラーになる例
{{ undefined_variable }}

# 安全な書き方
{{ variable_name | default('デフォルト値') }}
```

### 2. テンプレート構文エラー

構文エラーは実行時に詳細なエラーメッセージで報告されます：

```
Template rendering failed: Unexpected token 'end of template' at line 5
```

### 3. フォールバック処理

bakufuは`render_with_fallback`メソッドを提供し、エラー時の代替処理が可能です。

## パフォーマンス考慮事項

### 1. 変数の再利用

同じ値を複数回使用する場合は変数に格納：

```jinja2
{% set current_time = now() %}
実行開始: {{ current_time.strftime('%H:%M') }}
実行終了予定: {{ current_time.strftime('%H:%M') }}
```

### 2. 条件の最適化

複雑な条件式は事前に評価：

```jinja2
{% set is_valid_user = user.status == 'active' and user.type == 'premium' %}
{% if is_valid_user %}
  プレミアム機能を提供
{% endif %}
```

### 3. フィルターの順序

処理コストの低い操作から実行：

```jinja2
{{ long_text | truncate_words(100) | strip_whitespace }}
```

## 実用的なパターン

実際のワークフローでよく使用されるテンプレートパターンについては、[テンプレート実用例](examples.md) を参照してください。

## セキュリティ考慮事項

1. **入力の検証**: ユーザー入力は適切にエスケープ
2. **機密情報**: テンプレート内に機密情報を直接記述しない
3. **実行制限**: 無限ループなどを避ける適切な制御

## トラブルシューティング

### よくある問題

1. **未定義変数エラー**: `default`フィルターで対処
2. **型エラー**: 適切な型変換を実行
3. **文字エンコーディング**: UTF-8で統一
4. **パフォーマンス**: 重い処理は事前に実行

### デバッグのヒント

1. テンプレート内で`{{ variable | tojson }}`を使用して変数の内容を確認
2. 段階的に複雑さを追加してエラー箇所を特定
3. `validate_template`メソッドで事前に構文チェック

## 関連ドキュメント

- [カスタムフィルターリファレンス](custom-filters.md)
- [カスタム関数リファレンス](custom-functions.md)
- [テンプレート実用例](examples.md)
- [Jinja2標準機能](jinja2-reference.md)

---

**注意**: このドキュメントは継続的に更新されます。最新の機能については、実装コード（`bakufu/core/template_engine.py`）も併せて確認してください。