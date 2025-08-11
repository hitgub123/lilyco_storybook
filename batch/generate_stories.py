"""
这个模块包含使用LLM（大型语言模型）生成内容的工具函数。
"""

import json
from typing import List, Callable
from logger_config import get_logger

logger = get_logger(__name__)


class MockLLM:
    """
    一个模拟的LLM类，用于测试和演示。
    它返回一个预设的JSON字符串，模拟真实LLM的行为。
    它包含多个不同名称的方法（complete, invoke）以证明灵活性。
    """

    def _generate_response(self, prompt: str, method_name: str) -> str:
        """内部方法，用于生成标准响应。"""
        logger.debug(f"--- Mock LLM 通过 {method_name} 方法接收到的提示 ---")
        logger.debug(prompt)
        # 模拟LLM根据提示返回的JSON数据
        return """
        {
            "stories": [
                "勇敢的小猫米奇，第一次爬上了高高的书架探险。",
                "小猫莉莉在花园里追逐蝴蝶，不小心滚进了花丛里。",
                "夜里，小猫汤姆悄悄溜进厨房，偷吃了盘里的鱼干。"
            ]
        }
        """

    def complete(self, prompt: str) -> str:
        """模拟名为 'complete' 的LLM生成方法。"""
        return self._generate_response(prompt, "complete")

    def invoke(self, prompt: str) -> str:
        """模拟名为 'invoke' 的LLM生成方法。"""
        return self._generate_response(prompt, "invoke")


def generate_stories_by_generation_func(
    topic: str,
    generation_func: Callable[[str], str],
    count: int = 3,
    word_count: int = 30,
) -> List[str]:
    """
    使用generation_func根据指定主题生成多个小故事。

    Args:
        topic (str): 故事的主题。
        generation_func (Callable[[str], str]): 用于生成文本的函数。
            这个函数应该接受一个字符串提示(prompt)作为输入，并返回一个字符串结果。
            例如: my_llm_client.complete 或 my_llm_client.invoke
        count (int): 需要生成的故事数量。
        word_count (int): 每个故事的大致字数。

    Returns:
        List[str]: 一个包含生成的故事字符串的列表。如果失败则返回空列表。
    """
    # 构建一个清晰、具体的提示，要求LLM返回JSON格式
    prompt = f"""请根据以下主题生成一个JSON对象。
主题：'{topic}'
对象应该包含一个名为 "stories" 的键，其值是一个包含 {count} 个字符串的数组。
每个字符串都应该是一个关于主题的、长度在{word_count}个字左右的独立小故事。
请确保您的回答是严格的JSON格式，不要包含任何额外的解释或注释。"""

    response_text = ""
    try:
        # 调用传入的函数来获取结果
        response_text = generation_func(prompt)

        # 解析LLM返回的JSON字符串
        data = json.loads(response_text)

        # 从解析后的数据中提取故事列表
        stories = data.get("stories", [])

        # 校验返回的是否是列表以及元素是否是字符串
        if isinstance(stories, list) and all(isinstance(s, str) for s in stories):
            return stories
        else:
            logger.error("错误：LLM返回的JSON中'stories'键的值不是一个字符串列表。")
            return []

    except json.JSONDecodeError:
        logger.error(
            f"错误：无法解析LLM返回的文本为JSON。收到的文本: \n{response_text}"
        )
        return []
    except Exception as e:
        logger.error(f"在与LLM交互或处理数据时发生未知错误: {e}")
        return []


# --- 主程序入口，用于演示和测试 ---
if __name__ == "__main__":
    # 1. 创建一个模拟的LLM实例
    mock_llm_client = MockLLM()

    # 2. 定义故事主题和数量
    story_topic = "一只勇敢的小猫"
    number_of_stories = 3

    # 3. 调用函数生成故事，演示传入 complete 方法
    logger.debug(f"--- 演示1: 使用 mock_llm_client.complete 方法 ---")
    logger.debug(f"正在为主题 '{story_topic}' 生成 {number_of_stories} 个小故事...")
    generated_stories_1 = generate_stories_by_generation_func(
        topic=story_topic,
        count=number_of_stories,
        generation_func=mock_llm_client.complete,  # 直接把方法作为参数传入
    )

    # 4. 打印结果
    if generated_stories_1:
        logger.debug("\n--- 成功生成的故事列表 (来自complete) ---")
        for i, story in enumerate(generated_stories_1, 1):
            logger.debug(f"{i}. {story}")
    else:
        logger.error("\n--- 未能生成故事 (来自complete) ---")

    logger.debug("\n" + "=" * 50 + "\n")

    # 5. 再次调用函数，演示传入 invoke 方法
    logger.debug(f"--- 演示2: 使用 mock_llm_client.invoke 方法 ---")
    logger.debug(f"正在为主题 '{story_topic}' 生成 {number_of_stories} 个小故事...")
    generated_stories_2 = generate_stories_by_generation_func(
        topic=story_topic,
        count=number_of_stories,
        generation_func=mock_llm_client.invoke,  # 传入另一个方法
    )

    # 6. 打印结果
    if generated_stories_2:
        logger.debug("\n--- 成功生成的故事列表 (来自invoke) ---")
        for i, story in enumerate(generated_stories_2, 1):
            logger.debug(f"{i}. {story}")
    else:
        logger.error("\n--- 未能生成故事 (来自invoke) ---")
