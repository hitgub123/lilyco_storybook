import functools
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


def inject_tool_name(func):
    """
    一个装饰器，它将原始函数的名称作为关键字参数 '__tool_name' 注入。
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 将函数名注入到调用参数中
        # kwargs['__tool_name'] = func.__name__
        print(func.__name__)
        return func(*args, **kwargs)

    return wrapper


# --- 1. 工具定义 ---
@tool
@inject_tool_name
def notice_groupC() -> str:
    """通知C部门"""
    pass


@tool
@inject_tool_name
def notice_groupB() -> str:
    """通知B部门"""
    pass


@tool
@inject_tool_name
def notice_groupA() -> str:
    """通知A部门"""
    pass


@tool
@inject_tool_name
def end_a_day() -> str:
    """完成所有任务后打卡下班"""
    pass


@tool
@inject_tool_name
def buy_water() -> str:
    """买水"""
    pass


@tool
@inject_tool_name
def buy_instant_noodle() -> str:
    """买泡面"""
    pass


@tool
@inject_tool_name
def goto_hospital() -> str:
    """去医院看望病人，返回值是部门的列表，表示哪些部门有病人，
    比如返回['销售','开发']表示销售部和开发部有病人"""
    # return ['C']
    # return ['C','A']
    return []


class AgentState(TypedDict):
    messages: Annotated[Sequence[AIMessage | HumanMessage | ToolMessage], operator.add]


tools = [
    goto_hospital,
    buy_instant_noodle,
    buy_water,
    notice_groupA,
    notice_groupB,
    notice_groupC,
    end_a_day,
]

tool_node = ToolNode(tools)


def agent_node(state: AgentState, llm) -> dict:
    messages = state["messages"]
    response = llm.invoke(messages)
    print([t["name"] for t in response.tool_calls])
    return {"messages": [response]}


default_tool_node = ToolNode(tools)


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
    workflow.add_node("tool", tool_node)

    workflow.set_entry_point("agent")

    workflow.add_conditional_edges(
        "agent", should_call_tool, {"tool": "tool", END: END}
    )

    workflow.add_edge("tool", "agent")

    return workflow.compile()


def agent_main(app, user_query, recursion_limit=10):
    # app = create_agent_graph()

    initial_state = {"messages": [HumanMessage(content=user_query)]}

    print("--- Agent 开始运行 ---")
    final_state = app.invoke(initial_state, {"recursion_limit": recursion_limit})
    final_answer = final_state["messages"][-1].content
    print("--- Agent 运行结束 ---")
    print(f"最终答案: {final_answer}")


if __name__ == "__main__":
    app = create_agent_graph()
    while 1:
        prompt = input("请输入你任务：\n")
        # prompt = f"""
        # 我们代表公司去医院看望病人，去之前要买吃的和喝的。
        # 看望病人后，我们能知道哪些部门由病人，接下来我们要通知这些部门，如果没有病人就不用通知。
        # 最后我们才能打卡下班。
        # """
        if prompt == "q":
            break
        else:
            agent_main(app, prompt)
