"""
使用 LangGraph 构建的 AI Agent，用于编排故事创作流程。
"""

import os
from typing import List, Sequence, Annotated, TypedDict
import operator
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

OK_msg = "执行成功，请继续后续处理"
NG_msg = "执行失败，终止后续处理"


@tool
def generate_stories_tool(
    story_topic="城里长大的女孩lily第一次回到乡下，她来到一片花海", pic=None
) -> str:
    """根据主题生成多个短故事并保存到故事记录文件里。"""
    number_of_stories = 1

    logger.info(f"正在为主题 '{story_topic}' 生成 {number_of_stories} 个小故事...")
    generated_stories_1 = generate_stories.generate_stories_by_generation_func(
        topic=story_topic,
        number_of_stories=number_of_stories,
        generation_func=llm.invoke,  # 直接把方法作为参数传入
    )

    if generated_stories_1:
        logger.info("\n--- 成功生成的故事列表---")
        for i, story in enumerate(generated_stories_1):
            logger.info(f"{i}. {story}")
        tm.insert_task(generated_stories_1, pic=pic)
        return OK_msg
    else:
        logger.error("\n--- 未能生成故事 ---")
        return NG_msg


@tool
def generate_images_tool() -> str:
    """从故事记录文件读取未处理的数据，生成故事绘本保存到图片库。"""
    tasks = tm.read_df_from_csv()
    target_task = tasks.query("is_target == 1 and generate_storybook != 1")
    logger.info("target_task", target_task)
    for _, task in target_task.iterrows():
        # prompt = "兔子托比在林间小溪上漂流,它沿途看到了很多鱼，它和其中一只叫波利的安康鱼做了朋友"
        prompt = task["text"]
        id = task["id"]
        pic = task["pic"]
        res = generate_storybooks.run(prompt=prompt, id=id, pic=pic)
        if res:
            tasks.loc[tasks["id"] == id, "generate_storybook"] = 1
            tm.update_task(tasks)
            return OK_msg
        else:
            logger.error("生成绘本失败")
            return NG_msg


@tool
def upload_images_to_cloudinary_tool() -> str:
    """从图片库取得未处理的图片，上传到Cloudinary。"""
    cloudinary_util.main()
    uploaded_list = cloudinary_util.update_task_record(tm)
    return OK_msg if uploaded_list else NG_msg


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
    return OK_msg if result else NG_msg


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # 我们可以在状态中添加更多字段来传递信息，但这里为了简洁，信息通过message传递


tools = [
    generate_stories_tool,
    generate_images_tool,
    upload_images_to_cloudinary_tool,
    update_d1,
]
tool_node = ToolNode(tools)

agelnt_llm = llm
agelnt_llm_with_tools = llm.bind_tools(tools)


def should_continue(state: AgentState) -> str:
    """决定是继续调用工具还是结束流程。"""
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


def agent_main(user_query,recursion_limit=10):
    initial_prompt = "请帮我创作一个关于一只勇敢的小兔子的故事，并生成图片上传"
    inputs = {"messages": [HumanMessage(content=initial_prompt)]}

    print("--- Agent 开始运行 ---")
    # for output in app.stream(inputs, {"recursion_limit": recursion_limit}):
    #     for key, value in output.items():
    #         print(f"--- 输出自节点: {key} ---")
    #         print(value)
    #         print("--------------------")

    final_state = app.invoke(inputs, {"recursion_limit": recursion_limit})
    final_answer = final_state["messages"][-1].content
    print("--- Agent 运行结束 ---")
    print(f"最终答案: {final_answer}")

if __name__ == "__main__":
    agent_main('')