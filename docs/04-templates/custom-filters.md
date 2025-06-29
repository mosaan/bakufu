# Jinja2 カスタムフィルターリファレンス

bakufuでは、ワークフローテンプレートでの利用を想定した独自のJinja2フィルターを提供しています。これらのフィルターは、AI生成テキストの処理、データ変換、フォーマット調整などの用途に特化しています。

## フィルター一覧

### 1. `strip_whitespace`

**用途**: 余分な空白文字を除去し、テキストを正規化する

**引数**: なし

**動作**: 
- 連続する空白文字（スペース、タブ、改行など）を単一のスペースに変換
- 先頭と末尾の空白文字を除去

**使用例**:
```jinja2
{{ "  Hello    World  \n  " | strip_whitespace }}
```

**出力例**:
```
Hello World
```

**実用的な使用場面**:
```yaml
- id: clean_ai_response
  type: ai_call
  prompt: |
    以下のテキストについて要約してください:
    {{ input_text | strip_whitespace }}
```

---

### 2. `truncate_words`

**用途**: 指定した単語数でテキストを切り詰める

**引数**: 
- `length` (int, デフォルト: 10): 残す単語数
- `suffix` (str, デフォルト: "..."): 切り詰めた場合に追加する文字列

**動作**:
- 単語境界でテキストを分割
- 指定された単語数を超える場合、指定数までを保持してsuffixを追加

**使用例**:
```jinja2
{{ "This is a very long text that needs to be truncated" | truncate_words(5) }}
{{ "This is a very long text that needs to be truncated" | truncate_words(5, "...続く") }}
```

**出力例**:
```
This is a very long...
This is a very long...続く
```

**実用的な使用場面**:
```yaml
- id: create_summary
  type: ai_call  
  prompt: |
    以下のテキストの要約を作成してください（最初の部分のみ表示）:
    {{ long_text | truncate_words(50) }}
```

---

### 3. `escape_quotes`

**用途**: テキスト内のクォート文字をエスケープする

**引数**: なし

**動作**:
- ダブルクォート（`"`）を `\"` に変換
- シングルクォート（`'`）を `\'` に変換

**使用例**:
```jinja2
{{ 'He said "Hello World" and she replied \'Good morning\'' | escape_quotes }}
```

**出力例**:
```
He said \"Hello World\" and she replied \'Good morning\'
```

**実用的な使用場面**:
```yaml
- id: prepare_json_string
  type: text_processing
  method: replace
  pattern: "ESCAPED_TEXT"
  replacement: "{{ user_input | escape_quotes }}"
```

---

### 4. `extract_json`

**用途**: テキストからJSON部分を抽出する

**引数**: なし

**動作**:
- テキスト内のJSONパターンを正規表現で検索
- コードブロック内のJSON（```json ... ```）や独立したJSONオブジェクトを抽出
- 最初に見つかった有効なJSONを返す

**使用例**:
```jinja2
{{ "解析結果は以下の通りです: ```json\n{\"score\": 85, \"grade\": \"A\"}\n``` となります" | extract_json }}
```

**出力例**:
```json
{"score": 85, "grade": "A"}
```

**実用的な使用場面**:
```yaml
- id: extract_ai_json
  type: ai_call
  prompt: |
    以下のデータを分析してJSON形式で結果を返してください:
    {{ input_data }}
  
- id: parse_result
  type: text_processing
  method: parse_as_json
  input: "{{ steps.extract_ai_json.output | extract_json }}"
```

---

### 5. `tojson`

**用途**: Unicode対応のJSON変換（デフォルトのtojsonをオーバーライド）

**引数**: なし

**動作**:
- オブジェクトをJSON文字列に変換
- `ensure_ascii=False`でUnicode文字を保持

**使用例**:
```jinja2
{{ {"name": "田中太郎", "age": 30} | tojson }}
```

**出力例**:
```json
{"name": "田中太郎", "age": 30}
```

**実用的な使用場面**:
```yaml
- id: format_user_data
  type: ai_call
  prompt: |
    以下のユーザー情報を分析してください:
    {{ user_data | tojson }}
```

---

### 6. `parse_json_array`

**用途**: JSON文字列の配列を解析してオブジェクト配列に変換

**引数**: なし

**動作**:
- 配列内の各要素がJSON文字列の場合、パースを試行
- パースに失敗した要素は元の文字列のまま保持
- 非配列の入力はそのまま返す

**使用例**:
```jinja2
{{ ['{"name": "田中", "score": 85}', '{"name": "佐藤", "score": 92}'] | parse_json_array }}
```

**出力例**:
```json
[{"name": "田中", "score": 85}, {"name": "佐藤", "score": 92}]
```

**実用的な使用場面**:
```yaml
- id: process_json_strings
  type: text_processing
  method: array_transform
  input: "{{ json_string_array | parse_json_array }}"
  transform_expression: "{{ item.name }}: {{ item.score }}点"
```

## フィルターの組み合わせ

複数のフィルターを組み合わせることで、より高度なテキスト処理が可能です：

```yaml
# 例1: AI応答の正規化とJSON抽出
- id: clean_and_extract
  type: ai_call
  prompt: |
    データを分析してJSON形式で結果を返してください:
    {{ input_data | strip_whitespace | truncate_words(100) }}

- id: extract_clean_json
  type: text_processing
  method: parse_as_json
  input: "{{ steps.clean_and_extract.output | strip_whitespace | extract_json }}"

# 例2: 安全な文字列処理
- id: safe_string_processing
  type: ai_call
  prompt: |
    以下のテキストについて分析してください（安全にエスケープ済み）:
    "{{ user_input | escape_quotes | strip_whitespace }}"
```

## 注意事項

1. **パフォーマンス**: 大きなテキストに対する`strip_whitespace`や`truncate_words`は処理時間が長くなる可能性があります

2. **エラーハンドリング**: `extract_json`や`parse_json_array`は無効なJSONに対して適切にフォールバックします

3. **文字エンコーディング**: すべてのフィルターはUTF-8エンコーディングに対応しています

4. **テンプレート変数**: フィルターは`StrictUndefined`モードで動作するため、未定義変数はエラーになります

## 関連項目

- [カスタム関数リファレンス](custom-functions.md)
- [テンプレート実用例](examples.md)
- [Jinja2標準機能](jinja2-reference.md)