import asyncio
import sys
from datetime import datetime
from playwright.async_api import async_playwright, expect

class TengxunyunBot:
    def __init__(self):
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
        self.running = True
        self.high_freq_task = None
        self.main_task = None

    async def setup(self):
        """初始化浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def teardown(self):
        """关闭浏览器"""
        self.running = False
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("end")

    async def main_task_executor(self):
        """主任务：定期检查按钮状态"""
        while self.running:
            try:
                # 查找主按钮
                button = self.page.locator(
                    "#LH > div > div > div.uno3-section__bd > div > div > div > div:nth-child(2) > div > div > div.uno3-buy-card__ft > div.uno3-buy-card__btn-progress > div.uno3-buy-card__btn"
                )
                button_text = await button.text_content()
                print(f"按钮状态: {button_text}")

                # 检查对话框是否存在
                dialog_footers = self.page.locator(".uno3-dialog-footer")
                count = await dialog_footers.count()

                if count > 0:
                    # 启动高频点击器
                    if self.high_freq_task is None or self.high_freq_task.done():
                        self.high_freq_task = asyncio.create_task(self.start_high_frequency_clicker())
                    await asyncio.sleep(0.05)  # 50ms
                    continue

                # 主按钮点击逻辑
                if button_text and button_text not in ["添加提醒", "取消提醒"]:
                    try:
                        await button.click()
                    except Exception as e:
                        # 使用JavaScript点击
                        await self.page.evaluate("arguments[0].click();", await button.element_handle())

                await asyncio.sleep(0.05)  # 50ms

            except Exception as e:
                print(f"主任务错误: {str(e)}")
                await asyncio.sleep(0.05)

    async def start_high_frequency_clicker(self):
        """高频点击器：不断尝试点击购买按钮"""
        print("启动高频点击器")
        while self.running:
            try:
                print("抢!!!")
                # 等待可点击的购买按钮，超时时间100秒
                buy_button = self.page.locator(".uno3-dialog-footer-btn .uno3-button--primary")
                
                try:
                    await asyncio.wait_for(
                        buy_button.wait_for(state="visible"),
                        timeout=100
                    )
                    # 使用JavaScript点击，避免被阻挡
                    await self.page.evaluate("arguments[0].click();", await buy_button.element_handle())
                except asyncio.TimeoutError:
                    pass

                await asyncio.sleep(0.03)  # 30ms

            except Exception as e:
                # 忽略单次错误，继续执行
                await asyncio.sleep(0.03)

    async def hello(self):
        """主函数"""
        try:
            # 访问目标网站
            await self.page.goto("https://cloud.tencent.com/act/pro/warmup202506?from=27490")
            
            # 获取用户输入
            print("请输入数字（回车继续）:")
            user_input = input()
            print(f"用户输入: {user_input}")

            # 启动主任务
            self.running = True
            main_task = asyncio.create_task(self.main_task_executor())

            print("程序运行中，按回车键退出...")
            # 在新线程中等待用户输入
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, input)

            # 停止任务
            self.running = False
            await asyncio.sleep(0.1)
            main_task.cancel()
            if self.high_freq_task and not self.high_freq_task.done():
                self.high_freq_task.cancel()

        except Exception as e:
            print(f"错误: {str(e)}")
            self.running = False

    async def run(self):
        """运行测试"""
        await self.setup()
        try:
            await self.hello()
        finally:
            await self.teardown()


async def main():
    bot = TengxunyunBot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
