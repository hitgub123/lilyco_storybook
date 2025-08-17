from pydantic import PrivateAttr
import os, torch

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
from transformers import pipeline
from langchain_core.tools import tool
from langchain_core.language_models import BaseLLM, BaseChatModel
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, ToolCall
from typing import TypedDict, Annotated, Sequence, Dict, Any
import operator
import json

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

device = "cuda" if torch.cuda.is_available() else "cpu"

SYSTEM_CONTENT="""
你是一个智能助手，请选择合适的工具帮我完成任务：
你可以使用如下工具，
{}
请按照以下 JSON 格式返回工具调用：
{
  "tool_calls": [
    {"name": "tool_name", "args": {"arg_name": "value"}}
  ]
}
如果没有工具需要调用，返回空列表：{"tool_calls": []}。
现在请根据任务描述生成工具调用。"""
# google/gemma-3-270m-it
# google/gemma-3-1b-it
# 自定义 LLM 类
class CustomLLM(BaseLLM):
    # class CustomLLM(BaseChatModel):
    llm_name: str = "google/gemma-3-270m-it"
    tools: list = []
    _pipe: Any = PrivateAttr()

    def __init__(self, **data: Any):
        super().__init__(**data)
        # self.llm_name = llm_name
        self._pipe = pipeline("text-generation", model=self.llm_name, device=device)

    def invoke(self, query: str) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_CONTENT.format(self.tools)},
            {"role": "user", "content": query},
        ]
        response = self._pipe(messages)
        print("response", response)
        generated_text_list = response[0]["generated_text"]
        assistant_reply_dict = generated_text_list[-1]
        assistant_content = assistant_reply_dict["content"]
        return assistant_content

    def _generate(self, messages: Sequence[Dict]) -> Dict:
        # 将 LangChain 的消息转换为你的 LLM 输入格式
        query = messages[-1].content if messages else ""
        response_text = self.invoke(query)

        # 模拟工具调用解析：假设 LLM 返回 JSON 格式的工具调用
        # 示例：{"tool_calls": [{"name": "reverse_string", "args": {"input_text": "hello"}}]}
        try:
            response_json = json.loads(response_text)
            if "tool_calls" in response_json:
                tool_calls = [
                    {"id": f"call_{i}", "name": call["name"], "args": call["args"]}
                    for i, call in enumerate(response_json["tool_calls"])
                ]
                return AIMessage(content="", tool_calls=tool_calls)
        except json.JSONDecodeError:
            # 如果不是 JSON，假设是普通文本响应
            pass

        return AIMessage(content=response_text)

    def bind_tools(self, tools):
        # 模拟工具绑定，实际需要根据你的 LLM 支持情况调整
        self.tools = {tool.name: tool for tool in tools}
        return self

    @property
    def _llm_type(self) -> str:
        return "custom_llm"


if __name__ == "__main__":
    llm = CustomLLM(llm_name="google/gemma-3-1b-it")
    # res=llm.invoke("法国首都是是哪里")
    res = llm.invoke("where is japan")
    print(res)
