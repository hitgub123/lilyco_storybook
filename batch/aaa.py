
import operator
from typing import TypedDict, Annotated, List

from langgraph.graph import StateGraph, END

# --- 步骤 1: 定义工作流的状态 ---
# 定义一个字典，用于在图的各个节点之间传递数据。
class WorkflowState(TypedDict):
    # 初始输入的主题
    topic: str
    # 每一步执行后的日志信息
    log: Annotated[List[str], operator.add]
    # 下一步要执行的节点名称，这是路由的关键
    next_step: str
    # 各个步骤的产出结果
    story_result: str
    image_result: str
    upload_result: str
    db_result: str


# --- 步骤 2: 定义图中的各个节点（每个节点代表一个工作步骤） ---
# 为了让代码能独立运行，我们先模拟一下工具函数

def generate_stories_tool(topic: str) -> str:
    print(f"  (模拟工具执行: 正在为 '{topic}' 生成故事...)")
    return f"关于'{topic}'的故事内容"

def generate_images_tool(story_content: str) -> str:
    print(f"  (模拟工具执行: 正在为故事生成图片...)")
    return "图片已生成，路径为 /images/story.jpg"

def upload_images_tool(image_path: str) -> str:
    print(f"  (模拟工具执行: 正在上传图片 '{image_path}'...)")
    return "图片已上传到 a.com/image.jpg"

def update_database_tool(image_url: str) -> str:
    print(f"  (模拟工具执行: 正在用 '{image_url}' 更新数据库...)")
    return "数据库更新成功"

# --- 定义节点函数 ---
# 每个节点函数接收当前状态(state)，执行操作，并返回一个字典来更新状态。

def node_generate_story(state: WorkflowState) -> dict:
    """节点1: 生成故事"""
    print("节点 [1/4]: 生成故事")
    topic = state["topic"]
    result = generate_stories_tool(topic)
    # 返回结果，并指定下一步要去'generate_images'
    return {
        "story_result": result,
        "log": [f"故事生成成功: {result}"],
        "next_step": "generate_images"
    }

def node_generate_images(state: WorkflowState) -> dict:
    """节点2: 生成图片"""
    print("节点 [2/4]: 生成图片")
    story_result = state["story_result"]
    result = generate_images_tool(story_result)
    # 返回结果，并指定下一步要去'upload_images'
    return {
        "image_result": result,
        "log": [f"图片生成成功: {result}"],
        "next_step": "upload_images"
    }

def node_upload_images(state: WorkflowState) -> dict:
    """节点3: 上传图片"""
    print("节点 [3/4]: 上传图片")
    image_result = state["image_result"]
    result = upload_images_tool(image_result)
    # 返回结果，并指定下一步要去'update_database'
    return {
        "upload_result": result,
        "log": [f"图片上传成功: {result}"],
        "next_step": "update_database"
    }

def node_update_database(state: WorkflowState) -> dict:
    """节点4: 更新数据库"""
    print("节点 [4/4]: 更新数据库")
    upload_result = state["upload_result"]
    result = update_database_tool(upload_result)
    # 返回结果，并指定流程结束
    return {
        "db_result": result,
        "log": [f"数据库更新成功: {result}"],
        "next_step": "end"
    }


# --- 步骤 3: 定义路由逻辑 ---
# 这个函数就是我们的路由器。它检查状态中的'next_step'字段，
# 然后返回对应的节点名称，告诉图下一步该去哪里。
def router(state: WorkflowState) -> str:
    """
    根据 state['next_step'] 的值来决定下一个要执行的节点。
    """
    print(f"--- 路由器: 当前步骤 '{state['next_step']}'，决定下一步走向 ---")
    next_step = state["next_step"]
    if next_step == "generate_images":
        return "generate_images_node"
    elif next_step == "upload_images":
        return "upload_images_node"
    elif next_step == "update_database":
        return "update_database_node"
    elif next_step == "end":
        return END # END 是一个特殊信号，表示工作流结束

# --- 步骤 4: 构建并编译图 ---
def create_workflow():
    # 创建一个状态图实例
    workflow = StateGraph(WorkflowState)

    # 添加所有节点
    workflow.add_node("generate_story_node", node_generate_story)
    workflow.add_node("generate_images_node", node_generate_images)
    workflow.add_node("upload_images_node", node_upload_images)
    workflow.add_node("update_database_node", node_update_database)

    # 设置入口点
    workflow.set_entry_point("generate_story_node")

    # 添加从每个任务节点到路由器的边
    workflow.add_edge("generate_images_node", "update_database_node") # 示例：也可以添加固定边
    workflow.add_edge("upload_images_node", "update_database_node")
    
    # 添加条件边（路由的关键）
    # 从'generate_story_node'出来后，调用'router'函数，
    # 'router'函数的返回值将决定下一个节点的走向。
    workflow.add_conditional_edges(
        "generate_story_node",
        router,
        {
            "generate_images": "generate_images_node",
            "upload_images": "upload_images_node",
            "update_database": "update_database_node",
            END: END
        }
    )
    workflow.add_conditional_edges(
        "update_database_node",
        router,
        {
            END: END
        }
    )


    # 编译图，使其成为一个可执行的应用
    return workflow.compile()


# --- 步骤 5: 运行工作流 ---
if __name__ == "__main__":
    # 创建工作流应用
    app = create_workflow()

    # 定义初始输入
    initial_input = {
        "topic": "一个宇航员和他的太空狗的故事",
        "log": [],
        "next_step": "generate_story" # 初始状态
    }

    print("--- 开始执行工作流 ---")
    # 执行工作流
    final_state = app.invoke(initial_input)
    print("--- 工作流执行完毕 ---")

    # 打印最终状态
    print("\n--- 最终结果 ---")
    from pprint import pprint
    pprint(final_state)
