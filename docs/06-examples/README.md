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
  "document_content": "@file:large_doc.txt:text",
  "analysis_depth": "comprehensive",
  "output_file_path": "/reports/analysis.txt"
}'
```

## 🔗 関連セクション

- [ユーザーガイド](../02-user-guide/README.md) - 基本的な作成方法
- [機能リファレンス](../03-features/README.md) - 各機能の詳細
- [テンプレートシステム](../04-templates/README.md) - テンプレート活用

---

📖 [ドキュメント目次に戻る](../README.md)