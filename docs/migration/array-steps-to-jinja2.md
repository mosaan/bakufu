# Array処理ステップ群からJinja2テンプレートへの移行ガイド

## 概要

bakufu v0.5.0において、専用のArray処理ステップ（ArrayAggregateStep、ArrayFilterStep、ArraySortStep、ArrayTransformStep）は廃止され、Jinja2テンプレートの標準機能に統一されました。

この移行により、以下の利点が得られます：
- **学習コストの削減**: 業界標準のJinja2テンプレート記法に統一
- **柔軟性の向上**: Jinja2の豊富な機能へのアクセス
- **メンテナンス効率向上**: 重複コードの削除とシンプルなAPI

## 移行パターン

### ArrayAggregateStep → Jinja2フィルタ

#### 合計 (sum)
```yaml
# Before
- id: calculate_total
  method: array_aggregate
  aggregate_operation: "sum"
  input: "{{ numbers }}"

# After  
- id: calculate_total
  method: format
  template: "{{ numbers | sum }}"
```

#### 平均 (avg)
```yaml
# Before
- id: calculate_average
  method: array_aggregate
  aggregate_operation: "avg"
  input: "{{ numbers }}"

# After
- id: calculate_average
  method: format
  template: "{{ (numbers | sum) / (numbers | length) }}"
```

#### カウント (count)
```yaml
# Before
- id: count_items
  method: array_aggregate
  aggregate_operation: "count"
  input: "{{ items }}"

# After
- id: count_items
  method: format
  template: "{{ items | length }}"
```

#### 最小/最大 (min/max)
```yaml
# Before
- id: find_min_max
  method: array_aggregate
  aggregate_operation: "min"  # or "max"
  input: "{{ numbers }}"

# After
- id: find_min_max
  method: format
  template: "{{ numbers | min }}"  # or "{{ numbers | max }}"
```

#### 結合 (join)
```yaml
# Before
- id: join_items
  method: array_aggregate
  aggregate_operation: "join"
  separator: ", "
  input: "{{ items }}"

# After
- id: join_items
  method: format
  template: "{{ items | join(', ') }}"
```

### ArrayFilterStep → Jinja2 for文

#### 基本的なフィルタリング
```yaml
# Before
- id: filter_high_values
  method: array_filter
  condition: "item > 10"
  input: "{{ numbers }}"

# After
- id: filter_high_values
  method: format
  template: |
    [{% for item in numbers if item > 10 %}
      {{ item }}{{ "," if not loop.last }}
    {% endfor %}]
  parse_as_json: true
```

#### オブジェクトのフィルタリング
```yaml
# Before
- id: filter_adults
  method: array_filter
  condition: "int(item['age']) >= 18"
  input: "{{ people }}"

# After
- id: filter_adults
  method: format
  template: |
    [{% for person in people if person.age|int >= 18 %}
      {{ person | tojson }}{{ "," if not loop.last }}
    {% endfor %}]
  parse_as_json: true
```

### ArraySortStep → Jinja2 sortフィルタ

#### 昇順ソート
```yaml
# Before
- id: sort_items
  method: array_sort
  sort_key: "value"
  input: "{{ items }}"

# After
- id: sort_items
  method: format
  template: "{{ items | sort(attribute='value') | tojson }}"
  parse_as_json: true
```

#### 降順ソート
```yaml
# Before
- id: sort_desc
  method: array_sort
  sort_key: "priority"
  sort_reverse: true
  input: "{{ tasks }}"

# After
- id: sort_desc
  method: format
  template: "{{ tasks | sort(attribute='priority', reverse=true) | tojson }}"
  parse_as_json: true
```

### ArrayTransformStep → Jinja2 mapフィルタ

#### 属性の抽出
```yaml
# Before
- id: extract_names
  method: array_transform
  transform_expression: "item['name']"
  input: "{{ people }}"

# After
- id: extract_names
  method: format
  template: "{{ people | map(attribute='name') | list | tojson }}"
  parse_as_json: true
```

#### 計算による変換
```yaml
# Before
- id: calculate_tax
  method: array_transform
  transform_expression: "item * 0.1"
  input: "{{ prices }}"

# After
- id: calculate_tax
  method: format
  template: |
    [{% for price in prices %}
      {{ price * 0.1 }}{{ "," if not loop.last }}
    {% endfor %}]
  parse_as_json: true
```

## 複合操作の例

### フィルタリング + ソート + 変換
```yaml
# Before (複数ステップ)
- id: filter_step
  method: array_filter
  condition: "int(item['salary']) >= 400000"
  input: "{{ employees }}"

- id: sort_step  
  method: array_sort
  sort_key: "salary"
  sort_reverse: true
  input: "{{ steps.filter_step }}"

- id: transform_step
  method: array_transform
  transform_expression: "item['name']"
  input: "{{ steps.sort_step }}"

# After (単一ステップ)
- id: top_earners
  method: format
  template: "{{ employees | selectattr('salary', 'ge', 400000) | sort(attribute='salary', reverse=true) | map(attribute='name') | list | tojson }}"
  parse_as_json: true
```

## よくある質問

### Q: parse_as_jsonはいつ使うべきですか？
A: Jinja2テンプレートでJSONを生成し、それを後続のステップでオブジェクトとして使用したい場合に使用してください。

### Q: 複雑な条件でのフィルタリングはどうすればよいですか？
A: Jinja2の豊富なフィルタとテスト関数を活用できます：
```yaml
template: "{{ items | selectattr('status', 'equalto', 'active') | selectattr('score', 'gt', 85) | list | tojson }}"
```

### Q: エラーハンドリングはどうすればよいですか？
A: Jinja2のデフォルトフィルタを使用：
```yaml
template: "{{ (items | sum) / (items | length | default(1)) }}"
```

### Q: パフォーマンスに影響はありますか？
A: Jinja2テンプレートエンジンは高度に最適化されており、専用ステップと同等またはそれ以上のパフォーマンスを期待できます。

## 参考資料

- [Jinja2テンプレート基礎](../04-templates/jinja2-basics.md)
- [カスタムフィルタ](../04-templates/custom-filters.md)
- [Jinja2公式ドキュメント](https://jinja.palletsprojects.com/)