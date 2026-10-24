---
layout: default
title: "Edge Signal Aggregator"
grand_parent: 日本語
parent: スキルガイド
nav_order: 11
lang_peer: /en/skills/edge-signal-aggregator/
permalink: /ja/skills/edge-signal-aggregator/
---

# Edge Signal Aggregator
{: .no_toc }

複数のエッジ検出スキル（edge-candidate-agent、theme-detector、sector-analyst、institutional-flow-tracker）からのシグナルを集約・ランク付けし、加重スコアリング、重複排除、矛盾検出を備えた優先順位付きコンビクションダッシュボードを生成します。
{: .fs-6 .fw-300 }

<span class="badge badge-free">API不要</span>

[スキルパッケージをダウンロード (.skill)](https://github.com/tradermonty/claude-trading-skills/raw/main/skill-packages/edge-signal-aggregator.skill){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[GitHubでソースを見る](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/edge-signal-aggregator){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>目次</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. 概要

複数の上流エッジ検出スキルからの出力を、単一の加重コンビクションダッシュボードに統合します。このスキルは設定可能なシグナルウェイトを適用し、重複するテーマを排除し、スキル間の矛盾をフラグし、複合的なエッジアイデアを集約信頼度スコアでランク付けします。結果として、各寄与スキルへのプロヴェナンスリンク付きの優先順位付けされたエッジショートリストが得られます。

---

## 2. 使用タイミング

- 複数のエッジ検出スキルを実行後、統一的なビューが欲しい場合
- edge-candidate-agent、theme-detector、sector-analyst、institutional-flow-trackerからのシグナルを統合する場合
- 複数のシグナルソースに基づいてポートフォリオ配分の意思決定を行う前
- 異なる分析アプローチ間の矛盾を特定する場合
- どのエッジアイデアがより深いリサーチに値するかを優先順位付けする場合

---

## 3. 前提条件

- Python 3.9+
- APIキー不要（他のスキルからのローカルJSON/YAMLファイルを処理）
- 依存関係: `pyyaml`（ほとんどの環境で標準）

---

## 4. クイックスタート

```bash
python3 skills/edge-signal-aggregator/scripts/aggregate_signals.py \
  --edge-candidates reports/edge_candidate_agent_*.json \
  --edge-concepts reports/edge_concepts_*.yaml \
  --themes reports/theme_detector_*.json \
  --sectors reports/sector_analyst_*.json \
  --institutional reports/institutional_flow_*.json \
  --hints reports/edge_hints_*.yaml \
  --output-dir reports/
```

---

## 5. ワークフロー

### ステップ1: 上流スキル出力の収集

集約したい上流スキルからの出力ファイルを収集します：
- `reports/edge_candidate_*.json` （edge-candidate-agentから）
- `reports/edge_concepts_*.yaml` （edge-concept-synthesizerから）
- `reports/theme_detector_*.json` （theme-detectorから）
- `reports/sector_analyst_*.json` （sector-analystから）
- `reports/institutional_flow_*.json` （institutional-flow-trackerから）
- `reports/edge_hints_*.yaml` （edge-hint-extractorから）

### ステップ2: シグナル集約の実行

上流出力へのパスを指定してアグリゲータースクリプトを実行します：

```bash
python3 skills/edge-signal-aggregator/scripts/aggregate_signals.py \
  --edge-candidates reports/edge_candidate_agent_*.json \
  --edge-concepts reports/edge_concepts_*.yaml \
  --themes reports/theme_detector_*.json \
  --sectors reports/sector_analyst_*.json \
  --institutional reports/institutional_flow_*.json \
  --hints reports/edge_hints_*.yaml \
  --output-dir reports/
```

オプション: カスタムウェイト設定を使用：

```bash
python3 skills/edge-signal-aggregator/scripts/aggregate_signals.py \
  --edge-candidates reports/edge_candidate_agent_*.json \
  --weights-config skills/edge-signal-aggregator/assets/custom_weights.yaml \
  --output-dir reports/
```

### ステップ3: 集約ダッシュボードのレビュー

生成されたレポートを開いてレビューします：
1. **ランク付けされたエッジアイデア** - 複合コンビクションスコアでソート
2. **シグナルプロヴェナンス** - 各アイデアに寄与したスキル（コントリビュータごとの `evidence_id` 付き）
3. **矛盾** - 手動レビュー用にフラグされた相反するシグナル
4. **重複排除ログ** - マージされた重複テーマ（同一証拠の再取得にボーナスは付与されない）
5. **無効シグナル** - NaN/無限大・負・宣言スケール範囲外のスコアは除外して報告され、信頼度に変換されない

### ステップ4: 高コンビクションシグナルへの対応

最小コンビクション閾値でショートリストをフィルタリング：

```bash
python3 skills/edge-signal-aggregator/scripts/aggregate_signals.py \
  --edge-candidates reports/edge_candidate_agent_*.json \
  --min-conviction 0.7 \
  --output-dir reports/
```

---

## 6. リソース

**リファレンス:**

- `skills/edge-signal-aggregator/references/signal-weighting-framework.md`

**スクリプト:**

- `skills/edge-signal-aggregator/scripts/aggregate_signals.py`

---

## 7. プロデューサ契約とスコアリング規則（スキーマ1.1）

スキーマ1.1から、集約は冪等でスコアの妥当性に厳格になりました（Issue #510）：

- **`evidence_id`**（任意・アイテムごと）: 証拠の安定識別子。同一証拠（同じスキル + `evidence_id`）の
  再取得はボーナスを加えません。省略時はスキル・シグナル参照・タイトル・ティッカー・方向から決定論的
  フォールバックを生成します（タイムスタンプは除外され、更新されたタイムスタンプで新規証拠にはなりません）。
  コピー間で内容が異なる場合は最新の観測が優先されます。タイムゾーン付きで解析した最新のタイムスタンプ
  のコピーのスコアを採用し（日付のみ・タイムゾーンなしはUTC扱い）、同時刻・欠落・解析不能の場合は
  最高のraw scoreと安定キーで決めるため、取り込み順序で結果は変わりません。順序付けされるのはISO-8601文字列（または `YYYY-MM-DD`）のみで、エポック数値や `20261010` のような略記はタイムスタンプなしとして扱われます。新しく低いスコアは古く
  高いスコアを置き換え、破棄されたコピーは `deduplication_log[].discarded_copies` に記録されます。
- **`score_scale`**（任意・アイテムまたはドキュメント単位: `"0-1"` / `"0-100"`）: 宣言されたスケールは
  厳格に強制されます。NaN/無限大・負・範囲外の値は `invalid_signals` に除外され、宣言のパースに失敗する
  値（`""`、`"foo"`）は `missing_scale` として拒否されます。キー省略時は (1, 100] の値を0-100とみなし
  （`score_scale_assumed: true` + `scale_assumptions_report`）、100超は拒否します。
- **一致ルール**: ボーナスは `agreement_tier = min(別証拠ID数, 別イベント指紋数, 別スキル数)` で発火。
  同一正規タイトル+ティッカーの逐語的な別スキル再表明は1カウントで自己確認できません。既知の限界:
  イベント指紋は語彙ベースのため、語彙が重ならないパラフレーズ再表明は一致ボーナスを得ます。
- **`merge_bonus_per_duplicate`**（カスタムweights YAML内）は廃止予定で無視されます。
