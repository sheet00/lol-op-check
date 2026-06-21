import time
import sys
import logging
from data_fetcher import ChampionStatsFetcher
from overlay import OverlayState, OverlayWindow

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ポーリング間隔（秒）
POLLING_INTERVAL = 1.0

def main():
    fetcher = ChampionStatsFetcher()
    overlay_state = OverlayState()
    overlay_window = OverlayWindow(overlay_state)
    overlay_window.show()

    last_fetch_time = 0

    print("LoL OP Checker overlay window started.")
    print("Drag window with Left Click. Close window with Right Click or Escape key.")

    try:
        while True:
            # Tkinterのイベント処理。ウィンドウが閉じられたらループを抜ける。
            if not overlay_window.process_events():
                break

            current_time = time.time()
            # 定期的なポーリング処理
            if current_time - last_fetch_time >= POLLING_INTERVAL:
                try:
                    strongest = fetcher.fetch_strongest_enemy()
                    if strongest:
                        overlay_state.update(
                            status="データ取得成功",
                            strongest_champion=strongest
                        )
                    else:
                        overlay_state.update(
                            status="待機中",
                            strongest_champion=None
                        )
                except Exception as e:
                    logger.error(f"Error fetching data: {e}")
                    overlay_state.update(
                        status="データ取得エラー",
                        strongest_champion=None
                    )
                
                last_fetch_time = current_time

            # CPU負荷を抑えるための短いスリープ
            time.sleep(0.05)

    except KeyboardInterrupt:
        pass
    finally:
        overlay_window.close()
        print("LoL OP Checker stopped.")

if __name__ == "__main__":
    main()
