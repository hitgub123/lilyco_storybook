"""
使用 LangGraph 构建的 AI Agent，用于编排故事创作流程。
这个版本依赖LLM进行决策，并通过一个强大的System Prompt来引导LLM，以弥补小模型推理能力的不足。
"""

import os

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import json
from typing import Sequence, Annotated, TypedDict
import operator

# --- 模块和工具导入 ---
from langchain_core.tools import tool
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    ToolMessage,
    AIMessage,
    SystemMessage,
)
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# 确保我们能从batch目录中导入其他模块
import cloudinary_util
import generate_storybooks
import generate_stories
from logger_config import get_logger
from batch.local_llm_uti_customl import Local_llm
from task_manager import Task_manager
from dotenv import load_dotenv
import subprocess

load_dotenv()
logger = get_logger(__name__)
SAMPLE_PIC_4_STORYBOOK = os.getenv("SAMPLE_PIC_4_STORYBOOK")
sample_pic = os.path.join(SAMPLE_PIC_4_STORYBOOK, "gqj1.jpg")

# --- 初始化工具和模型 ---
llm = Local_llm(llm_name="google/gemma-3-1b-it")
# llm = Local_llm(llm_name="google/gemma-3-270m-it")

tm = Task_manager()

OK_msg = "执行成功，请继续后续处理。"
NG_msg = "执行失败，终止后续处理。"


def format_input(messages: list):
    formatted_messages = []
    for msg in messages:
        role = ""
        if isinstance(msg, SystemMessage):
            role = "system"
        elif isinstance(msg, AIMessage):
            role = "assistant"
        elif isinstance(msg, HumanMessage):
            role = "user"
        else:
            # 如果有其他未知的消息类型，可以先跳过或报错
            continue
        formatted_messages.append({"role": role, "content": msg.content})
    return formatted_messages


def format_output(response: list):
    generated_text_list = response[0]["generated_text"]
    assistant_reply_dict = generated_text_list[-1]
    assistant_content = assistant_reply_dict["content"]
    assistant_content = assistant_content.replace("\n", "")
    tool_calls = False if assistant_content == "FINISH" else True
    ai_message = AIMessage(content=assistant_content, tool_calls=tool_calls)
    return ai_message


# --- 1. 工具定义 ---


@tool
def generate_stories_tool(story_topic: str) -> str:
    """根据主题生成1个短故事并保存。这是整个流程的第一步。"""
    logger.info(f"[Tool] 正在为主题 '{story_topic}' 生成故事...")
    generated_stories = generate_stories.generate_stories_by_generation_func(
        topic=story_topic, number_of_stories=1, generation_func=llm.invoke
    )
    if generated_stories:
        tm.insert_task(generated_stories, pic=sample_pic)
        logger.info(f"成功生成故事并存入任务管理器。")
        return OK_msg
    else:
        logger.error("未能生成故事。")
        return NG_msg


@tool
def generate_images_tool() -> str:
    """为任务管理器中的故事生成图片。这是流程的第二步。"""
    logger.info("[Tool] 正在生成图片...")
    tasks = tm.read_df_from_csv()
    result = False
    target_tasks = tasks.query("is_target == 1 and generate_storybook != 1").iloc[0]
    for _, task in target_tasks.iterrows():
        prompt, id, pic = task["text"], task["id"], task["pic"]
        res = generate_storybooks.run(prompt=prompt, id=id, pic=pic)
        result = result or res
        if res:
            tasks.loc[tasks["id"] == id, "generate_storybook"] = 1
            tm.update_task(tasks)
            logger.info(f"成功为故事ID {target_tasks['id']} 生成图片。")
    return OK_msg if result else NG_msg


@tool
def upload_images_to_cloudinary_tool() -> str:
    """上传已生成的图片到Cloudinary。这是流程的第三步。"""
    logger.info("[Tool] 正在上传图片到 Cloudinary...")
    cloudinary_util.main()
    uploaded_list = cloudinary_util.update_task_record(tm)
    if uploaded_list:
        logger.info(f"成功上传 {len(uploaded_list)} 张图片。")
        return OK_msg
    logger.error("上传图片失败或没有需要上传的图片。")
    return NG_msg


@tool
def update_d1_database_tool() -> str:
    """更新数据库。这是流程的最后一步。"""
    logger.info("[Tool] 正在更新数据库...")
    result = subprocess.run(
        ["node", "post_stories.js"], capture_output=True, text=True, encoding="utf-8"
    )
    # 正确的成功逻辑判断
    if result.returncode == 0:
        logger.info(f"数据库更新成功。输出: {result.stdout}")
        return OK_msg
    else:
        logger.error(f"数据库更新失败。错误: {result.stderr}")
        return f"{NG_msg} 错误详情: {result.stderr}"


