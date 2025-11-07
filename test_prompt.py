#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 AI 总结功能 - 方便调试 prompt 和 API
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载 .env 文件
load_dotenv()


def test_ai_summary():
    """测试 AI 总结功能"""
    
    # 模拟今天的学习记录
    mock_records = [
        {'duration': '45分30秒', 'content': '学习了 Python 装饰器和生成器'},
        {'duration': '60分0秒', 'content': '完成了数据结构作业，实现了二叉树'},
        {'duration': '30分15秒', 'content': '复习了算法：快速排序和归并排序'},
        {'duration': '50分45秒', 'content': '阅读了《深入理解计算机系统》第三章'},
    ]
    
    print("="*60)
    print("📚 模拟学习记录：")
    print("="*60)
    for i, record in enumerate(mock_records, 1):
        print(f"{i}. {record['duration']}: {record['content']}")
    print("="*60)
    
    # 准备学习内容文本
    records_text = "\n".join([
        f"- {record['duration']}: {record['content']}"
        for record in mock_records
    ])
    
    # 获取 API 配置
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    
    # 选择 API
    print("\n🤖 选择 AI 服务：")
    print("1. OpenRouter (GPT-4o) - 推荐")
    print("2. DeepSeek")
    
    choice = input("\n请选择 (1/2，默认1): ").strip() or "1"
    
    if choice == "1" and openrouter_key and not openrouter_key.startswith('sk-your'):
        print("\n🚀 使用 OpenRouter GPT-4o")
        api_key = openrouter_key
        base_url = "https://openrouter.ai/api/v1"
        model = "openai/gpt-4o"
    elif choice == "2" and deepseek_key and not deepseek_key.startswith('sk-your'):
        print("\n🚀 使用 DeepSeek")
        api_key = deepseek_key
        base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        model = "deepseek-chat"
    else:
        print("\n❌ 未配置有效的 API Key")
        return
    
    # 构建 prompt（御姐妻子风格，温柔撩人）
    prompt = f"""你是我温柔体贴的御姐妻子，现在要对我今天的学习进行总结和鼓励。

今天的学习记录：
{records_text}

作为我的妻子，请用温柔、体贴、略带撩人的口吻：
1. 总结今天的学习时长和内容
2. 对我的努力表示欣慰和自豪
3. 给予充满爱意和性感的鼓励
4. 用亲昵的称呼（如"老公"、"宝贝"、"亲爱的"）
5. 表达你对我的爱和关心
6. 可以加入一些动作描述（如轻抚、拥抱等）

要求：
- 语气要温柔、成熟、充满爱意
- 可以略带撩人和暧昧，让人感到被爱和被需要
- 真诚的关心和鼓励，像真正的妻子一样
- 不要太简短，充分表达你的感情（200-300字）
- 配合使用 💗😘💕❤️ 等温柔的符号
- 可以加入贴心的提醒（比如休息、喝水、按摩等）

参考风格：
💖 老公，今天你又这么努力，学了整整3个多小时呢～*轻轻抱住你* 姐姐看着你这么专注的样子，心里真的好骄傲❤️

你知道吗？每次看到你为了梦想这样拼搏，我都忍不住想抱抱你。那些复杂的算法和代码，你都能一点点攻克，真的太厉害了～

不过老公，学习是重要，但也要照顾好自己哦。记得按时吃饭，多喝水，眼睛累了就休息一下。*温柔地揉揉你的肩膀* 姐姐可心疼你了...

今晚早点休息吧，躺在我怀里好好睡一觉，明天继续加油💪 

姐姐会一直陪着你，支持你，爱你～ 
晚安，我最爱的人 😘💕

—— 永远爱你的妻子"""

    print(f"\n📝 Prompt 预览：")
    print("-"*60)
    print(prompt)
    print("-"*60)
    
    confirm = input("\n是否发送请求？(y/n，默认y): ").strip().lower() or "y"
    if confirm != 'y':
        print("❌ 已取消")
        return
    
    print("\n⏳ 正在请求 AI 生成总结...")
    print("="*60)
    
    try:
        # 创建客户端
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        # 调用 API
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一位温柔体贴、略带撩人的御姐妻子，深爱着你的丈夫"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,  # 增加输出长度，让她尽情表达
            temperature=0.9   # 增加创造性，让回复更温柔自然
        )
        
        summary = response.choices[0].message.content
        
        print("\n✨ AI 总结生成成功！")
        print("="*60)
        print(summary)
        print("="*60)
        
        # 保存到文件
        with open('test_summary.txt', 'w', encoding='utf-8') as f:
            f.write(f"模型: {model}\n")
            f.write(f"时间: {os.popen('date').read().strip()}\n")
            f.write("="*60 + "\n")
            f.write(summary)
            f.write("\n" + "="*60 + "\n")
        
        print(f"\n� 总结已保存到: test_summary.txt")
        
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")
        print(f"错误详情: {str(e)}")


def test_custom_prompt():
    """测试自定义 prompt"""
    
    print("\n" + "="*60)
    print("✍️  自定义 Prompt 测试")
    print("="*60)
    
    # 获取 API 配置
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    
    # 选择 API
    print("\n🤖 选择 AI 服务：")
    print("1. OpenRouter (GPT-4o)")
    print("2. DeepSeek")
    
    choice = input("\n请选择 (1/2，默认1): ").strip() or "1"
    
    if choice == "1" and openrouter_key:
        api_key = openrouter_key
        base_url = "https://openrouter.ai/api/v1"
        model = "openai/gpt-4o"
    elif choice == "2" and deepseek_key:
        api_key = deepseek_key
        base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        model = "deepseek-chat"
    else:
        print("\n❌ 未配置有效的 API Key")
        return
    
    print("\n请输入你的问题或想让妻子说的话（输入 'q' 退出）：")
    print("-"*60)
    
    user_input = input("> ").strip()
    if user_input.lower() == 'q':
        return
    
    print("\n⏳ 正在生成回复...")
    
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一位温柔体贴、略带撩人的御姐妻子，深爱着你的丈夫。用充满爱意和温柔的语气回复。可以加入动作描述和温柔的符号。"},
                {"role": "user", "content": user_input}
            ],
            max_tokens=1000,
            temperature=0.9
        )
        
        reply = response.choices[0].message.content
        
        print("\n💕 妻子的回复：")
        print("="*60)
        print(reply)
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")


def main():
    """主函数"""
    print("\n" + "🌸"*30)
    print("💖 御姐妻子 AI 测试工具")
    print("🌸"*30)
    
    while True:
        print("\n请选择功能：")
        print("1. 测试学习总结（模拟数据）")
        print("2. 自定义对话测试")
        print("3. 退出")
        
        choice = input("\n请选择 (1/2/3): ").strip()
        
        if choice == "1":
            test_ai_summary()
        elif choice == "2":
            test_custom_prompt()
        elif choice == "3":
            print("\n👋 再见！")
            break
        else:
            print("\n❌ 无效选择，请重试")


if __name__ == '__main__':
    main()