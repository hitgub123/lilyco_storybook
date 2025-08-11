import pandas as pd
import os
from logger_config import get_logger

logger = get_logger(__name__)


class Task_manager:
    def __init__(
        self,
        csv_path="asset/task.csv",
        csv_columns=[
            "id",
            "text",
            "generate_storybook",
            "upload_storybook",
            "is_target",
            "pic",
        ],
        encoding="utf-8-sig",
    ) -> None:

        # 定义 CSV 文件的路径和列名
        self.CSV_PATH = csv_path
        self.CSV_COLUMNS = csv_columns
        self.encoding = encoding

    def read_df_from_csv(self):
        return pd.read_csv(self.CSV_PATH)

    def insert_task(self, text_list: list[str]):
        # 确保 asset 文件夹存在
        os.makedirs(os.path.dirname(self.CSV_PATH), exist_ok=True)

        start_id = 0
        # 如果文件已存在，读取现有数据以确定新的 id 起始值
        if os.path.exists(self.CSV_PATH):
            try:
                df_existing = self.read_df_from_csv()
                if not df_existing.empty:
                    start_id = df_existing["id"].max()
            except pd.errors.EmptyDataError:
                logger.debug(f"'{self.CSV_PATH}' 文件为空，将从头开始写入。")
                df_existing = pd.DataFrame()
        else:
            df_existing = pd.DataFrame()

        # 根据输入的文本列表，创建新的数据
        new_data = []
        for i, text in enumerate(text_list, start=1):
            new_data.append(
                {
                    self.CSV_COLUMNS[0]: start_id + i,
                    self.CSV_COLUMNS[1]: text,
                    self.CSV_COLUMNS[2]: 0,
                    self.CSV_COLUMNS[3]: 0,
                    self.CSV_COLUMNS[4]: 1,
                    self.CSV_COLUMNS[5]: 0,
                }
            )

        if not new_data:
            logger.warning("没有需要添加的新任务。")
            return

        # 将新数据转换为 DataFrame
        df_new = pd.DataFrame(new_data, columns=self.CSV_COLUMNS)

        # 将新数据追加到文件中
        # 如果文件是第一次创建，mode='w' 会写入表头
        # 如果是追加，mode='a' 和 header=False 可以避免重复写入表头
        write_header = not os.path.exists(self.CSV_PATH) or df_existing.empty
        df_new.to_csv(
            self.CSV_PATH,
            mode="a",
            header=write_header,
            index=False,
            encoding=self.encoding,
        )

    def update_task(self, df: pd.DataFrame):
        # df_total = self.read_df_from_csv()

        # if not df_total.empty:
        #     # 使用 .loc[行索引, 列名] 来定位并修改数据
        #     df_total.loc[0, self.CSV_COLUMNS[2]] = -1

        #     # 将修改后的整个 DataFrame 写回文件，这次是覆盖模式
        #     df_total.to_csv(
        #         self.CSV_PATH,
        #         mode="w",
        #         header=True,
        #         index=False,
        #         encoding=self.encoding,
        #     )
        df.to_csv(
                self.CSV_PATH,
                mode="w",
                header=True,
                index=False,
                encoding=self.encoding,
            )        
        logger.debug("修改成功。")


# --- 主程序入口 ---
if __name__ == "__main__":
    # 这是一个示例用法
    # 定义一个包含多个文本的列表
    tasks_to_add = [
        "这是第一个故事的文本内容。",
        "这是第二个故事,关于一只,勇敢的小猫。",
        "第三个故事发生在一个魔法森林里。",
    ]

    # 调用主方法
    tm = Task_manager()
    df = tm.read_df_from_csv()
    tm.insert_task(tasks_to_add)
    # tm.update_task(df=None)
