# 💡 実用例

実際のユースケースに基づいたワークフロー例を紹介します。

## 💼 実際のファイル例

詳細な実装例は、プロジェクトの[examples/](../../examples/)ディレクトリに保存されています：

- `examples/ja/` - 日本語の実用例
- `examples/en/` - 英語の実用例  
- `examples/large_output_demo.yml` - 長大出力制御のデモンストレーション
- 各カテゴリ別のサンプルワークフロー

## 🚀 特殊機能のデモ

### 長大出力制御デモ
`examples/large_output_demo.yml`では、MCPサーバで大容量出力を効率的に処理する方法を実演します：

- ワークフロー定義での明示的制御（`large_output_control: true`）
- 複数段階の文書分析
- ファイル出力による結果管理

**使用例：**
```bash
# 小容量分析
bakufu run examples/large_output_demo.yml --input '{
  "document_content": "短いドキュメント...", 
  "analysis_depth": "basic"
}'

# 大容量分析（ファイル出力推奨）
bakufu run examples/large_output_demo.yml --input '{
  "document_content": {"type": "file", "data": "large_doc.txt", "format": "text"},
  "analysis_depth": {"type": "value", "data": "comprehensive"}
}'
```

### Jinja2テンプレート形式化デモ（v1.2.0新機能）
`examples/format_step_examples.yaml`では、AI呼び出しなしで純粋なJinja2テンプレート処理によるテキスト形式化の様々な使用法を実演します：

- **基本的なテンプレート変数置換**
- **条件分岐（if/else）によるメッセージ変更**
- **ループ処理とフィルタを組み合わせた商品レポート生成**
- **ステップ結果の参照と加工**
- **マクロ定義による価格フォーマット関数**
- **日時機能とグローバル関数の活用**

**主要な活用場面**:
- **セキュリティチェックリストのバッチ処理**: 複数項目を3つずつまとめて処理
- **売上レポートの自動生成**: データを集計・分析して見やすい形式で出力
- **条件に応じた動的メッセージ生成**: ユーザー属性に基づく個別対応
- **複雑なデータ変換処理**: JSON、CSV等の構造化データを読みやすい形式に変換

**使用例：**
```bash
# 基本的なテンプレート変数置換
bakufu run examples/format_step_examples.yaml --input '{
  "user_name": "田中太郎",
  "user_age": 30
}'

# 商品データを含む詳細レポート生成
bakufu run examples/format_step_examples.yaml --input '{
  "user_name": "田中太郎",
  "user_age": 30,
  "product_list": [
    {"name": "ノートPC", "price": 120000, "category": "electronics"},
    {"name": "コーヒー豆", "price": 1500, "category": "food"}
  ]
}'
```

**特徴**:
- **高速処理**: AI呼び出しなしのため非常に高速
- **複雑な制御構造**: 条件分岐、ループ、マクロなどを自由に使用
- **ステップ間のデータ連携**: 前のステップの結果を動的に参照・加工
- **実用的なパターン**: 実際のビジネスシーンで使える形式化テンプレート

## 🔗 関連セクション

- [ユーザーガイド](../02-user-guide/README.md) - 基本的な作成方法
- [機能リファレンス](../03-features/README.md) - 各機能の詳細
- [テンプレートシステム](../04-templates/README.md) - テンプレート活用

---

📖 [ドキュメント目次に戻る](../README.md)