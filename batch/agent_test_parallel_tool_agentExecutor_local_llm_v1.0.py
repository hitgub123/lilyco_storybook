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
    """买水。如果有人需要喝的，或者需要用水，就调用这个方法"""
    pass


@tool
@inject_tool_name
def buy_instant_noodle() -> str:
    """买泡面。如果有人需要吃的，就调用这个方法"""
    pass


@tool
@inject_tool_name
def goto_hospital() -> str:
    """去医院看望病人，返回值是部门的列表，表示哪些部门有病人，
    比如返回['销售','开发']表示销售部和开发部有病人"""
    # return ['C']
    # return ['C','A']
    return []


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
                """你是一个能干的、拥有工具使用能力的AI秘书。
                你的任务是分析用户的请求和对话历史，然后决定最佳行动方案。
                请遵循以下思考过程：
                1.  首先，判断用户的最新请求是否需要通过调用工具来解决。
                2.  如果需要调用工具，请直接返回一个或多个工具调用请求，并确保为每个工具提供了所有必需的、正确的参数。
                3.  如果不需要调用工具，或者工具执行完毕后，请直接用自然语言生成一个友好且有帮助的回答。""",
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
    model_list=["phi4-mini:3.8b","gemma3:12b","llama3.1:8b","gemma3-1b-lora:model-f16","gemma3-1b-lora:model-Q4_K_M"]
    options_str = "\n".join([f'{idx}: {model_name}' for idx, model_name in enumerate(model_list)])

    # 提示用户输入，并显示格式化后的选项
    user_input = input(f"请输入想使用的模型序号：\n{options_str}\n你的选择是：")
    selected_index = int(user_input)
    model=model_list[selected_index]
    llm = ChatOllama(model=model, temperature=0)
    agent = create_agent(llm)
    chat_history = []
    # 我们代表公司去医院看望病人，去之前要买吃的和喝的。看望病人后，我们能知道哪些部门由病人，接下来我们要通知这些部门，如果没有病人就不用通知。最后我们才能打卡下班。
    while 1:
        prompt = input("请输入今天的任务：\n")
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
            # print(response)
