---
layout: default
title: 日本語
nav_order: 2
has_children: true
lang_peer: /en/
permalink: /ja/
---

# Claude Trading Skills
{: .no_toc }

<div class="hero">
  <p class="hero-mantra">Empower Solo Traders and Growing Together</p>
  <p class="hero-tagline">Claudeが動かす、あなた専用のマーケットアナリスト</p>
</div>

## Claude Trading Skillsとは？

Claude Trading Skillsは、株式投資家やトレーダーのための**Claudeスキル集**です。各スキルはドメイン固有のプロンプト、ナレッジベース、ヘルパースクリプトをパッケージ化しており、Claudeがマーケット分析、銘柄スクリーニング、戦略検証、ポートフォリオ管理などを支援します。

自然言語で指示するだけで、構造化されたレポートとアクション可能なインサイトを取得できます。

<div class="category-cards">
  <div class="category-card">
    <h3>銘柄スクリーニング</h3>
    <p>CANSLIM、VCP、FinViz、配当スクリーナーなど、複数の投資手法に基づくスクリーニングスキル群。自然言語で条件を伝えるだけで候補銘柄リストを生成します。</p>
  </div>
  <div class="category-card">
    <h3>マーケット分析</h3>
    <p>セクターローテーション、市場幅（ブレッド）、テクニカル分析、ニュース分析など、市場全体の健全性と方向性を評価するスキル群。</p>
  </div>
  <div class="category-card">
    <h3>戦略・リサーチ</h3>
    <p>バックテスト、オプション戦略、テーマ検出、ペアトレードなど、投資戦略の構築と検証を支援するスキル群。</p>
  </div>
  <div class="category-card">
    <h3>ポートフォリオ・執行</h3>
    <p>Portfolio Manager、Position Sizer、決算カレンダーなど、保有管理からポジションサイジング、イベント監視までカバーするスキル群。</p>
  </div>
</div>

---

## 3ステップで始める

<div class="steps">
  <div class="step">
    <span class="step-number">1</span>
    <h4>インストール</h4>
    <p><code>.skill</code>ファイルをClaude Web Appにアップロード、またはリポジトリをクローンしてClaude Codeに配置します。</p>
  </div>
  <div class="step">
    <span class="step-number">2</span>
    <h4>自然言語で指示</h4>
    <p>探したい条件やリサーチしたい内容をClaudeに日本語（または英語）で伝えます。</p>
  </div>
  <div class="step">
    <span class="step-number">3</span>
    <h4>分析結果を取得</h4>
    <p>構造化されたレポートとアクション可能なインサイトをMarkdown + JSON形式で受け取ります。</p>
  </div>
</div>

---

## 出力プレビュー

架空データによる表示例です。ワークフロー提案、相場方針、週次振り返りの形式を示します。現在の相場情報や売買指示ではありません。

画像を選ぶと原寸のSVGを開けます。スマートフォンでは開いた後に拡大できます。

[![架空の毎朝15分の確認目標に対し、必要な3スキルと有料API不要の経路を示すNavigatorの出力例]({{ '/assets/previews/navigator-recommendation.svg' | relative_url }})]({{ '/assets/previews/navigator-recommendation.svg' | relative_url }})

**ワークフローを選ぶ:** [Trading Skills Navigator]({{ '/ja/skills/trading-skills-navigator/' | relative_url }})が目的に合うワークフローと導入スキルを提案します。

[![架空のスコアから計算した上限36%、REDUCE_ONLY、重要入力不足によるLOWの信頼度を示す方針の出力例]({{ '/assets/previews/market-posture.svg' | relative_url }})]({{ '/assets/previews/market-posture.svg' | relative_url }})

**相場リスクを確認する:** [市場レジーム日次ワークフロー]({{ '/ja/workflows/' | relative_url }})の最後に人間が確認する方針を示します。

[![架空の決済済み4取引を使い、勝率50%と実現損益プラス75ドルを示す週次振り返りの出力例]({{ '/assets/previews/weekly-digest.svg' | relative_url }})]({{ '/assets/previews/weekly-digest.svg' | relative_url }})

**決済済み取引を振り返る:** [Weekly Performance Digest]({{ '/ja/skills/weekly-performance-digest/' | relative_url }})が実現損益と改善点を整理します。

---

## 注目スキル

| スキル | 概要 | API |
|--------|------|-----|
| [FinViz Screener]({{ '/ja/skills/finviz-screener/' | relative_url }}) | 自然言語でFinVizスクリーニング条件を構築し、Chromeで結果を表示 | 不要 |
| [CANSLIM Screener]({{ '/ja/skills/canslim-screener/' | relative_url }}) | William O'NeilのCANSLIM手法で成長株を7コンポーネントスコアリング | FMP必須 |
| [VCP Screener]({{ '/ja/skills/vcp-screener/' | relative_url }}) | MinerviniのVolatility Contraction Patternを自動検出 | FMP必須 |
| [Theme Detector]({{ '/ja/skills/theme-detector/' | relative_url }}) | クロスセクターの上昇・下落テーマを3次元スコアリングで検出 | 任意 |

全スキルの一覧は[スキル一覧]({{ '/ja/skill-catalog/' | relative_url }})をご覧ください。

---

## 運用ワークフロー

複数スキルを組み合わせる Core + Satellite 運用導線は [ワークフロー]({{ '/ja/workflows/' | relative_url }}) を参照してください。各ワークフローは使用スキル・判断ゲート・artifact を順番通りに記述しており、`workflows/*.yaml` の正本 manifest から自動生成されます。

[スキルセット]({{ '/ja/skillsets/' | relative_url }}) はその対となる「目的のために何を入れるか」の層で、各ワークフローに紐づくカテゴリ単位のスキル束です。`skillsets/*.yaml` から自動生成されます。

---

## はじめに

初めての方は[はじめに]({{ '/ja/getting-started/' | relative_url }})ページで、インストール手順とAPIキーの設定方法を確認してください。
