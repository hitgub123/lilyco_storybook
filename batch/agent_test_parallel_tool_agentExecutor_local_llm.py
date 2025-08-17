import functools
import os, torch

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_ollama.chat_models import ChatOllama
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    ToolMessage,
    AIMessage,
    SystemMessage,
)


def inject_tool_name(func):
    """
    一个装饰器，它将原始函数的名称作为关键字参数 '__tool_name' 注入。
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 将函数名注入到调用参数中
        # kwargs['__tool_name'] = func.__name__
        print(f'[执行工具 {func.__name__}]')
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
    return ["C", "A"]
    # return []


def create_agent(llm):
    tools = [
        goto_hospital,
        buy_instant_noodle,
        buy_water,
        notice_groupA,
        notice_groupB,
        notice_groupC,
        end_a_day,
    ]

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "你是一个能干的秘书，会根据用户的请求和对话历史来决定如何行动。",
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    # 创建代理
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    return agent_executor


if __name__ == "__main__":
    # model="gemma3:1b-it-qat"  #do not support function calling
    # model = "allenporter/xlam:1b" # can only answer computer questions
    model = "phi4-mini:3.8b"
    llm = ChatOllama(model=model, temperature=0)
    agent = create_agent(llm)
    chat_history = []
    while 1:
        prompt = input("请输入你今天的任务\n")
        if prompt == "q":
            break
        else:
            response = agent.invoke({"input": prompt, "chat_history": chat_history})
            chat_history.extend(
                [
                    HumanMessage(content=prompt),
                    AIMessage(content=response["output"]),
                ]
            )
            print(response)
