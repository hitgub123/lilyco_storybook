'''
主AI Agent文件，用于编排故事生成、图片制作和上传的整个流程。
'''
import os
import sys
import json
from typing import List, Callable

# 将batch目录添加到Python路径中，以便导入其中的模块
# 确保此脚本是从项目根目录（D:\workspace-lilyco\lilyco_storybook）运行的
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(project_root, 'batch'))

from langchain.agents import Tool, initialize_agent
from langchain.llms.fake import FakeListLLM

# 1. --- 模拟和封装工具 ---
# 这是对您现有工具的封装和模拟，以便Agent可以调用它们

# 模拟来自 llm_utils.py 的功能
class DummyStoryLLM:
    '''模拟一个拥有invoke方法的LLM，用于故事生成。'''
    def invoke(self, prompt: str) -> str:
        print(f"\n[DummyStoryLLM] 接收到提示: '{prompt[:30]}...'\n")
        print("[DummyStoryLLM] 正在返回预设的故事JSON...")
        stories = {
            "stories": [
                "小兔子托比发现了一张藏宝图，决定开始寻宝大冒险。",
                "在魔法森林里，托比遇到了聪明的狐狸芬尼克，它成了托比的伙伴。",
                "它们一起解开了谜题，找到了传说中由宝石构成的胡萝卜。"
            ]
        }
        return json.dumps(stories)

def generate_stories_tool(topic: str) -> List[str]:
    '''
    这是一个封装好的故事生成工具。
    它接收一个主题，内部使用Dummy LLM生成故事列表。
    '''
    print(f"\n[Tool: generate_stories] 正在为主题 '{topic}' 生成故事...")
    dummy_llm = DummyStoryLLM()
    try:
        response_text = dummy_llm.invoke(f"请为我生成关于{topic}的多个故事")
        stories = json.loads(response_text).get("stories", [])
        print(f"[Tool: generate_stories] 成功生成 {len(stories)} 个故事。\n")
        return stories
    except Exception as e:
        print(f"[Tool: generate_stories] 生成故事时出错: {e}\n")
        return []

# 模拟来自 generate_storybook.py 的功能
NOTDONE_PATH = os.path.join(project_root, "asset", "pic", "not_done")
def generate_images_tool(story: str) -> str:
    '''
    这是一个模拟的图片生成工具。
    它接收一个故事文本，并假装在本地创建了图片文件。
    '''
    print(f"\n[Tool: generate_images] 正在为故事 '{story[:30]}...' 生成图片...")
    os.makedirs(NOTDONE_PATH, exist_ok=True)
    # 模拟为每个故事生成3张图片
    for i in range(1, 4):
        # 使用故事的前几个字符和序号作为文件名
        safe_filename = "".join(x for x in story[:10] if x.isalnum()) 
        img_path = os.path.join(NOTDONE_PATH, f"{safe_filename}-{i}.jpg")
        with open(img_path, 'w') as f:
            f.write(story) # 将故事内容写入文件以作模拟
        print(f"[Tool: generate_images]   - 模拟创建了图片: {img_path}\n")
    return f"成功为故事 '{story[:20]}...' 生成了图片。"

# 模拟来自 cloudinary_util.py 的功能
def upload_to_cloudinary_tool(dummy_input: str = "") -> str:
    '''
    这是一个模拟的Cloudinary上传工具。
    它会假装上传not_done文件夹中的所有图片，然后删除它们。
    '''
    print("\n[Tool: upload_to_cloudinary] 开始模拟上传流程...")
    if not os.path.exists(NOTDONE_PATH) or not os.listdir(NOTDONE_PATH):
        msg = "[Tool: upload_to_cloudinary] 文件夹为空，没有图片需要上传。"
        print(msg)
        return msg

    files_to_upload = os.listdir(NOTDONE_PATH)
    print(f"[Tool: upload_to_cloudinary] 找到 {len(files_to_upload)} 个文件准备上传。\n")
    for filename in files_to_upload:
        file_path = os.path.join(NOTDONE_PATH, filename)
        print(f"[Tool: upload_to_cloudinary]   - 模拟上传: {filename}\n")
        os.remove(file_path) # 删除文件以模拟移动
        print(f"[Tool: upload_to_cloudinary]   - 清理本地文件: {filename}\n")
    
    print("[Tool: upload_to_cloudinary] 所有图片均已成功上传和清理。\n")
    return "所有图片均已成功上传到Cloudinary。"


# 2. --- 定义Agent和工具 ---
tools = [
    Tool(
        name="Story Generator",
        func=generate_stories_tool,
        description="当需要根据一个主题或提示词生成多个短故事时使用。输入应该是一个字符串形式的主题。",
    ),
    Tool(
        name="Image Generator",
        func=generate_images_tool,
        description="当需要为一个已经存在的短故事生成一系列图片时使用。输入应该是一个字符串形式的故事文本。",
    ),
    Tool(
        name="Cloudinary Uploader",
        func=upload_to_cloudinary_tool,
        description="当所有图片都生成完毕后，用于将它们全部上传到Cloudinary。这个工具不需要输入参数。",
    ),
]

# 3. --- 设置Agent的大脑 (使用FakeListLLM来预设思考和行动) ---
# 我们将预设LLM的反应，引导它按正确顺序调用工具
responses = [
    "Action: Story Generator\nAction Input: 一只勇敢的小兔子", # 第一步：生成故事
    # Agent会接收到故事列表，然后我们引导它为第一个故事生成图片
    "Action: Image Generator\nAction Input: 小兔子托比发现了一张藏宝图，决定开始寻宝大冒险。",
    # 为第二个故事生成图片
    "Action: Image Generator\nAction Input: 在魔法森林里，托比遇到了聪明的狐狸芬尼克，它成了托比的伙伴。",
    # 为第三个故事生成图片
    "Action: Image Generator\nAction Input: 它们一起解开了谜题，找到了传说中由宝石构成的胡萝卜。",
    # 所有图片生成完毕，引导它上传
    "Action: Cloudinary Uploader\nAction Input: (none)",
    # 上传完成，给出最终答案
    "Thought: 所有步骤都已完成。故事已生成，图片已制作并上传。\nFinal Answer: 我已经成功根据提示词创作了多个故事，并为它们生成图片上传到了Cloudinary。",
]
llm = FakeListLLM(responses=responses)

# 4. --- 初始化并运行Agent ---
agent = initialize_agent(
    tools,
    llm,
    agent="zero-shot-react-description",
    verbose=True, # 设置为True可以看到Agent的思考过程
)

if __name__ == "__main__":
    print("--- Agent开始运行 ---")
    try:
        # 初始提示词，Agent将根据这个提示词开始它的工作流程
        initial_prompt = "请帮我创作一个关于一只勇敢的小兔子的故事，并生成图片上传"
        agent.run(initial_prompt)
        print("\n--- Agent运行结束 ---")
    except Exception as e:
        print(f"Agent在运行过程中遇到错误: {e}")
