from typing import List
import random
from ..models.player import Player

class EventSystem:
    def __init__(self):
        self.event_types = {
            "combat": 0.3,
            "item_found": 0.2,
            "trap": 0.15,
            "supply_drop": 0.1,
            "special_event": 0.25
        }
        
        self.special_events = {
            "毒雾扩散": self._handle_poison_fog,
            "补给空投": self._handle_supply_drop,
            "区域封锁": self._handle_area_lockdown,
            "野生动物来袭": self._handle_animal_attack
        }
    
    def generate_event(self, player: Player, alive_players: List[Player]):
        event = random.choices(
            list(self.event_types.keys()),
            list(self.event_types.values())
        )[0]
        
        if event == "special_event":
            special_event = random.choice(list(self.special_events.keys()))
            return self.special_events[special_event](player)
        
        return self._handle_basic_event(event, player, alive_players)
    
    def _handle_basic_event(self, event: str, player: Player, alive_players: List[Player]):
        if event == "combat":
            return self._handle_combat(player, alive_players)
        elif event == "item_found":
            return self._handle_item_found(player)
        elif event == "trap":
            return self._handle_trap(player)
        elif event == "supply_drop":
            return self._handle_supply_drop(player)
    
    def _handle_combat(self, player: Player, alive_players: List[Player]):
        opponents = [p for p in alive_players if p != player]
        if not opponents:
            return f"{player.name} 没有找到对手"
            
        opponent = random.choice(opponents)
        combat_power = player.skills["combat"] * random.random()
        opponent_power = opponent.skills["combat"] * random.random()
        
        # 特定职业战斗力加成
        if player.occupation in ["警察", "特种兵", "武术教练"]:
            combat_power *= 1.2
        if opponent.occupation in ["警察", "特种兵", "武术教练"]:
            opponent_power *= 1.2
            
        if combat_power > opponent_power:
            damage = random.randint(20, 50)
            opponent.take_damage(damage)
            if not opponent.is_alive:
                player.kills += 1
            return f"{player.name} 在战斗中击败了 {opponent.name}，造成 {damage} 点伤害"
        else:
            damage = random.randint(20, 50)
            player.take_damage(damage)
            if not player.is_alive:
                opponent.kills += 1
            return f"{opponent.name} 在战斗中击败了 {player.name}，造成 {damage} 点伤害"
    
    def _handle_item_found(self, player: Player):
        found_items = player.search_area()
        for item in found_items:
            player.items.append(item)
        return f"{player.name} 找到了 {', '.join(found_items)}"
    
    def _handle_trap(self, player: Player):
        # 特定职业可能避免陷阱
        if player.occupation in ["特种兵", "猎人"] and random.random() < 0.4:
            return f"{player.name} 成功避开了陷阱"
            
        damage = random.randint(10, 30)
        player.take_damage(damage)
        return f"{player.name} 触发了陷阱，受到 {damage} 点伤害"
    
    def _handle_poison_fog(self, player: Player):
        # 防毒专家和医生受到的伤害更少
        damage = random.randint(5, 15)
        if player.occupation in ["防毒专家", "医生"]:
            damage = int(damage * 0.6)
        player.take_damage(damage)
        return f"毒雾扩散！{player.name} 受到 {damage} 点伤害"
    
    def _handle_supply_drop(self, player: Player):
        items = ["高级医疗包", "防弹衣", "能量饮料", "军用口粮"]
        gained_items = random.sample(items, k=2)
        for item in gained_items:
            player.items.append(item)
        return f"{player.name} 获得了空投补给: {', '.join(gained_items)}"
    
    def _handle_area_lockdown(self, player: Player):
        if not player.move((random.randint(0, 100), random.randint(0, 100))):
            damage = random.randint(10, 20)
            player.take_damage(damage)
            return f"{player.name} 未能及时撤离封锁区域，受到 {damage} 点伤害"
        return f"{player.name} 成功撤离了封锁区域"
    
    def _handle_animal_attack(self, player: Player):
        # 兽医和猎人更容易应对野生动物
        if player.occupation in ["兽医", "猎人"] and random.random() < 0.6:
            return f"{player.name} 成功驯服了野生动物"
            
        damage = random.randint(15, 35)
        player.take_damage(damage)
        return f"{player.name} 遭到野生动物攻击，受到 {damage} 点伤害" 