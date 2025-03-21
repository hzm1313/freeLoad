from agent.core.agent.agent import Agent


def main():
    # 创建工具管理器
    agent = Agent()

    query = "预测苹果未来一个月的股价变化"

    # 执行查询并打印结果
    result = agent.query_with_tools("AAPL", query)
    print("\nQuery result:", result)

if __name__ == "__main__":
    main()
