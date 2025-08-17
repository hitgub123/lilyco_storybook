import os

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from langchain_google_genai import ChatGoogleGenerativeAI

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
from task_manager import Task_manager
from dotenv import load_dotenv
import subprocess

load_dotenv()
logger = get_logger(__name__)
SAMPLE_PIC_4_STORYBOOK = os.getenv("SAMPLE_PIC_4_STORYBOOK")
sample_pic = os.path.join(SAMPLE_PIC_4_STORYBOOK, "gqj1.jpg")

tm = Task_manager()
OK_msg='执行成功'
NG_msg='执行失败'

# --- 1. 工具定义 ---
@tool
def generate_stories_tool(story_topic: str) -> str:
    """根据主题生成1个短故事并保存"""
    # """根据主题生成1个短故事并保存。这是整个流程的第一步。"""
    logger.info(f"[Tool] 正在为主题 '{story_topic}' 生成故事...")

    from local_llm_util import Local_llm
    llm = Local_llm(llm_name="google/gemma-3-270m-it")
    generated_stories = generate_stories.generate_stories_by_generation_func(
        topic=story_topic,
        number_of_stories=1,
        generation_func=llm.invoke_query_format1
    )
    if generated_stories:
        tm.insert_task(generated_stories, pic=sample_pic)
        logger.info(f"成功生成故事并存入任务管理器。")
        # return OK_msg.format("请为任务管理器中的故事生成图片")
        return OK_msg
    else:
        logger.error("未能生成故事。")
        return NG_msg
        # return OK_msg.format("请为任务管理器中的故事生成图片")


@tool
def generate_images_tool() -> str:
    """为任务管理器中的故事生成图片"""
    # """为任务管理器中的故事生成图片。这是流程的第二步。"""
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
    return OK_msg if result else NG_msg
    # return OK_msg.format("请上传已生成的图片") if result else NG_msg


@tool
def upload_images_to_cloudinary_tool() -> str:
    """上传已生成的图片到Cloudinary"""
    # """上传已生成的图片到Cloudinary。这是流程的第三步。"""
    logger.info("[Tool] 正在上传图片到 Cloudinary...")
    cloudinary_util.main()
    uploaded_list = cloudinary_util.update_task_record(tm)
    if uploaded_list:
        logger.info(f"成功上传 {len(uploaded_list)} 张图片。")
        return OK_msg
        # return OK_msg.format("请更新数据库")
    logger.error("上传图片失败或没有需要上传的图片。")
    return NG_msg


@tool
def update_d1_database_tool() -> str:
    # """更新数据库。这是流程的最后一步。"""
    """更新数据库"""
    logger.info("[Tool] 正在更新数据库...")
    result = subprocess.run(
        ["node", "batch/post_stories.js"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    # 正确的成功逻辑判断
    if result.returncode == 0 and not result.stderr:
        logger.info(f"数据库更新成功。输出: {result.stdout}")
        return OK_msg
        # return OK_msg.format("步骤全部完成，请结束任务")
    else:
        logger.error(f"数据库更新失败。错误: {result.stderr[:20]}")
        return f"{NG_msg} 错误详情: {result.stderr}"


class AgentState(TypedDict):
    # messages: Annotated[Sequence[BaseMessage], operator.add]
    # toolMessage will be added althought next code is used
    messages: Annotated[Sequence[AIMessage | HumanMessage], operator.add]


tools = [
    generate_stories_tool,
    generate_images_tool,
    upload_images_to_cloudinary_tool,
    update_d1_database_tool,
]

tool_node = ToolNode(tools)

def agent_node(state: AgentState, llm) -> dict:
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


# 自定义的节点函数
def custom_tool_node(state):
    """
    自定义工具节点。
    如果调用的工具是 'hogehoge'，则直接返回 "ok"。
    否则，使用默认的 ToolNode 逻辑处理。
    """
    mock_tools= [tools[0].name,tools[1].name,tools[2].name]

    last_message = state["messages"][-1]
    cur_tools =last_message.tool_calls
    if cur_tools and cur_tools[0] and cur_tools[0]["name"] in mock_tools:
        # 获取 f1 工具调用的 ID
        tool_call_id = cur_tools[0]['id']

        # 手动创建一个 ToolMessage 作为 f1 的返回结果
        tool_message = ToolMessage(content=OK_msg, tool_call_id=tool_call_id)
        return {"messages": [tool_message]}
    else:
        default_tool_node = ToolNode(tools)
        return default_tool_node.invoke(state)


def should_call_tool(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tool"
    return END


# 创建 LangGraph 工作流
def create_agent_graph():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=os.environ.get("gemini_api_key2"),
    )
    llm_with_tools = llm.bind_tools(tools)

    workflow = StateGraph(AgentState)

    workflow.add_node("agent", lambda state: agent_node(state, llm_with_tools))
    # workflow.add_node("tool", tool_node)
    # use custom_tool_node if want to change the default tool_node
    workflow.add_node("tool", custom_tool_node)

    workflow.set_entry_point("agent")

    workflow.add_conditional_edges(
        "agent", should_call_tool, {"tool": "tool", END: END}
    )

    workflow.add_edge("tool", "agent")

    return workflow.compile()


def agent_main(user_query, recursion_limit=10):
    app = create_agent_graph()

    initial_state = {"messages": [HumanMessage(content=user_query)]}

    print("--- Agent 开始运行 ---")
    final_state = app.invoke(initial_state, {"recursion_limit": recursion_limit})
    final_answer = final_state["messages"][-1].content
    print("--- Agent 运行结束 ---")
    print(f"最终答案: {final_answer}")


if __name__ == "__main__":
    topic='城里长大的女孩lily第一次回到大山里,开始了乡村生活'
    prompt=f'为下面的主题生成故事再生成绘本再上传再更新数据库。主题:{topic}'
    agent_main(prompt)
