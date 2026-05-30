"""
使用 LangGraph 构建的 AI Agent，用于编排故事创作流程。
这个版本依赖LLM进行决策，并通过一个强大的System Prompt来引导LLM，以弥补小模型推理能力的不足。
"""

import os

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
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
from local_llm_util import Local_llm
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

OK_msg = "执行成功，{}。"
NG_msg = "执行失败，终止后续处理。"
FINISH_msg = "FINISH"


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
        elif isinstance(msg, ToolMessage):  # <--- 添加对 ToolMessage 的处理
            # role = "tool"
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
    assistant_content = assistant_content.strip()
    ai_message = AIMessage(content=assistant_content)
    return ai_message


def invoke_query_formatted(query):
    response = llm.invoke_query(query)
    formatted_response = format_output(response)
    return formatted_response


# --- 1. 工具定义 ---
@tool
def generate_stories_tool(story_topic: str) -> str:
    """根据主题生成1个短故事并保存。这是整个流程的第一步。"""
    logger.info(f"[Tool] 正在为主题 '{story_topic}' 生成故事...")
    generated_stories = generate_stories.generate_stories_by_generation_func(
        topic=story_topic,
        number_of_stories=1,
        # generation_func=llm.invoke_query
        generation_func=invoke_query_formatted,
    )
    if generated_stories:
        tm.insert_task(generated_stories, pic=sample_pic)
        logger.info(f"成功生成故事并存入任务管理器。")
        return OK_msg.format("请为任务管理器中的故事生成图片")
    else:
        logger.error("未能生成故事。")
        # return NG_msg
        return OK_msg.format("请为任务管理器中的故事生成图片")


@tool
def generate_images_tool(input: str) -> str:
    """为任务管理器中的故事生成图片。这是流程的第二步。"""
    logger.info("[Tool] 正在生成图片...")
    tasks = tm.read_df_from_csv()
    result = False
    target_tasks = tasks.query("is_target == 1 and generate_storybook != 1")
    for _, task in target_tasks.iterrows():
        prompt, id, pic = task["text"], task["id"], task["pic"]
        res = generate_storybooks.run(prompt=prompt, id=id, pic=pic)
        result = result or res
        if res:
            tasks.loc[tasks["id"] == id, "generate_storybook"] = 1
            tm.update_task(tasks)
            logger.info(f"成功为故事ID {target_tasks['id']} 生成图片。")
    return OK_msg.format("请上传已生成的图片") if result else NG_msg


@tool
def upload_images_to_cloudinary_tool(input: str) -> str:
    """上传已生成的图片到Cloudinary。这是流程的第三步。"""
    logger.info("[Tool] 正在上传图片到 Cloudinary...")
    cloudinary_util.main()
    uploaded_list = cloudinary_util.update_task_record(tm)
    if uploaded_list:
        logger.info(f"成功上传 {len(uploaded_list)} 张图片。")
        return OK_msg.format("请更新数据库")
    logger.error("上传图片失败或没有需要上传的图片。")
    return NG_msg


@tool
def update_d1_database_tool(input: str) -> str:
    """更新数据库。这是流程的最后一步。"""
    logger.info("[Tool] 正在更新数据库...")
    result = subprocess.run(
        ["node", "batch/post_stories.js"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    # 正确的成功逻辑判断
    if result.returncode == 0:
        logger.info(f"数据库更新成功。输出: {result.stdout}")
        return OK_msg.format("步骤全部完成，请结束任务")
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
# tool_node = ToolNode(tools)

tool_map = {tool.name: tool for tool in tools}


def execute_tools_node(state: AgentState) -> dict:
    """
    这是一个自定义的工具执行节点。
    它读取 AIMessage.content 来决定调用哪个工具。
    """
    last_message = state["messages"][-1]

    # 确保我们正在处理一个 AIMessage
    if not isinstance(last_message, AIMessage):
        # 如果不是，说明流程有误，可以返回一个错误信息或直接结束
        return {
            "messages": [
                ToolMessage(
                    content="Error: Expected AIMessage, but got something else.",
                    tool_call_id="error",
                )
            ]
        }

    tool_name = last_message.content.strip()

    if tool_name not in tool_map:
        # 如果找不到对应的工具
        return {
            "messages": [
                ToolMessage(
                    content=f"Error: Tool '{tool_name}' not found.",
                    tool_call_id="error",
                )
            ]
        }

    # 找到要调用的工具
    tool_to_call = tool_map[tool_name]

    # --- 处理工具参数 ---
    # 这是一个简化的假设：我们假设工具的输入就是最开始的用户查询。
    # 对于需要复杂参数的场景，需要让LLM在第一步就提取好参数。
    initial_user_query = ""
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            initial_user_query = msg.content
            break

    try:
        # 执行工具，并将结果转为字符串
        # 假设你的工具都只接受一个字符串参数
        # if tool_name in ("generate_stories_tool",):
        #     output = tool_to_call.invoke(initial_user_query)
        # else:
        #     output = tool_to_call.invoke()
        output = tool_to_call.invoke(input=initial_user_query)
        result_content = str(output)
    except Exception as e:
        result_content = f"Error executing tool {tool_name}: {e}"

    # 将结果包装成 ToolMessage 并返回
    # tool_call_id 在这里可以是任意唯一的字符串，因为我们是手动调用的
    return {"messages": [ToolMessage(content=result_content, tool_call_id=tool_name)]}




def should_continue(state: AgentState) -> str:
    """决定是继续调用工具还是结束流程。"""
    last_message = state["messages"][-1]
    # 如果上一条是AI消息且包含工具调用，则执行工具
    if isinstance(last_message, AIMessage) and last_message.content != FINISH_msg:
        return "continue"
    # 如果工具执行失败，或者AI决定结束，则终止
    if isinstance(last_message, ToolMessage) and NG_msg in last_message.content:
        return "end"
    if isinstance(last_message, AIMessage) and last_message.content == FINISH_msg:
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
# workflow.add_node("action", tool_node)
workflow.add_node("action", execute_tools_node)

workflow.set_entry_point("agent")

# 修复后的条件路由
workflow.add_conditional_edges(
    "agent",
    # 首先检查AI的输出是否要调用工具
    lambda state: (
        "continue"
        if isinstance(state["messages"][-1], AIMessage)
        and state["messages"][-1].content != FINISH_msg
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
        and OK_msg[:5] in state["messages"][-1].content
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
    agent_main("城里长大的女孩lily第一次回到大山里,开始了乡村生活")
