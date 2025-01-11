import asyncio
import random
from datetime import datetime, timedelta
from ai_chat.core.chat_manager import ChatManager

async def run_community_discussions(chat_manager: ChatManager,
                                  interval_seconds: int = 15,
                                  duration_minutes: int = 60):
    """运行社区讨论"""
    start_time = datetime.now()
    duration = timedelta(minutes=duration_minutes)
    
    while datetime.now() - start_time < duration:
        # 随机选择两个成员进行对话
        available_members = list(chat_manager.community.members.keys())
        if len(available_members) >= 2:
            member1, member2 = random.sample(available_members, 2)
            topic = chat_manager.community.get_random_topic()
            
            print(f"\n[{datetime.now()}] 新的讨论开始:")
            print(f"参与者: {member1} 和 {member2}")
            print(f"话题: {topic}")
            
            # 进行对话
            for _ in range(random.randint(3, 5)):  # 每组进行3-5轮对话
                # member1 发言
                response1 = await chat_manager.generate_conversation(
                    speaker=member1,
                    listener=member2,
                    topic=topic,
                    interval_seconds=interval_seconds
                )
                
                if response1:
                    print(f"\n[{datetime.now()}] {member1}: {response1}")
                    await asyncio.sleep(interval_seconds)
                
                # member2 回应
                response2 = await chat_manager.generate_conversation(
                    speaker=member2,
                    listener=member1,
                    topic=topic,
                    interval_seconds=interval_seconds
                )
                
                if response2:
                    print(f"\n[{datetime.now()}] {member2}: {response2}")
                    await asyncio.sleep(interval_seconds)
            
            print(f"\n[{datetime.now()}] 讨论结束")
        
        await asyncio.sleep(1)

async def main():
    try:
        chat_manager = ChatManager()
        print("启动社区讨论...")
        await run_community_discussions(
            chat_manager=chat_manager,
            interval_seconds=15,
            duration_minutes=60
        )
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"\n发生错误: {e}")
    finally:
        print("\n程序结束")

if __name__ == "__main__":
    asyncio.run(main()) 