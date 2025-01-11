import json
import os
from battle_royale.models.player import Player
from battle_royale.core.game_manager import GameManager

def load_players():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, 'config', 'players.json')
    
    with open(config_path, 'r', encoding='utf-8') as f:
        player_data = json.load(f)
    
    players = []
    for i, data in enumerate(player_data):
        player = Player(
            id=i,
            name=data['name'],
            age=data['age'],
            occupation=data['occupation'],
            background=data['background']
        )
        players.append(player)
    return players

def display_game_intro():
    print("="*50)
    print("欢迎来到文字大逃杀游戏！")
    print("游戏规则：")
    print("1. 总共49名参与者")
    print("2. 每15秒为一个回合")
    print("3. 安全区会逐渐缩小")
    print("4. 最后一名生存者获胜")
    print("="*50)
    input("按回车键开始游戏...")

def main():
    display_game_intro()
    players = load_players()
    game = GameManager(players)
    try:
        game.start_game()
    except KeyboardInterrupt:
        print("\n游戏被中断！")
    finally:
        print("游戏结束")

if __name__ == "__main__":
    main() 