# --- 2. Agent 状态定义 ---


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


# --- 3. Agent 核心逻辑 ---

tools = [
    generate_stories_tool,
    generate_images_tool,
    upload_images_to_cloudinary_tool,
    update_d1_database_tool,
]
tool_node = ToolNode(tools)

# 这是给LLM的“超级指令”，是优化Agent决策能力的关键
# SYSTEM_PROMPT_CONTENT = """你是一个故事绘本创作流程的控制助手。你的任务是按顺序调用工具来完成整个工作流。

# 工作流程严格按照以下四步进行：
# 第一步：**generate_stories_tool**，根据用户提供的主题生成故事。
# 第二步：**generate_images_tool**，为上一步生成的故事制作图片。
# 第三步：**upload_images_to_cloudinary_tool**，将制作好的图片上传。
# 第四步：**update_d1_database_tool**，上传成功后，更新数据库。

# 请严格遵守以下规则：
# - **一步一动**: 每次只调用一个工具。
# - **顺序执行**: 必须严格按照 1 -> 2 -> 3 -> 4 的顺序调用工具。
# - **解读反馈**: 每个工具执行后会返回`OK_msg`或`NG_msg`。收到`OK_msg`表示上一步成功，你应该继续调用流程中的下一个工具。收到`NG_msg`表示上一步失败，你应该停止所有操作并报告失败。
# - **用户输入**: 你收到的第一条用户消息是故事的主题，请用它来调用第一个工具 `generate_stories_tool`。
# - **结束流程**: 当第四步 `update_d1_database_tool` 执行成功后，整个流程结束，你应该向用户报告整个任务已成功完成。
# """
SYSTEM_PROMPT_CONTENT = """你是一个严格的流程控制器。你的唯一任务是根据用户的最新请求，从下面的工具列表中选择一个必须执行的工具。    
    可用工具列表:
    - `generate_stories_tool`
    - `generate_images_tool`
    - `upload_images_to_cloudinary_tool`
    - `update_d1_database_tool`
    - `FINISH` (当所有步骤都完成后使用)
    你的回复必须只能是上述列表中的一个工具名称，不能包含任何其他文字、解释、标点符号或换行符。
    例如，如果应该生成故事，你的回复必须是:
    generate_stories_tool
    """
SYSTEM_PROMPT = SystemMessage(content=SYSTEM_PROMPT_CONTENT)


def should_continue(state: AgentState) -> str:
    """决定是继续调用工具还是结束流程。"""
    last_message = state["messages"][-1]
    # 如果上一条是AI消息且包含工具调用，则执行工具
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "continue"
    # 如果工具执行失败，或者AI决定结束，则终止
    if isinstance(last_message, ToolMessage) and NG_msg in last_message.content:
        return "end"
    if isinstance(last_message, AIMessage) and not last_message.tool_calls:
        return "end"
    # 其他情况（比如工具执行成功），都应返回给Agent继续决策
    return "agent"


def call_model(state: AgentState) -> dict:
    """调用LLM（大脑）来决定下一步行动。"""
    logger.info("--- Agent 正在思考... ---")
    # 在每次调用时，都把“超级指令”放在最前面
    messages_with_system_prompt = [SYSTEM_PROMPT] + state["messages"]
    formatted_messages = format_input(messages_with_system_prompt)
    response = llm.invoke(formatted_messages)
    formatted_output = format_output(response)
    return {"messages": [formatted_output]}


# 定义工作流
workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)

workflow.set_entry_point("agent")

# 修复后的条件路由
workflow.add_conditional_edges(
    "agent",
    # 首先检查AI的输出是否要调用工具
    lambda state: (
        "continue"
        if isinstance(state["messages"][-1], AIMessage)
        and state["messages"][-1].tool_calls
        else "end"
    ),
    {"continue": "action", "end": END},
)

# 工具执行后的路由
workflow.add_conditional_edges(
    "action",
    # 检查工具的输出是成功还是失败
    lambda state: (
        "agent"
        if isinstance(state["messages"][-1], ToolMessage)
        and OK_msg in state["messages"][-1].content
        else "end"
    ),
    {"agent": "agent", "end": END},  # 成功则返回给Agent决策下一步  # 失败则直接结束
)

# 编译图
app = workflow.compile()

# --- 4. 主程序入口 ---


def agent_main(user_query, recursion_limit=10):
    inputs = {"messages": [HumanMessage(content=user_query)]}

    print("--- Agent 开始运行 ---")
    final_state = app.invoke(inputs, {"recursion_limit": recursion_limit})
    final_answer = final_state["messages"][-1].content
    print("--- Agent 运行结束 ---")
    print(f"最终答案: {final_answer}")


if __name__ == "__main__":
    agent_main("用户提供的主题:城里长大的女孩lily第一次回到大山里,开始了乡村生活")
