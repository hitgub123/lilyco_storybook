import os,datetime

DONE_MD_PATH = "asset/cloudonary_done.md"

def main():
    with open(DONE_MD_PATH, "a", encoding="utf-8") as md_file:
        md_file.write(f"{datetime.datetime.now()}\n")

    


if __name__ == "__main__":
    main()
