# 長大出力制御

MCPサーバーでの長大出力制御機能の詳細仕様とガイドです。

## 概要

MCPクライアントで長大なワークフロー出力を扱う際の問題（コンテキストウィンドウ飽和、パフォーマンス低下）を解決するため、bakufuは2つの制御方式を提供します。

## 2つの制御方式

### 制御方式1: ワークフロー定義での明示的設定

ワークフロー定義に`large_output_control: true`を追加することで、`output_file_path`パラメータを必須にします。

#### ワークフロー定義

```yaml
name: "comprehensive_document_analyzer"
description: "大容量ドキュメントの包括的分析"
output:
  format: "text"
  large_output_control: true
  template: |
    # 分析結果
    {{ steps.detailed_analysis }}
```

#### 使用方法

MCPツールレベルで`input`と`output_file_path`を並列引数として指定：

**引数:**
- input: `{"document": "@file:/path/to/large_document.pdf:text", "analysis_type": "comprehensive"}`
- output_file_path: `"/reports/analysis_result.txt"`

**応答:** `"✅ Results saved to: /absolute/path/to/reports/analysis_result.txt"`

#### 特徴

- **明示的制御**: 開発者が意図的にファイル出力を強制
- **必須パラメータ**: `large_output_control: true`の場合、`output_file_path`が必須
- **責任分離**: ワークフロー固有パラメータとMCP制御パラメータの明確な分離

### 制御方式2: グローバル設定による自動対応

設定可能な閾値を超えた場合、自動的にファイル出力を行います。

#### 設定ファイル

```yaml
# bakufu.yml
mcp_max_output_chars: 8000
mcp_auto_file_output_dir: "./mcp_outputs"
```

#### 使用方法

通常のワークフロー実行で、出力サイズが閾値を超えた場合に自動処理：

**引数:**
- input: `{"@file:dataset": "/data/large_dataset.csv:csv", "processing_type": "full_analysis"}`

**応答（75KB出力の場合）:**
`"🔄 Large output detected (76,543 characters). Results automatically saved to: ./mcp_outputs/data_batch_processor_1640995200000.txt"`

#### 特徴

- **透明性**: 既存ワークフローの変更不要
- **自動判定**: 出力サイズに基づく自動処理
- **フォールバック**: 自動保存失敗時は切り捨て出力

## 設定オプション

### 基本設定

| 設定項目 | デフォルト値 | 説明 |
|---------|-------------|------|
| `mcp_max_output_chars` | 8000 | 自動ファイル出力の閾値（文字数） |
| `mcp_auto_file_output_dir` | `"./mcp_outputs"` | 自動ファイル出力ディレクトリ |

### 設定例

```yaml
# bakufu.yml - 長大出力制御設定
mcp_max_output_chars: 10000           # 10KB閾値に変更
mcp_auto_file_output_dir: "/tmp/bakufu_outputs"  # 出力先変更
```

## エラー処理とフォールバック

システムは以下の優先順位でエラー処理を行います：

1. **第1選択**: 明示的ファイル出力（`output_file_path`指定時）
2. **第2選択**: 自動ファイル保存（閾値超過時）
3. **最終手段**: 全文出力（保存失敗時）

### エラーケース

#### ファイル書き込み失敗

```
⚠️ Large result (75,432 characters) returned as full text (file save failed):

[結果の全文]
```

#### ディスク容量不足

自動的に全文出力にフォールバックし、警告メッセージを表示します。

## MCPツール構造

各ワークフローは以下の構造でMCPツールとして公開されます：

```
ツール引数:
├── input (object)          # ワークフロー固有のパラメータ
└── output_file_path (string, optional)  # MCP共通の制御パラメータ
```

### 引数の詳細

#### input引数
- **型**: JSONオブジェクト
- **内容**: ワークフロー定義の`input_parameters`で定義されたパラメータ
- **例**: `{"document": "content...", "analysis_type": "detailed"}`

#### output_file_path引数
- **型**: 文字列（オプショナル）
- **用途**: ファイル出力パスの指定
- **例**: `"/path/to/output.txt"`

