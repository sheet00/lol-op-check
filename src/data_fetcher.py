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
        self.item_prices = self._load_item_prices()

    def _load_item_prices(self):
        """
        Riot Data Dragon から最新のアイテムIDと価格（Total Cost）のマップを取得します。
        失敗した場合は空の辞書を返し、API側の価格にフォールバックします。
        """
        try:
            # 最新のゲームバージョンを取得
            v_res = self.http.request('GET', 'https://ddragon.leagueoflegends.com/api/versions.json', timeout=1.5)
            if v_res.status != 200:
                return {}
            versions = json.loads(v_res.data.decode('utf-8'))
            latest_version = versions[0]

            # アイテムの定義データを取得
            item_url = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/ja_JP/item.json"
            i_res = self.http.request('GET', item_url, timeout=2.5)
            if i_res.status != 200:
                return {}
            item_data = json.loads(i_res.data.decode('utf-8'))

            prices = {}
            for item_id, item_info in item_data.get("data", {}).items():
                gold_info = item_info.get("gold", {})
                prices[int(item_id)] = gold_info.get("total", 0)
            return prices
        except Exception:
            return {}

    def fetch_strongest_enemy(self):
        """
        Live Client API からデータを取得し、敵チームの最強チャンピオン情報を返します。
        取得した生データはデバッグ用に live_game_data.json に保存します。
        """
        try:
            # 接続タイムアウトと読み込みタイムアウトをそれぞれ0.2秒に設定し、ソケットのハングを防ぐ
            timeout = urllib3.Timeout(connect=0.2, read=0.2)
            response = self.http.request('GET', self.api_url, timeout=timeout, retries=False)
            if response.status != 200:
                self.http.clear() # 接続不良時はプール内の接続をクリア
                return None
            
            data = json.loads(response.data.decode('utf-8'))
            
            # ログとして取得した生データをJSONファイルとして保存
            try:
                with open("live_game_data.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

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

        # 自分自身の装備ゴールドを求める
        my_gold = 0.0
        for p in my_team_players:
            if p.get("summonerName") == my_name:
                my_gold = self._calculate_equipment_gold(p)
                break

        strongest_enemy = None
        max_score = -9999.0
        strongest_gold = 0.0

        for enemy in enemies:
            scores = enemy.get("scores", {})
            kills = scores.get("kills", 0)
            deaths = scores.get("deaths", 0)
            assists = scores.get("assists", 0)
            champion_name = enemy.get("championName", "Unknown")

            # KDAスコアの計算 (Kills * 3 + Assists * 1 - Deaths * 2)
            kda_score = kills * 3 + assists * 1 - deaths * 2

            # 装備ゴールドの計算
            equipment_gold = self._calculate_equipment_gold(enemy)

            # 純粋にKDAスコアが一番大きいやつを特定 (同点の場合は装備ゴールドが多い方を優先)
            if kda_score > max_score or (kda_score == max_score and equipment_gold > strongest_gold):
                max_score = kda_score
                strongest_gold = equipment_gold
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
            # 自チームの平均装備ゴールドに対する倍率を求め、4乗モデルで戦闘力比率を計算
            enemy_base_ratio = strongest_gold / my_team_avg if my_team_avg > 0 else 1.0
            ratio = enemy_base_ratio ** 4
            strongest_enemy["gold_ratio"] = round(ratio, 2)
            
            # 自分自身の戦闘力比率を計算
            my_base_ratio = my_gold / my_team_avg if my_team_avg > 0 else 1.0
            my_ratio = my_base_ratio ** 4
            strongest_enemy["my_gold_ratio"] = round(my_ratio, 2)

        return strongest_enemy

    def _calculate_equipment_gold(self, player_data):
        """
        対象プレイヤーの現在所持している装備（アイテム）の合計ゴールド価値を計算します。
        Data Dragon から取得した正しい価格を優先し、なければAPIの price にフォールバックします。
        """
        total_gold = 0
        items = player_data.get("items", [])
        for item in items:
            item_id = item.get("itemID", 0)
            price = self.item_prices.get(item_id, item.get("price", 0))
            count = item.get("count", 1)
            total_gold += price * count
        return total_gold
