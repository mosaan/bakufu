# Jinja2 カスタム関数リファレンス

bakufuでは、ワークフローテンプレート内で使用できる独自のグローバル関数を提供しています。これらの関数は、動的な値の生成や計算処理に使用できます。

## 関数一覧

### 1. `now()`

**用途**: 現在の日時を取得する

**引数**: なし

**戻り値**: `datetime.datetime`オブジェクト

**動作**:
- 関数呼び出し時点での現在の日時を返す
- ローカルタイムゾーンで日時を取得
- Pythonの`datetime.now()`と同等

**基本的な使用例**:
```jinja2
{{ now() }}
{{ now().strftime('%Y-%m-%d %H:%M:%S') }}
{{ now().year }}
{{ now().month }}
{{ now().day }}
```

**出力例**:
```
2024-06-20 15:30:45.123456
2024-06-20 15:30:45
2024
6
20
```

## 実用的な使用例

### 1. ログ・レポートのタイムスタンプ

```yaml
- id: generate_report
  type: ai_call
  prompt: |
    レポート生成日時: {{ now().strftime('%Y年%m月%d日 %H時%M分') }}
    
    以下のデータについて分析レポートを作成してください:
    {{ input_data }}
```

### 2. 日付ベースの条件分岐

```yaml
- id: time_based_greeting
  type: conditional
  condition: "{{ now().hour < 12 }}"
  if_true:
    - id: morning_message
      type: ai_call
      prompt: "おはようございます。今日は{{ now().strftime('%m月%d日') }}です。"
  if_false:
    - id: afternoon_message
      type: ai_call
      prompt: "こんにちは。現在{{ now().strftime('%H時%M分') }}です。"
```

### 3. ファイル名やIDへの日時埋め込み

```yaml
- id: create_daily_summary
  type: ai_call
  prompt: |
    今日の日報を作成してください。
    
    作成日時: {{ now().strftime('%Y-%m-%d %H:%M:%S') }}
    タイトル: {{ now().strftime('%Y年%m月%d日') }}の業務報告
    
    内容: {{ daily_activities }}

output:
  format: text
  template: |
    === {{ now().strftime('%Y年%m月%d日') }}の日報 ===
    作成時刻: {{ now().strftime('%H:%M') }}
    
    {{ steps.create_daily_summary.output }}
```

### 4. 期限や締切の計算

```yaml
- id: deadline_reminder
  type: ai_call
  prompt: |
    現在時刻: {{ now().strftime('%Y-%m-%d %H:%M') }}
    
    以下のタスクについて、現在時刻を基準とした
    優先度付けと進捗管理のアドバイスを提供してください:
    
    {% for task in tasks %}
    - {{ task.name }} (締切: {{ task.deadline }})
    {% endfor %}
```

### 5. 時間帯別のメッセージカスタマイズ

```yaml
- id: time_sensitive_content
  type: ai_call
  prompt: |
    {% set current_hour = now().hour %}
    {% if current_hour >= 6 and current_hour < 12 %}
    朝の時間帯（{{ current_hour }}時）に適した
    {% elif current_hour >= 12 and current_hour < 18 %}
    昼の時間帯（{{ current_hour }}時）に適した
    {% else %}
    夜の時間帯（{{ current_hour }}時）に適した
    {% endif %}
    
    {{ content_type }}を作成してください:
    {{ input_content }}
```

### 6. 実行時間の記録

```yaml
input_parameters:
  - name: execution_start_time
    type: string
    required: false
    default: "{{ now().isoformat() }}"

steps:
  - id: process_data
    type: ai_call
    prompt: |
      処理開始時刻: {{ execution_start_time }}
      現在時刻: {{ now().isoformat() }}
      
      データ処理を実行してください:
      {{ input_data }}
```

## 日時フォーマット例

`now()`関数と`strftime()`メソッドを組み合わせることで、様々な日時フォーマットが可能です：

```jinja2
# 基本的な日時フォーマット
{{ now().strftime('%Y-%m-%d') }}           # 2024-06-20
{{ now().strftime('%Y年%m月%d日') }}        # 2024年06月20日
{{ now().strftime('%H:%M:%S') }}           # 15:30:45
{{ now().strftime('%Y-%m-%d %H:%M:%S') }}  # 2024-06-20 15:30:45

# 曜日を含むフォーマット
{{ now().strftime('%Y年%m月%d日 (%A)') }}   # 2024年06月20日 (Thursday)
{{ now().strftime('%m/%d (%a)') }}         # 06/20 (Thu)

# ISO形式
{{ now().isoformat() }}                    # 2024-06-20T15:30:45.123456

# カスタムフォーマット
{{ now().strftime('Week %U of %Y') }}      # Week 24 of 2024
```

## 日時の計算

Jinja2テンプレート内では、Python的な日時計算も可能です：

```jinja2
# 現在の年、月、日の取得
今年: {{ now().year }}年
今月: {{ now().month }}月
今日: {{ now().day }}日

# 曜日の判定（0=月曜日、6=日曜日）
{% if now().weekday() < 5 %}
平日です
{% else %}
週末です
{% endif %}

# 時刻による条件分岐
{% set hour = now().hour %}
{% if hour < 9 %}
営業時間外です（開始前）
{% elif hour >= 18 %}
営業時間外です（終了後）
{% else %}
営業時間内です
{% endif %}
```

## 注意事項

1. **タイムゾーン**: `now()`はローカルタイムゾーンを使用します。UTC時刻が必要な場合は別途考慮が必要です

2. **実行タイミング**: テンプレートが評価される度に現在時刻が取得されるため、同一ワークフロー内でも時刻が変わる可能性があります

3. **パフォーマンス**: 頻繁な`now()`呼び出しは避け、必要に応じて変数に格納することを推奨します

4. **文字エンコーディング**: 日本語の曜日や月名を使用する場合は、適切なロケール設定が必要な場合があります

## 関連項目

- [カスタムフィルターリファレンス](custom-filters.md)
- [テンプレート実用例](examples.md)
- [Jinja2標準機能](jinja2-reference.md)