## 実用例

### 例1: 法的文書の詳細分析

**ワークフロー定義:**
```yaml
name: "legal_document_analyzer"
output:
  large_output_control: true
```

**使用:**
- input: `{"@file:contract": "/legal/contract.pdf:text", "analysis_type": "compliance"}`
- output_file_path: `"/legal/analysis/contract_analysis.txt"`

### 例2: データセットの統計分析

**使用:**
- input: `{"@file:data": "/data/sales_2024.csv:csv", "metrics": ["revenue", "growth"]}`

**自動応答（大容量の場合）:**
`"🔄 Large output detected (45,832 characters). Results automatically saved to: /absolute/path/to/mcp_outputs/data_analyzer_1704067200000.txt"`

### 例3: ソースコードレビュー

**使用:**
- input: `{"@file:code": "/src/main.py:text", "review_level": "comprehensive"}`
- output_file_path: `"/reviews/main_py_review.md"`

## セキュリティ考慮事項

### ファイルシステムセキュリティ

- **パストラバーサル防止**: `../`等の危険なパスパターンの検証
- **権限確認**: ファイル書き込み権限の事前チェック
- **一時ファイル管理**: 自動削除とセキュアな保存場所

### 機密情報の処理

- **ファイルパス検証**: 機密ディレクトリへのアクセス防止
- **出力内容確認**: 機密情報の意図しない出力防止
- **アクセス制御**: 出力ファイルの適切な権限設定

## パフォーマンス最適化

### ファイル操作の最適化

- **非同期処理**: `aiofiles`による非ブロッキング書き込み
- **ストリーミング**: 大容量データの段階的処理
- **圧縮**: 必要に応じた出力の圧縮

### メモリ管理

- **メモリ効率**: 大容量データの一時保存を最小化
- **ガベージコレクション**: 処理完了後の適切なリソース解放

## トラブルシューティング

### よくある問題

#### 1. ファイル出力されない

**症状**: `large_output_control: true`なのにファイル出力されない

**解決策**:
- `output_file_path`パラメータが正しく指定されているか確認
- ファイルパスの権限とディレクトリの存在を確認

#### 2. 自動保存されない

**症状**: 大きな出力が切り捨てられる

**解決策**:
- `mcp_max_output_chars`設定を確認
- `mcp_auto_file_output_dir`の書き込み権限を確認

#### 3. パフォーマンス問題

**症状**: ファイル書き込みが遅い

**解決策**:
- SSDストレージの使用
- `mcp_auto_file_output_dir`を高速ストレージに配置

### デバッグ

詳細なログで問題を特定：

```bash
# デバッグログ有効化
bakufu-mcp --workflow-dir examples --verbose
```

ログには以下の情報が含まれます：
- ファイル出力の試行と結果
- 自動保存の判定プロセス
- エラーとフォールバック処理

## Claude Desktop設定例

```json
{
  "mcpServers": {
    "bakufu": {
      "command": "bakufu-mcp",
      "args": ["--workflow-dir", "/path/to/workflows", "--config", "bakufu.yml"]
    }
  }
}
```

## プログラマティックアクセス例

```python
import asyncio
from bakufu.mcp_integration import MCPWorkflowIntegrator

async def process_large_document():
    integrator = MCPWorkflowIntegrator()
    
    result = await integrator.execute_workflow(
        "document_analyzer",
        {"document": large_document_content},
        output_file_path="/reports/analysis.txt"
    )
    
    if result.success:
        print(f"分析完了: {result.result}")
    else:
        print(f"エラー: {result.error_message}")
```

## 関連ドキュメント

- [MCP統合](mcp-integration.md) - MCP統合の全体概要
- [設定リファレンス](../08-reference/configuration.md) - 詳細な設定オプション
- [セキュリティガイド](../08-reference/security.md) - セキュリティのベストプラクティス

---

このドキュメントは、長大出力制御機能の包括的なガイドです。具体的な実装例や詳細な設定については、関連ドキュメントを参照してください。