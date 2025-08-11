from playwright.sync_api import sync_playwright, Playwright, expect
import time
from logger_config import get_logger

WAIT_TIME = 30 * 1000
logger = get_logger(__name__)


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
    TARGET_URL_PART = "gemini.google.com/storybook"
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
            f"错误：在所有打开的标签页中，没有找到包含 '{TARGET_URL_PART}' 的页面。"
        )
        logger.error("请确认你已经在指定的浏览器窗口中手动打开并登录了目标网站。")
        browser.close()
        return
    logger.debug(f"连接成功！当前页面是: {page.title()}")
    return browser, context, target_page


def run(prompt,browser=None, context=None, target_page=None):
    if not browser or not context or not target_page:
        browser, context, target_page = get_browser(playwright)

    try:
        # 示例：在你登录后的页面上，找到某个元素并截图
        # 你需要把下面的选择器换成你登录后页面上的元素
        input_box = target_page.locator("rich-textarea p").first
        # 等待元素可见
        expect(input_box).to_be_visible(timeout=60)
        input_box.fill(prompt)

        time.sleep(1)
        target_page.keyboard.press("Control+Enter")

        # result_locator = target_page.locator("storybook")
        share_button = target_page.locator("share-button")

        logger.debug("正在等待share_button元素加载...")
        # expect 会在这里暂停脚本，直到元素可见，或者超时（默认30秒）
        expect(share_button).to_be_visible(timeout=180 * 1000)
        share_button.click()

        button = share_button.locator("button").nth(1)
        expect(button).to_be_visible(timeout=WAIT_TIME)
        button.click()

        copy_link = target_page.locator('a[data-test-id="created-share-link"]')
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

        new_tab = context.new_page()
        new_tab.goto(href_storybook)
        new_tab.bring_to_front()

        next_page_button = new_tab.locator(
            "button[aria-label='Next page'][data-test-id='next-page-button']"
        )
        expect(next_page_button).to_be_visible(timeout=WAIT_TIME)

        current_page = 1
        while 1:
            if current_page == 1:
                storybook_content = new_tab.locator("storybook-page[class='right']")
            else:
                storybook_content = new_tab.locator("storybook")
            expect(storybook_content).to_be_visible(timeout=WAIT_TIME)
            screenshot_path = f"/asset/pic/not_done/{current_page}.jpg"
            storybook_content.screenshot(path=screenshot_path)
            logger.debug(f"操作成功！截图{screenshot_path}已保存。")
            current_page += 1
            if next_page_button.is_disabled():
                break
            next_page_button.click()
            time.sleep(3)
        new_tab.close()

    except Exception as e:
        logger.error(f"发生错误: {e}")

    finally:
        # --- 脚本结束时，我们不再关闭浏览器，以便你下次还可以使用 ---
        # browser.close() # 注释掉这一行
        logger.debug("脚本执行完毕。浏览器保持打开状态。")


if __name__ == "__main__":
    # --- 运行主程序 ---
    with sync_playwright() as playwright:
        browser, context, target_page = get_browser(playwright)
        story = "兔子托比在林间小溪上漂流,它沿途看到了很多鱼，它和其中一只叫波利的安康鱼做了朋友"
        prompt = f"不要问我问题，按我给的上下文和你的想法帮我做一个storybook:{story}"
        run(prompt,browser, context, target_page)
