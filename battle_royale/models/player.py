from dataclasses import dataclass
from typing import List, Dict
import random
import math

@dataclass
class Player:
    id: int
    name: str
    age: int
    occupation: str
    background: str
    health: int = 100
    items: List[str] = None
    skills: Dict[str, int] = None
    is_alive: bool = True
    kills: int = 0
    position: tuple = (0, 0)
    stamina: int = 100
    hunger: int = 100
    thirst: int = 100
    
    def __post_init__(self):
        if self.items is None:
            self.items = []
        if self.skills is None:
            # 基础技能
            self.skills = {
                "combat": self._init_combat_skill(),
                "survival": self._init_survival_skill(),
                "stealth": random.randint(1, 10),
                "medical": self._init_medical_skill(),
                "searching": random.randint(1, 10),
                "crafting": self._init_crafting_skill()
            }
    
    def _init_combat_skill(self) -> int:
        combat_jobs = ["警察", "武术教练", "特种兵教官", "格斗教练", "特技演员"]
        return 8 if self.occupation in combat_jobs else random.randint(1, 6)
    
    def _init_survival_skill(self) -> int:
        survival_jobs = ["猎人", "野外生存专家", "营地教官", "登山家"]
        return 8 if self.occupation in survival_jobs else random.randint(1, 6)
    
    def _init_medical_skill(self) -> int:
        medical_jobs = ["医生", "护士", "兽医", "营养师"]
        return 8 if self.occupation in medical_jobs else random.randint(1, 6)
    
    def _init_crafting_skill(self) -> int:
        craft_jobs = ["工程师", "化学研究生", "机械工程师", "电工"]
        return 8 if self.occupation in craft_jobs else random.randint(1, 6)

    def take_damage(self, damage: int):
        # 如果有防具，伤害减少30%
        if "防具" in self.items:
            damage = int(damage * 0.7)
        # 气功师和武术教练有额外减伤
        if self.occupation in ["气功师", "武术教练"]:
            damage = int(damage * 0.8)
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.is_alive = False
            
    def heal(self, amount: int):
        if self.is_alive:
            # 医生治疗效果提升50%
            if self.occupation == "医生":
                amount = int(amount * 1.5)
            self.health = min(100, self.health + amount)
            
    def move(self, new_position: tuple):
        distance = math.sqrt((new_position[0] - self.position[0])**2 + 
                           (new_position[1] - self.position[1])**2)
        # 运动员体力消耗降低
        stamina_cost = int(distance * (8 if self.occupation in ["跑酷运动员", "运动员"] else 10))
        if self.stamina >= stamina_cost:
            self.stamina -= stamina_cost
            self.position = new_position
            return True
        return False
    
    def use_item(self, item: str) -> bool:
        if item in self.items:
            if item == "医疗包":
                self.heal(50)
            elif item == "食物":
                # 厨师和营养师食用效果提升
                bonus = 1.3 if self.occupation in ["厨师", "营养师"] else 1.0
                self.hunger = min(100, self.hunger + int(30 * bonus))
            elif item == "水":
                self.thirst = min(100, self.thirst + 30)
            elif item == "能量饮料":
                self.stamina = min(100, self.stamina + 50)
            self.items.remove(item)
            return True
        return False
    
    def craft_item(self, materials: List[str]) -> str:
        """尝试制作物品"""
        if self.skills["crafting"] >= 7:
            if set(materials) == {"草药", "绷带"}:
                return "医疗包"
            elif set(materials) == {"布料", "金属"}:
                return "防具"
        return None
    
    def search_area(self) -> List[str]:
        """搜索当前区域"""
        base_items = ["食物", "水", "医疗包", "武器"]
        # 特定职业搜索能力提升
        if self.occupation in ["猎人", "侦探", "特种兵"]:
            base_items.extend(["能量饮料", "防具"])
        return random.sample(base_items, k=min(3, len(base_items)))
    
    def update_status(self):
        # 每回合更新状态
        self.stamina = min(100, self.stamina + 5)
        # 野外生存专家和猎人消耗降低
        hunger_rate = 1 if self.occupation in ["野外生存专家", "猎人"] else 2
        thirst_rate = 2 if self.occupation in ["野外生存专家", "猎人"] else 3
        
        self.hunger -= hunger_rate
        self.thirst -= thirst_rate
        
        if self.hunger <= 0 or self.thirst <= 0:
            damage = 5
            # 运动员和特种兵抗性更强
            if self.occupation in ["运动员", "特种兵"]:
                damage = 3
            self.take_damage(damage) 