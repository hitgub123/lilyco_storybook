from playwright.sync_api import sync_playwright, Playwright, expect
import time, os
from logger_config import get_logger
from dotenv import load_dotenv
import random

WAIT_TIME = 30 * 1000
load_dotenv()
NOTDONE_PATH = os.getenv("NOTDONE_PATH")
SCREENSHOT_QUALITY = int(os.getenv("SCREENSHOT_QUALITY"))
logger = get_logger(__name__)


def sleep_random(sleep_time=10, bias=1):
    r_sleep_time = random.randint(sleep_time - bias, sleep_time + bias)
    time.sleep(r_sleep_time)


def get_browser(playwright: Playwright):
    # ---. 连接到在9222端口上运行的现有浏览器 ---
    # 注意：这里不再是 launch()，而是 connect_over_cdp()
    logger.debug("正在连接到已打开的浏览器...")
    browser = playwright.chromium.connect_over_cdp("http://localhost:9222")

    # 获取浏览器的默认上下文和已打开的页面
    # 通常，手动打开的第一个标签页就是 context.pages[0]
    context = browser.contexts[0]

    # target_page = context.pages[-1]
    target_page = None
    TARGET_URL_PART = "storybook"
    # 遍历所有浏览器上下文（通常只有一个）
    for context in browser.contexts:
        # 遍历该上下文中的所有页面（标签页）
        for page in context.pages:
            # 检查当前页面的 URL 是否包含我们想要的目标字符串
            if TARGET_URL_PART in page.url:
                target_page = page
                break  # 找到后就跳出内层循环
        if target_page:
            break  # 找到后也跳出外层循环

    # 如果遍历完所有页面还是没找到，就报错退出
    if not target_page:
        logger.error(
            f"错误：在所有打开的标签页中，没有找到包含 '{TARGET_URL_PART}' 的页面。\n请确认你已经在指定的浏览器窗口中手动打开并登录了目标网站。"
        )
        browser.close()
        raise Exception(f"not found target page {TARGET_URL_PART}")
    logger.debug(f"连接成功！当前页面是: {target_page.title()}")
    return browser, context, target_page


def crawl_new_tab(context, href_storybook, id):
    logger.debug(f"开始访问会本页面,href={href_storybook},id={id}")
    id = str(id)
    new_tab = context.new_page()
    new_tab.goto(href_storybook)
    new_tab.bring_to_front()

    next_page_button = new_tab.locator(
        "button[aria-label='Next page'][data-test-id='next-page-button']"
    )
    expect(next_page_button).to_be_visible(timeout=WAIT_TIME)

    # cover_dir = os.path.join('cover', id)
    comic_dir = os.path.join(NOTDONE_PATH, id)
    # comic_dir = f"asset/pic/not_done/{id}"
    os.makedirs(comic_dir, exist_ok=True)

    current_page = 1
    while 1:
        # 这能确保图片等动态内容加载完成后再继续执行,not work here
        # new_tab.wait_for_load_state('networkidle', timeout=WAIT_TIME)

        # 1:{1},2:{2,3},3:{4,5},
        if current_page == 1:
            sleep_random(20)
        else:
            sleep_random(4)
            storybook_content = new_tab.locator("storybook-page[class='left']").nth(-1)
            screenshot_path = os.path.join(comic_dir, f"{id}-{current_page*2-2}.jpg")
            storybook_content.screenshot(
                path=screenshot_path, type="jpeg", quality=SCREENSHOT_QUALITY
            )

        # if current_page == 1:
        #     sleep_random(20)
        #     storybook_content = new_tab.locator("storybook-page[class='right']")
        #     screenshot_path = os.path.join(comic_dir, f"{id}-{current_page}.jpg")
        # else:
        #     sleep_random(4)
        #     storybook_content = new_tab.locator("storybook")
        #     screenshot_path = os.path.join(comic_dir, f"{id}-{current_page}.jpg")
        # expect(storybook_content).to_be_visible(timeout=WAIT_TIME)
        # expect(storybook_content).to_be_visible(timeout=WAIT_TIME)

        time.sleep(1)
        storybook_content = new_tab.locator("storybook-page[class='right']").nth(-1)
        screenshot_path = os.path.join(comic_dir, f"{id}-{current_page*2-1}.jpg")
        storybook_content.screenshot(
            path=screenshot_path, type="jpeg", quality=SCREENSHOT_QUALITY
        )
        logger.debug(f"操作成功！截图{screenshot_path}已保存。")
        current_page += 1
        if next_page_button.is_disabled():
            break
        next_page_button.click()
    new_tab.close()
    return True


