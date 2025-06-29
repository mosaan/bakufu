# Jinja2標準機能リファレンス

bakufuではJinja2の標準機能も利用できます。このドキュメントでは、ワークフローテンプレートで特に有用な標準フィルターと機能について説明します。

## 文字列操作フィルター

### 基本的な文字列変換

```jinja2
{{ "hello world" | upper }}          # HELLO WORLD
{{ "HELLO WORLD" | lower }}          # hello world
{{ "hello world" | title }}          # Hello World
{{ "hello world" | capitalize }}     # Hello world
```

### 文字列フォーマット

```jinja2
{{ "hello" | center(20) }}           # "       hello        "
{{ "hello" | ljust(10) }}            # "hello     "
{{ "hello" | rjust(10) }}            # "     hello"
```

### 文字列操作

```jinja2
{{ "hello world" | replace("world", "bakufu") }}  # hello bakufu
{{ "  hello  " | trim }}                          # hello
{{ "hello-world-test" | split("-") }}             # ["hello", "world", "test"]
```

## リスト・配列操作フィルター

### 基本的なリスト操作

```jinja2
{{ [3, 1, 4, 1, 5] | sort }}                    # [1, 1, 3, 4, 5]
{{ [3, 1, 4, 1, 5] | reverse }}                 # [5, 1, 4, 1, 3]
{{ [1, 2, 1, 3, 1] | unique }}                  # [1, 2, 3]
{{ ["apple", "banana", "cherry"] | join(", ") }} # apple, banana, cherry
```

### リストフィルタリング

```jinja2
{{ [1, 2, 3, 4, 5] | select("odd") }}           # [1, 3, 5]
{{ [1, 2, 3, 4, 5] | reject("odd") }}           # [2, 4]
{{ ["", "hello", "", "world"] | select() }}      # ["hello", "world"]
```

### リスト情報

```jinja2
{{ [1, 2, 3, 4, 5] | length }}                  # 5
{{ [1, 2, 3, 4, 5] | first }}                   # 1
{{ [1, 2, 3, 4, 5] | last }}                    # 5
{{ [1, 2, 3, 4, 5] | min }}                     # 1
{{ [1, 2, 3, 4, 5] | max }}                     # 5
{{ [1, 2, 3, 4, 5] | sum }}                     # 15
```

## 数値操作フィルター

```jinja2
{{ 3.14159 | round(2) }}                        # 3.14
{{ -5 | abs }}                                  # 5
{{ 3.7 | int }}                                 # 3
{{ "123" | int }}                               # 123
{{ 3 | float }}                                 # 3.0
```

## 条件・デフォルト値フィルター

```jinja2
{{ undefined_var | default("デフォルト値") }}
{{ "" | default("空文字の場合") }}
{{ none_value | default("Noneの場合") }}
{{ false_value | default("Falseの場合", true) }}  # Falseもデフォルト値を使用
```

## 日時関連（datetimeオブジェクト用）

```jinja2
# now() 関数と組み合わせて使用
{{ now() | strftime('%Y-%m-%d') }}               # 2024-06-20
{{ now() | strftime('%Y年%m月%d日') }}            # 2024年06月20日
{{ now() | strftime('%H:%M:%S') }}               # 15:30:45
```

## ループとインデックス

### 基本的なループ

```jinja2
{% for item in items %}
  {{ loop.index }}: {{ item }}         # 1から始まるインデックス
{% endfor %}

{% for item in items %}
  {{ loop.index0 }}: {{ item }}        # 0から始まるインデックス
{% endfor %}
```

### ループの状態確認

```jinja2
{% for item in items %}
  {% if loop.first %}最初: {% endif %}
  {% if loop.last %}最後: {% endif %}
  {{ item }}
  {% if not loop.last %}, {% endif %}
{% endfor %}
```

### ループの制御

```jinja2
{% for item in items %}
  {% if loop.index > 5 %}
    {% break %}                        # ループを終了
  {% endif %}
  {{ item }}
{% endfor %}

{% for item in items %}
  {% if item == "skip" %}
    {% continue %}                     # 次のイテレーションへ
  {% endif %}
  {{ item }}
{% endfor %}
```

## 条件分岐

### 基本的なif文

```jinja2
{% if user.is_premium %}
  プレミアム機能
{% elif user.is_member %}
  メンバー機能
{% else %}
  ゲスト機能
{% endif %}
```

### 複合条件

```jinja2
{% if user.age >= 18 and user.verified %}
  成人認証済みユーザー
{% endif %}

{% if user.role in ["admin", "moderator"] %}
  管理者機能
{% endif %}
```

