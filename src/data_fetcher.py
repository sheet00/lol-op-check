import urllib3
import json
import logging

# SSL証明書のエラー出力を抑制 (Live Client APIはオレオレ証明書のため)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# urllib3 のリトライ警告などがコンソールに出力されるのを抑制する
logging.getLogger("urllib3").setLevel(logging.ERROR)

class ChampionStatsFetcher:
    """
    LoL Live Client API から現在進行中の試合のデータを取得し、
    敵チームの中で最もKDAが良い（育っている）チャンピオンを特定します。
    """
    def __init__(self):
        self.http = urllib3.PoolManager(cert_reqs='CERT_NONE', retries=False)
        self.api_url = "https://127.0.0.1:2999/liveclientdata/allgamedata"

    def fetch_strongest_enemy(self):
        """
        Live Client API からデータを取得し、敵チームの最強チャンピオン情報を返します。
        試合が始まっていない、または接続できない場合は None を返します。
        """
        try:
            # 接続タイムアウトと読み込みタイムアウトをそれぞれ0.2秒に設定し、ソケットのハングを防ぐ
            timeout = urllib3.Timeout(connect=0.2, read=0.2)
            response = self.http.request('GET', self.api_url, timeout=timeout, retries=False)
            if response.status != 200:
                self.http.clear() # 接続不良時はプール内の接続をクリア
                return None
            
            data = json.loads(response.data.decode('utf-8'))
            return self._analyze_strongest_enemy(data)
        except Exception:
            # 接続エラーやタイムアウトが発生した場合は、ハングしたソケットを強制的にクローズしてクリアする
            self.http.clear()
            return None

    def _analyze_strongest_enemy(self, game_data):
        """
        ゲームデータから敵チームのプレイヤーを抽出し、
        最もKDAスコアが高いプレイヤーを特定します。
        """
        # APIレスポンス構造の揺れ（events/Events のキーや大文字小文字など）に依存せず GameEnd イベントを確実に検知する
        events_list = []
        for e_key in ["events", "Events"]:
            if e_key in game_data:
                events_data = game_data[e_key]
                if isinstance(events_data, dict):
                    events_list = events_data.get("Events", [])
                elif isinstance(events_data, list):
                    events_list = events_data
                break
        
        for event in events_list:
            if str(event.get("EventName", "")).lower() == "gameend":
                return None

        active_player = game_data.get("activePlayer")
        all_players = game_data.get("allPlayers", [])

        if not active_player or not all_players:
            return None

        # 自分のチーム名（TEAM_A または TEAM_B）を取得
        my_name = active_player.get("summonerName")
        my_team = None
        for player in all_players:
            if player.get("summonerName") == my_name:
                my_team = player.get("team")
                break

        if not my_team:
            return None

        # 敵チームのプレイヤーだけを抽出
        enemies = [p for p in all_players if p.get("team") != my_team]
        if not enemies:
            return None

        # 自分たちのチーム（自チーム）の平均装備ゴールドを求める
        my_team_players = [p for p in all_players if p.get("team") == my_team]
        my_team_golds = [self._calculate_equipment_gold(p) for p in my_team_players]
        my_team_avg = sum(my_team_golds) / len(my_team_golds) if my_team_golds else 0.0

        strongest_enemy = None
        max_score = -999.0
        strongest_gold = 0

        for enemy in enemies:
            scores = enemy.get("scores", {})
            kills = scores.get("kills", 0)
            deaths = scores.get("deaths", 0)
            assists = scores.get("assists", 0)
            champion_name = enemy.get("championName", "Unknown")

            # スコア計算式: 育っている（キャリーしている）指標
            # キルを最重視し、アシストを加算、デスで減算する単純な強さ評価値
            score = (kills * 3) + (assists * 1) - (deaths * 2)

            if score > max_score:
                max_score = score
                strongest_gold = self._calculate_equipment_gold(enemy)
                strongest_enemy = {
                    "name": champion_name,
                    "kills": kills,
                    "deaths": deaths,
                    "assists": assists,
                    "is_dead": enemy.get("isDead", False),
                    "respawn_timer": int(enemy.get("respawnTimer", 0.0)),
                    "level": enemy.get("level", 1),
                }

        # 最強の敵候補がキルもアシストも獲得していない（全員が0/0/0など、まだ誰も育っていない状態）なら表示しない
        if strongest_enemy and strongest_enemy["kills"] == 0 and strongest_enemy["assists"] == 0:
            return None

        if strongest_enemy:
            # 自チームの平均装備ゴールドに対する倍率を計算
            ratio = strongest_gold / my_team_avg if my_team_avg > 0 else 1.0
            strongest_enemy["gold_ratio"] = round(ratio, 1)

        return strongest_enemy

    def _calculate_equipment_gold(self, player_data):
        """
        対象プレイヤーの現在所持している装備（アイテム）の合計ゴールド価値を計算します。
        """
        total_gold = 0
        items = player_data.get("items", [])
        for item in items:
            price = item.get("price", 0)
            count = item.get("count", 1)
            total_gold += price * count
        return total_gold
