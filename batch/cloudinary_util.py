import shutil, os, glob
from collections import defaultdict
import cloudinary, datetime
import cloudinary.api
import cloudinary.uploader
from dotenv import load_dotenv
from logger_config import get_logger

load_dotenv()
logger = get_logger(__name__)

# --- 配置 ---
# 从环境变量读取 Cloudinary 凭证 (这将由 GitHub Action 传入)
cloudinary.config(
    cloud_name=os.getenv("NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)

# 本地文件路径 (相对于项目根目录)
NOTDONE_PATH = "asset/pic/not_done"
DONE_PATH = "asset/pic/done"
DONE_MD_PATH = "asset/cloudonary_done.md"
DONE_MD_PREFIX = "[TIME]"
CLOUDINARY_ROOT_FOLDER = os.getenv("CLOUDINARY_FOLDER")

max_results = 1000


def get_cloudinary_comic_count():
    """获取 Cloudinary comic 根目录下的所有文件名"""
    logger.debug(
        f"正在从 Cloudinary 的 '{CLOUDINARY_ROOT_FOLDER}' 文件夹获取文件列表..."
    )

    resources = cloudinary.api.resources_by_asset_folder(
        "comic1", max_results=max_results
    )
    return len(resources.get("resources", []))


def get_cloudinary_comic_covers():
    """获取 Cloudinary comic 根目录下的所有文件名"""
    logger.debug(
        f"正在从 Cloudinary 的 '{CLOUDINARY_ROOT_FOLDER}' 文件夹获取文件列表..."
    )

    resources = cloudinary.api.resources_by_asset_folder(
        "comic1", max_results=max_results
    )

    # 我们只关心在 comic1 根目录下的文件, 形如 "comic1/a-1.jpg"
    # 排除子文件夹里的文件, 形如 "comic1/a/a-1.jpg"
    cover_files = set()
    for res in resources.get("resources", []):
        # public_id = res.get("public_id")
        # public_id 减去根目录前缀后，如果不包含'/'，说明它在根目录
        # if "/" not in public_id[len(CLOUDINARY_ROOT_FOLDER) + 1 :]:
        # 提取文件名, e.g., "a-1.jpg"
        # filename = os.path.basename(public_id)
        # cover_files.add(filename)
        display_name = res.get("display_name")
        cover_files.add(display_name)
    logger.debug(f"找到 {len(cover_files)} 个封面文件。")
    return cover_files


def group_local_files():
    """分组本地 notdone 文件夹中的图片"""
    logger.debug(f"正在扫描本地文件夹: {NOTDONE_PATH}")
    local_files = glob.glob(os.path.join(NOTDONE_PATH, "*.*"))
    grouped = defaultdict(list)
    for f in local_files:
        # 从文件名 "a-b.jpg" 中提取 "a" 作为组名
        group_name = os.path.basename(f).split("-")[0]
        grouped[group_name].append(f)
    logger.debug(f"找到 {len(grouped)} 个本地图片组。")
    return grouped


def move_group_to_done(group_files):
    """将一组文件移动到 done 文件夹"""
    if not os.path.exists(DONE_PATH):
        os.makedirs(DONE_PATH)
    for f in group_files:
        logger.debug(f"  移动文件: {os.path.basename(f)} -> {DONE_PATH}")
        shutil.move(f, os.path.join(DONE_PATH, os.path.basename(f)))


def main():
    only_count = True
    cloudinary_comic_count, cloudinary_covers = 0, []
    local_groups = group_local_files()

    with open(DONE_MD_PATH, "a", encoding="utf-8") as md_file:
        md_file.write(f"{DONE_MD_PREFIX}{datetime.datetime.now()}\n")

    if not len(local_groups):
        return

    if only_count:
        cloudinary_comic_count = get_cloudinary_comic_count()
    else:
        cloudinary_covers = get_cloudinary_comic_covers()

    for group_name, files in local_groups.items():
        logger.debug(f"\n--- 正在处理组: {group_name} ---")

        # 判断封面是否已存在于 Cloudinary
        # 检查是否有任何一个 Cloudinary 封面文件名是以 "group_name-" 开头的
        if only_count:
            is_uploaded = group_name > cloudinary_comic_count
        else:
            is_uploaded = group_name in cloudinary_covers

        if is_uploaded:
            logger.debug(f"组 '{group_name}' 的封面已存在于 Cloudinary。跳过上传。")
            move_group_to_done(files)
            continue

        # --- 如果不存在，执行上传逻辑 ---
        logger.debug(f"组 '{group_name}' 不存在于 Cloudinary。开始上传...")

        # 1. 上传封面 (组里的第一个文件) 到 comic1 根目录
        cover_file = sorted(files)[0]
        cover_filename = os.path.basename(cover_file)
        logger.debug(f"  1. 上传封面 '{cover_filename}' 到 '{CLOUDINARY_ROOT_FOLDER}'")
        cloudinary.uploader.upload(
            cover_file,
            folder=CLOUDINARY_ROOT_FOLDER,
            # public_id=os.path.splitext(cover_filename)[0],  # 使用不带扩展名的文件名作为 public_id
            public_id=group_name,
        )

        # 2. 上传所有文件到 comic1/group_name 子文件夹
        subfolder = f"{CLOUDINARY_ROOT_FOLDER}/{group_name}"
        logger.debug(f"  2. 上传 {len(files)} 个文件到子文件夹 '{subfolder}'")
        for f in files:
            filename = os.path.basename(f)
            logger.debug(f"    - 上传 {filename}")
            cloudinary.uploader.upload(
                f, folder=subfolder, public_id=os.path.splitext(filename)[0]
            )

        # 3. 更新 done.md
        logger.debug(f"  3. 更新 '{DONE_MD_PATH}' 文件")
        with open(DONE_MD_PATH, "a", encoding="utf-8") as md_file:
            md_file.write(f"{group_name},")

        # 4. 移动本地文件
        logger.debug("  4. 移动本地文件到完成目录")
        move_group_to_done(files)

        logger.debug(f"--- 组 '{group_name}' 处理完成 ---")


if __name__ == "__main__":
    main()