### インライン条件

```jinja2
{{ "プレミアム" if user.is_premium else "一般" }}
```

## 変数操作

### 変数の定義

```jinja2
{% set user_name = user.first_name + " " + user.last_name %}
{% set current_year = now().year %}
{% set is_weekend = now().weekday() >= 5 %}
```

### 変数のスコープ

```jinja2
{% set global_var = "グローバル" %}

{% for item in items %}
  {% set local_var = "ローカル_" + loop.index|string %}
  {{ global_var }}: {{ local_var }}
{% endfor %}
```

## マクロ（再利用可能なテンプレート）

```jinja2
{% macro render_user(user) %}
  名前: {{ user.name }}
  年齢: {{ user.age }}歳
  {% if user.email %}
  メール: {{ user.email }}
  {% endif %}
{% endmacro %}

# マクロの使用
{{ render_user(current_user) }}
```

## テンプレート継承とインクルード

### インクルード

```jinja2
{% include 'common_header.jinja2' %}
```

### 変数付きインクルード

```jinja2
{% include 'user_info.jinja2' with context %}
{% set section_title = "ユーザー情報" %}
{% include 'section.jinja2' %}
```

## 実用的な組み合わせ例

### 1. リストの条件付きフィルタリング

```yaml
- id: filter_and_display
  type: ai_call
  prompt: |
    有効なユーザー:
    {% for user in users | selectattr("active") %}
    - {{ user.name }} ({{ user.role | default("一般") }})
    {% endfor %}
    
    総数: {{ users | selectattr("active") | list | length }}名
```

### 2. 数値データの集計

```yaml
- id: numerical_analysis
  type: ai_call
  prompt: |
    売上データ分析:
    {% set sales = items | map(attribute="amount") | list %}
    - 合計: {{ sales | sum }}円
    - 平均: {{ (sales | sum / sales | length) | round(2) }}円
    - 最高: {{ sales | max }}円
    - 最低: {{ sales | min }}円
```

### 3. 複雑な条件分岐とループ

```yaml
- id: complex_processing
  type: ai_call
  prompt: |
    {% for category in categories %}
    ## {{ category.name }}
    
    {% set category_items = items | selectattr("category", "eq", category.id) %}
    {% if category_items %}
      アイテム数: {{ category_items | list | length }}
      
      {% for item in category_items | sort(attribute="priority") %}
        {% if loop.index <= 3 %}
      {{ loop.index }}. {{ item.name }}{% if item.urgent %} ⚠️{% endif %}
        {% endif %}
      {% endfor %}
      
      {% if category_items | list | length > 3 %}
      ... 他{{ category_items | list | length - 3 }}件
      {% endif %}
    {% else %}
      アイテムなし
    {% endif %}
    
    {% endfor %}
```

### 4. データ変換チェーン

```yaml
- id: data_transformation
  type: ai_call
  prompt: |
    処理結果:
    {% set processed_data = raw_data 
       | selectattr("valid") 
       | map(attribute="value") 
       | list 
       | sort 
       | reverse %}
    
    {% for value in processed_data[:5] %}
    上位{{ loop.index }}: {{ value }}
    {% endfor %}
```

## よく使用されるパターン

### 安全なデータアクセス

```jinja2
# 安全な属性アクセス
{{ user.profile.name | default("名前未設定") }}

# 安全な辞書アクセス
{{ data.get("key", "デフォルト値") }}

# 安全なリストアクセス
{{ items[0] if items else "リストが空" }}
```

### 条件付きフォーマット

```jinja2
{% if items %}
合計 {{ items | length }} 件のアイテム:
  {% for item in items %}
- {{ item.name }}{% if item.new %} 🆕{% endif %}
  {% endfor %}
{% else %}
アイテムがありません
{% endif %}
```

### 動的なクラス・スタイル

```jinja2
<div class="item {{ 'premium' if user.is_premium else 'standard' }} {{ 'active' if item.active }}">
  {{ item.content }}
</div>
```

## パフォーマンス注意点

1. **重い処理の事前実行**: フィルターチェーンは事前に変数に格納
2. **ループ内での重複処理避**: 計算結果は変数に保存
3. **条件の最適化**: 複雑な条件は事前評価

## 関連項目

- [カスタムフィルターリファレンス](custom-filters.md)
- [カスタム関数リファレンス](custom-functions.md)
- [テンプレート実用例](examples.md)
- [テンプレートエンジン概要](README.md)