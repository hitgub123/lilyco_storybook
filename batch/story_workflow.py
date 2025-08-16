from local_llm_util import Local_llm
from task_manager import Task_manager
import cloudinary_util
import generate_storybooks
import generate_stories
import os
from logger_config import get_logger
from dotenv import load_dotenv

load_dotenv()
logger = get_logger(__name__)

# 本地文件路径 (相对于项目根目录)
# NOTDONE_PATH = os.getenv("NOTDONE_PATH")
# DONE_PATH = os.getenv("DONE_PATH")
# DONE_MD_PATH = os.getenv("DONE_MD_PATH")
# DONE_MD_PREFIX = os.getenv("DONE_MD_PREFIX")
# CLOUDINARY_ROOT_FOLDER = os.getenv("CLOUDINARY_FOLDER")

llm = Local_llm(llm_name='google/gemma-3-270m-it')
tm = Task_manager()

def generate_stories_tool(story_topic="住在森林的黑猫凯露的日常生活",pic=None) :
    number_of_stories=1

    print(f"正在为主题 '{story_topic}' 生成 {number_of_stories} 个小故事...")
    generated_stories_1 = generate_stories.generate_stories_by_generation_func(
        topic=story_topic,
        number_of_stories=number_of_stories,
        generation_func=llm.invoke,  # 直接把方法作为参数传入
    )

    if generated_stories_1:
        print("\n--- 成功生成的故事列表---")
        for i, story in enumerate(generated_stories_1):
            print(f"{i}. {story}")
    else:
        logger.error("\n--- 未能生成故事 ---")

    tm.insert_task(generated_stories_1,pic=pic)
    return generated_stories_1


def generate_images_tool() :
    tasks = tm.read_df_from_csv()
    target_task = tasks.query("is_target == 1 and generate_storybook != 1")
    print("target_task", target_task)
    for _, task in target_task.iterrows():
        # prompt = "兔子托比在林间小溪上漂流,它沿途看到了很多鱼，它和其中一只叫波利的安康鱼做了朋友"
        prompt = task["text"]
        id = task["id"]
        pic= task["pic"]
        res = generate_storybooks.run(prompt=prompt, id=id, pic=pic)
        if res:
            tasks.loc[tasks["id"] == id, "generate_storybook"] = 1
            tm.update_task(tasks)
        else:
            logger.error('生成绘本失败')
    return [task for _, task in target_task.iterrows()]

def upload_images_to_cloudinary_tool() :
    cloudinary_util.main()
    uploaded_list=cloudinary_util.update_task_record(tm)
    return uploaded_list

if __name__ == "__main__":
    pic=r"C:\Users\81802\Downloads\pic\281395.jpg"
    # generate_stories_tool(pic=pic)
    generate_images_tool()
    upload_images_to_cloudinary_tool()
