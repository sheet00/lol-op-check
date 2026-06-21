import urllib3
import json

# SSL証明書のエラー出力を抑制 (Live Client APIはオレオレ証明書のため)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ChampionStatsFetcher:
    """
    LoL Live Client API から現在進行中の試合のデータを取得し、
    敵チームの中で最もKDAが良い（育っている）チャンピオンを特定します。
    """
    def __init__(self):
        self.http = urllib3.PoolManager(cert_reqs='CERT_NONE')
        self.api_url = "https://127.0.0.1:2999/liveclientdata/allgamedata"

    def fetch_strongest_enemy(self):
        """
        Live Client API からデータを取得し、敵チームの最強チャンピオン情報を返します。
        試合が始まっていない、または接続できない場合は None を返します。
        """
        try:
            # 接続タイムアウトと読み込みタイムアウトをそれぞれ1秒に設定し、ソケットのハングを防ぐ
            timeout = urllib3.Timeout(connect=1.0, read=1.0)
            response = self.http.request('GET', self.api_url, timeout=timeout)
            if response.status != 200:
                return None
            
            data = json.loads(response.data.decode('utf-8'))
            return self._analyze_strongest_enemy(data)
        except Exception:
            # 接続エラー（LoLが起動していない、試合中でないなど）の場合は None
            return None

    def _analyze_strongest_enemy(self, game_data):
        """
        ゲームデータから敵チームのプレイヤーを抽出し、
        最もKDAスコアが高いプレイヤーを特定します。
        """
        # 試合終了イベント（GameEnd）が記録されている場合は、試合終了とみなして None を返す
        events = game_data.get("events", {}).get("Events", [])
        for event in events:
            if event.get("EventName") == "GameEnd":
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

        strongest_enemy = None
        max_score = -999.0

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
                strongest_enemy = {
                    "name": champion_name,
                    "kills": kills,
                    "deaths": deaths,
                    "assists": assists,
                    "is_dead": enemy.get("isDead", False),
                }

        return strongest_enemy