def run(prompt, id=1, browser=None, context=None, target_page=None):
    if not browser or not context or not target_page:
        browser, context, target_page = get_browser(playwright)

    try:
        # 示例：在你登录后的页面上，找到某个元素并截图
        # 你需要把下面的选择器换成你登录后页面上的元素
        input_box = target_page.locator("rich-textarea p").first
        # 等待元素可见
        expect(input_box).to_be_visible(timeout=60)

        # while 1:
        #     text_=input_box.inner_text()
        #     match_res=re.match(r'^\s+$',text_)
        #     if not text_ or not match_res:
        #         break
        #     input_box.clear()
        for i in range(10):
            input_box.clear()

        prompt = f"不要让我补充内容，按我给的提示词和你自己的想法，为这个故事生成绘本:\n{prompt}"
        input_box.fill(prompt)

        time.sleep(3)
        target_page.keyboard.press("Control+Enter")

        # result_locator = target_page.locator("storybook")
        share_button = target_page.locator("share-button")

        logger.debug("正在等待share_button元素加载...")
        # networkidle not work here ,to_be_enabled also not work
        # target_page.wait_for_load_state("networkidle", timeout=WAIT_TIME*6)
        # expect 会在这里暂停脚本，直到元素可见，或者超时（默认30秒）
        expect(share_button).to_be_visible(timeout=180 * 1000)
        # expect(share_button).to_be_enabled(timeout=180 * 1000)
        sleep_random(15)
        share_button.click()

        button = share_button.locator("button").nth(1)
        expect(button).to_be_visible(timeout=WAIT_TIME)
        button.click()

        copy_link = target_page.locator('a[data-test-id="created-share-link"]')
        # target_page.wait_for_load_state("networkidle", timeout=WAIT_TIME)
        expect(copy_link).to_be_visible(timeout=WAIT_TIME)
        href_storybook = copy_link.get_attribute("href")

        share_canvas = copy_link.locator("xpath=..").locator("xpath=..")
        close_canvas_button = share_canvas.locator("button[mattooltip='Close']")
        expect(close_canvas_button).to_be_visible(timeout=WAIT_TIME)
        close_canvas_button.click()

        close_panel_button = target_page.locator(
            "button[aria-label='Close panel'][mattooltip='Close']"
        )
        expect(close_panel_button).to_be_visible(timeout=WAIT_TIME)
        close_panel_button.click()

        return crawl_new_tab(context, href_storybook, id)

    except Exception as e:
        logger.error(f"发生错误: {e}")

    finally:
        # --- 脚本结束时，我们不再关闭浏览器，以便你下次还可以使用 ---
        # browser.close() # 注释掉这一行
        logger.debug("脚本执行完毕。浏览器保持打开状态。")


if __name__ == "__main__":
    run_crawl_new_tab = 0
    # --- 运行主程序 ---
    with sync_playwright() as playwright:
        browser, context, target_page = get_browser(playwright)
        if run_crawl_new_tab:
            href_storybook = "https://gemini.google.com/share/51df2cd2bab9"
            id = input("input your comic id\n")
            crawl_new_tab(context, href_storybook, id)
        else:
            from task_manager import Task_manager

            tm = Task_manager()
            tasks = tm.read_df_from_csv()
            target_task = tasks.query("is_target == 1 and generate_storybook != 1")
            print("target_task", target_task)
            for _, task in target_task.iterrows():
                # prompt = "兔子托比在林间小溪上漂流,它沿途看到了很多鱼，它和其中一只叫波利的安康鱼做了朋友"
                prompt = task["text"]
                id = task["id"]
                res = run(prompt, id, browser, context, target_page)
                if res:
                    # tasks.loc[id, "generate_storybook"] = 1
                    tasks.loc[tasks["id"] == id, "generate_storybook"] = 1
                    tm.update_task(tasks)
                else:
                    logger.error('生成绘本失败')
