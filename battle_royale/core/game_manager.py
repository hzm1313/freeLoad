import time
from typing import List, Tuple
import random
from ..models.player import Player
from .event_system import EventSystem

class GameManager:
    def __init__(self, players: List[Player]):
        self.players = players
        self.round = 0
        self.max_rounds = 240  # 1小时 = 240个15秒轮次
        self.start_time = None
        self.game_over = False
        self.map_size = (100, 100)  # 地图大小
        self.safe_zone = (100, 100)  # 安全区大小
        self.danger_zones = []  # 危险区域
        self.event_system = EventSystem()
        
    def start_game(self):
        self.start_time = time.time()
        self._initialize_player_positions()
        print("游戏开始！")
        print(f"总人数: {len(self.players)}")
        self._display_map_info()
        
        while not self.game_over and self.round < self.max_rounds:
            self.play_round()
            time.sleep(15)

    def _initialize_player_positions(self):
        # 随机分配玩家初始位置
        for player in self.players:
            player.position = (
                random.randint(0, self.map_size[0]),
                random.randint(0, self.map_size[1])
            )
    
    def play_round(self):
        self.round += 1
        alive_players = [p for p in self.players if p.is_alive]
        
        print(f"\n第 {self.round} 轮开始")
        print(f"存活人数: {len(alive_players)}")
        
        # 更新安全区
        if self.round % 10 == 0:
            self._update_safe_zone()
            self._display_map_info()
        
        # 更新玩家状态
        for player in alive_players:
            player.update_status()
            self._check_zone_damage(player)
        
        # 生成事件
        self._generate_round_events(alive_players)
        
        # 显示玩家状态
        self._display_players_status(alive_players)
        
        # 检查游戏是否结束
        self._check_game_end(alive_players)

    def _update_safe_zone(self):
        # 缩小安全区
        new_size = (int(self.safe_zone[0] * 0.8), int(self.safe_zone[1] * 0.8))
        self.safe_zone = new_size
        print(f"\n安全区缩小！新的安全区大小: {new_size[0]}x{new_size[1]}")
        
        # 更新危险区域
        danger_x = random.randint(0, self.map_size[0] - new_size[0])
        danger_y = random.randint(0, self.map_size[1] - new_size[1])
        self.danger_zones.append((danger_x, danger_y, new_size[0], new_size[1]))

    def _check_zone_damage(self, player: Player):
        x, y = player.position
        in_safe_zone = False
        
        # 检查是否在任何安全区内
        for zone in self.danger_zones:
            zone_x, zone_y, width, height = zone
            if (zone_x <= x <= zone_x + width and 
                zone_y <= y <= zone_y + height):
                in_safe_zone = True
                break
        
        if not in_safe_zone:
            damage = 10
            player.take_damage(damage)
            print(f"{player.name} 受到毒圈伤害 {damage}")

    def _generate_round_events(self, alive_players: List[Player]):
        print("\n本回合事件：")
        for player in alive_players:
            if random.random() < 0.3:  # 30%概率触发事件
                event_result = self.event_system.generate_event(player, alive_players)
                print(event_result)

    def _display_map_info(self):
        print("\n地图信息：")
        print(f"地图大小: {self.map_size[0]}x{self.map_size[1]}")
        print(f"当前安全区: {self.safe_zone[0]}x{self.safe_zone[1]}")
        if self.danger_zones:
            print("危险区域：")
            for i, zone in enumerate(self.danger_zones, 1):
                print(f"区域{i}: 位置({zone[0]},{zone[1]}) 大小{zone[2]}x{zone[3]}")

    def _display_players_status(self, alive_players: List[Player]):
        print("\n存活玩家状态:")
        for player in alive_players:
            print(f"{player.name}: HP:{player.health} 饥饿:{player.hunger} "
                  f"口渴:{player.thirst} 体力:{player.stamina} "
                  f"位置:({player.position[0]},{player.position[1]}) "
                  f"物品:{len(player.items)}个")

    def _check_game_end(self, alive_players: List[Player]):
        if len(alive_players) == 1:
            self.game_over = True
            winner = alive_players[0]
            print(f"\n游戏结束！获胜者是: {winner.name}")
            self._display_winner_stats(winner)
        elif len(alive_players) == 0:
            self.game_over = True
            print("\n游戏结束！无人生还")

    def _display_winner_stats(self, winner: Player):
        print("\n胜利者详细信息:")
        print(f"姓名: {winner.name}")
        print(f"职业: {winner.occupation}")
        print(f"背景: {winner.background}")
        print(f"击杀数: {winner.kills}")
        print(f"剩余生命值: {winner.health}")
        print(f"剩余物品: {', '.join(winner.items)}")
        print(f"技能等级:")
        for skill, level in winner.skills.items():
            print(f"  {skill}: {level}")
        
        game_duration = time.time() - self.start_time
        print(f"\n游戏持续时间: {int(game_duration/60)}分{int(game_duration%60)}秒") 