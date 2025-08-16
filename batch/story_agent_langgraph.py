"""
使用 LangGraph 构建的 AI Agent，用于编排故事创作流程。
"""

import os
import sys
import json
from typing import List, Sequence, Annotated, TypedDict
import operator

# --- 模块和工具导入 ---
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_community.llms.fake import FakeListLLM

# 确保我们能从batch目录中导入其他模块
# (此脚本应位于 batch 目录中)
import cloudinary_util
import generate_storybooks
import generate_stories
from logger_config import get_logger
from local_llm_util import Local_llm
from task_manager import Task_manager
from dotenv import load_dotenv
import subprocess

load_dotenv()
logger = get_logger(__name__)

# 本地文件路径 (相对于项目根目录)
SAMPLE_PIC_4_STORYBOOK = os.getenv("SAMPLE_PIC_4_STORYBOOK")

llm = Local_llm(llm_name="google/gemma-3-270m-it")
tm = Task_manager()


@tool
def generate_stories_tool(topic: str) -> str:
    """根据主题生成多个短故事。"""
    logger.info(f"[Tool] 正在为主题 '{topic}' 生成故事...")

    # 注意：为了和LangGraph的ToolMessage格式保持一致，我们返回JSON字符串
    stories_list = generate_stories.generate_stories_by_generation_func(
        topic=topic, generation_func=llm.invoke
    )
    return json.dumps(stories_list)


@tool
def generate_images_tool(story: str) -> str:
    """为一个故事文本生成图片并保存到本地。"""
    logger.info(f"[Tool] 正在为故事 '{story[:100]}...' 生成图片...")
    # 此处我们模拟 generate_storybooks.run 的行为
    # 实际项目中，您需要处理好 playwright 的浏览器实例传递
    generate_storybooks.run(prompt=story)
    # logger.debug("图片生成工具（模拟）执行完毕。")
    return f"成功为故事 '{story[:20]}...' 生成了图片。"


@tool
def upload_images_to_cloudinary_tool() -> str:
    """将本地生成的图片上传到Cloudinary。"""
    logger.info("[Tool] 正在将图片上传到 Cloudinary...")
    cloudinary_util.main()
    # logger.debug("Cloudinary上传工具（模拟）执行完毕。")
    return "所有图片已成功上传到Cloudinary。"

@tool
def update_d1() -> str:
    """图片上传到Cloudinary成功后，更新数据库"""
    result = subprocess.run(
        ["node", "post_stories.js"], capture_output=True, text=True, encoding="utf-8"
    )
    logger.info(f"脚本执行完毕，退出码: {result.returncode}")
    logger.info("--- 标准输出 (stdout) ---")
    logger.info(result.stdout)
    logger.info("--- 标准错误 (stderr) ---")
    logger.info(result.stderr)


# --- 2. Agent 状态定义 ---


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # 我们可以在状态中添加更多字段来传递信息，但这里为了简洁，信息通过message传递


# --- 3. LangGraph 的节点和图定义 ---

tools = [generate_stories_tool, generate_images_tool, upload_images_to_cloudinary_tool,update_d1]
tool_node = ToolNode(tools)

# 模拟 Agent 的大脑，预设其思考和决策过程
# LangGraph 需要 AIMessage 和 ToolCall 来驱动工具
responses = [
    AIMessage(
        id="m1",
        content="",
        tool_calls=[
            {"name": "generate_stories_tool", "args": {"topic": "一只勇敢的小兔子"}}
        ],
    ),
    AIMessage(
        id="m2",
        content="",
        tool_calls=[
            {
                "name": "generate_images_tool",
                "args": {"story": "小兔子托比发现了一张藏宝图。"},
            },
            {
                "name": "generate_images_tool",
                "args": {"story": "在魔法森林里，托比遇到了聪明的狐狸芬尼克。"},
            },
            {
                "name": "generate_images_tool",
                "args": {"story": "它们一起找到了传说中的宝石胡萝卜。"},
            },
        ],
    ),
    AIMessage(
        id="m3",
        content="",
        tool_calls=[{"name": "upload_images_to_cloudinary_tool", "args": {}}],
    ),
    AIMessage(content="所有任务已完成！故事生成、图片制作和上传均已成功。"),
]

# 使用一个能返回AIMessage列表的FakeListLLM
llm = FakeListLLM(responses=responses)


def should_continue(state: AgentState) -> str:
    """决定是继续调用工具还是结束流程。"""
    if not isinstance(state["messages"][-1], AIMessage):
        return "continue"  # 如果上一条不是AI消息（即工具消息），则继续
    last_message = state["messages"][-1]
    return "continue" if last_message.tool_calls else "end"


def call_model(state: AgentState) -> dict:
    """调用LLM（大脑）来决定下一步行动。"""
    logger.info("--- Agent 正在思考... ---")
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


# 定义工作流
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent", should_continue, {"continue": "action", "end": END}
)
workflow.add_edge("action", "agent")

# 编译图
app = workflow.compile()

# --- 4. 主程序入口 ---

if __name__ == "__main__":
    initial_prompt = "请帮我创作一个关于一只勇敢的小兔子的故事，并生成图片上传"
    inputs = {"messages": [HumanMessage(content=initial_prompt)]}

    print("--- Agent 开始运行 ---")
    for output in app.stream(inputs, {"recursion_limit": 10}):
        for key, value in output.items():
            print(f"--- 输出自节点: {key} ---")
            print(value)
            print("--------------------")

    final_state = app.invoke(inputs, {"recursion_limit": 10})
    final_answer = final_state["messages"][-1].content
    print("--- Agent 运行结束 ---")
    print(f"最终答案: {final_answer}")
