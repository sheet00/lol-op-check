# Rules & Project Guide

このファイルは、本プロジェクト（LoL OP Checker）の開発を行うAIエージェントおよび開発者が遵守すべきルールと、プロジェクトの設計・仕様をまとめたガイドラインです。

---

## 1. プロジェクト目的 (Purpose)

League of Legends (LoL) の対戦中において、敵チームの中で最も育っている（＝キル・アシストを多く獲得しキャリーしている）警戒すべきチャンピオンをリアルタイムで特定します。
特定したチャンピオンの情報をゲーム画面上の最前面（Tkinterによるオーバーレイ表示）に常時表示し、プレイヤーが警戒対象を一目で把握できるように支援することを目的とします。

---

## 2. サービス構成・アーキテクチャ (Architecture)

プロジェクトのソースコードは [src](file:///C:/Users/sheet/lol-op-check/src) ディレクトリ以下に格納されています。主要なコンポーネントとその役割は以下の通りです。

1. **データ取得レイヤ ([src/data_fetcher.py](file:///C:/Users/sheet/lol-op-check/src/data_fetcher.py))**:
   - クラス: [ChampionStatsFetcher](file:///C:/Users/sheet/lol-op-check/src/data_fetcher.py#L7)
   - ローカルで動作する LoL クライアントの Live Client API (`https://127.0.0.1:2999/liveclientdata/allgamedata`) を定期的にポーリングします。
   - 試合中の全プレイヤー情報から敵チームメンバーのみを抽出し、現在のKDAを基に算出される強さ評価スコアによって最も育っている敵チャンピオンを特定します。

2. **UI表示レイヤ ([src/overlay.py](file:///C:/Users/sheet/lol-op-check/src/overlay.py))**:
   - クラス: [OverlayWindow](file:///C:/Users/sheet/lol-op-check/src/overlay.py#L24)
   - Tkinter を用い、タイトルバーや枠線のない透過的なダークモード調オーバーレイウィンドウを表示します。
   - 常に最前面（`-topmost`）に表示され、左ドラッグによる任意の場所への移動や、右クリック / Escapeキーでの安全な終了に対応します。

3. **メイン制御ループ ([src/main.py](file:///C:/Users/sheet/lol-op-check/src/main.py))**:
   - 関数: [main](file:///C:/Users/sheet/lol-op-check/src/main.py#L17)
   - データ取得とUI更新のライフサイクルを制御するエントリーポイントです。3秒間隔（デフォルト）でデータを取得・更新します。

---

## 3. 技術仕様 (Technical Specifications)

### 3.1. 強さ評価スコアの算出式

敵プレイヤーの強さは、以下の計算式に基づいて算出します。
$$\text{Score} = (\text{Kills} \times 3) + (\text{Assists} \times 1) - (\text{Deaths} \times 2)$$
※最もスコアが高い敵チャンピオンを「最強の敵」として特定します。

### 3.2. Live Client API との接続

- エンドポイント: `https://127.0.0.1:2999/liveclientdata/allgamedata`
- SSL証明書の検証は行いません（自己署名証明書のため、`cert_reqs='CERT_NONE'` で動作させ、`urllib3` の警告出力を抑制します）。

### 3.3. UIの振る舞い

- 初期位置: 画面左上 (`250x80+10+10`)
- ウィンドウ構成:
  - ウィンドウ枠を排除（`overrideredirect(True)`）
  - 近未来的なディープダーク背景（`#080c12`）
  - 右上に `×` ボタンを配置
- イベントハンドリング:
  - 左ドラッグによる移動
  - 右クリック / Escape キーによる終了

---

## 4. 開発ルール (Project Rules)

- **Git コミットメッセージ**:
  - **必ず日本語で記述してください。**
- **エラーハンドリング**:
  - ゲームが起動していない、あるいは試合のロード中など、APIへの接続に失敗した場合は待機状態 (`Waiting for game...`) とし、オーバーレイの表示をリセットして待機状態を維持してください（クラッシュさせないこと）。
- **依存関係と動作環境**:
  - パッケージ管理には `uv` を使用します（[pyproject.toml](file:///C:/Users/sheet/lol-op-check/pyproject.toml) を参照）。
  - Pythonバージョン: `>=3.13`
  - 起動用スクリプトとして Windows PowerShell 向けの [run.ps1](file:///C:/Users/sheet/lol-op-check/run.ps1) が用意されています。
- **プロジェクトファイルの配置**:
  - 新規ファイルやソースコードの修正は、必ず本ワークスペース内に配置してください。
