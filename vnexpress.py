import argparse
from datetime import date
import os
import json

# selenium import
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
)

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")
chrome_options.page_load_strategy = "eager"


# chrome_options.add_argument('--headless') # must options for Google Colab
def get_url(home_path: str, max_url: int):
    """
    The function `get_url` uses a web driver to scrape URLs from a webpage up to a specified maximum
    number, handling errors and navigating to the next page if needed.

    :param home_path: The `home_path` parameter in the `get_url` function is the URL of the webpage from
    which you want to extract URLs. It is the starting point for the web scraping process
    :type home_path: str
    :param max_url: The `max_url` parameter in the `get_url` function represents the maximum number of
    URLs that you want to retrieve from the website. The function will keep scraping URLs until it
    reaches this maximum number
    :type max_url: int
    """
    urls = []
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(home_path)
    id = 0
    page = 1
    start = -1
    cnt_err = 0
    while len(urls) < max_url:
        id += 1
        print(f"id={id}")
        try:
            element = driver.find_element(
                By.CSS_SELECTOR, f'a[data-medium="Item-{id}"]'
            )
            href = element.get_attribute("href")
            if start == -1:
                start = id
                print(f"page={page}, start={start}")
            print(href)
            urls.append(href)
            cnt_err = 0

        except (StaleElementReferenceException, NoSuchElementException) as e:
            cnt_err += 1
            if (
                start != -1 and cnt_err == 3
            ):  # nếu đang crawl mà có 3 bài lỗi liên tục -> nhảy qua trang tiếp theo để kiếm
                id -= cnt_err
                print(f"Bug at id={id + 1}, next, find in page={page + 1}")
                print("Finding start_id.......")
                driver.get(home_path + "-p" + str(page + 1))
                page += 1
                start = -1
                cnt_err = 0
            driver.refresh()
            # Chúng ta tạm bỏ lỗi bây giờ
            continue
        except Exception:
            print("Exception")
            continue
    driver.close()
    return urls


def get_content_metadata(driver, article_url):
    """
    Extracts and returns metadata and content from a given article URL.

    :param driver: Selenium WebDriver instance.
    :param article_url: URL of the article to extract data from.
    :return: Dictionary containing article metadata and content.
    """

    # Get to current article
    driver.get(article_url)

    # Thu thập title
    title = driver.find_element(
        by=By.CSS_SELECTOR, value="h1.title-detail"
    ).text.strip()

    # Thu thập description
    description = driver.find_element(
        by=By.CLASS_NAME, value="description"
    ).text.strip()

    # Thu thập thể loại
    lis_cat = driver.find_element(
        by=By.CSS_SELECTOR, value="ul.breadcrumb"
    ).find_elements(by=By.TAG_NAME, value="li")
    main_cat = lis_cat[0].text if len(lis_cat) > 0 else None
    sub_cat = []
    for i in range(1, len(lis_cat)):
        sub_cat.append(lis_cat[i].text)
    if len(sub_cat) == 0:
        sub_cat = None

    # Thu thập published date
    publish_date = (
        driver.find_element(by=By.CSS_SELECTOR, value='[itemprop="datePublished"]')
        .get_attribute("content")
        .strip()
    )

    # Thu thập content bài báo
    # Locate phần viết content
    article = driver.find_element(by=By.CSS_SELECTOR, value="article.fck_detail")
    # Lấy hết các đầu mục con của bài báo
    children = article.find_elements(by=By.XPATH, value="./*")

    contents = []
    author = "Unknown"

    # Check có phải dạng slide show hay không
    is_slide_show = False
    for idx, child in enumerate(children):
        text = child.text.strip()
        # Nếu mà element right align --> có thể là tác giả
        if (
            child.tag_name == "p"
            and (
                "right" in child.get_attribute("align")
                or "right" in child.get_attribute("style")
            )
            and idx >= len(children) - 3
        ):  # last three, align right --> author
            author = text
        elif (
            child.tag_name == "p" and child.get_attribute("class") == "Normal"
        ):  # paragraph
            # If center
            if len(text):
                if "center" in child.get_attribute(
                    "align"
                ) or "center" in child.get_attribute("style"):
                    contents.append(f"[{text}]")
                else:
                    contents.append(text)

        # Chỉ lấy caption của figure
        elif child.tag_name == "figure":
            ## If length > 100  --> not a caption, it's next description
            if len(text):
                if len(text) <= 100:  # nếu mà len <= 100 --> add thêm [] xung quanh
                    contents.append(f"[{text}]")
                else:
                    contents.append(text)

        # Nếu mà là slide show thì nó giống figure
        elif child.tag_name == "div" and "item_slide_show" in child.get_attribute(
            "class"
        ):
            is_slide_show = True  # slideshow
            if len(text):
                if len(text) <= 100:
                    contents.append(f"[{text}]")
                else:
                    contents.append(text)

        # Bỏ qua table bây giờ
        elif child.tag_name == "table":  # Do nothing rightnow
            pass

    if is_slide_show:
        author = text

    # Nếu mà vẫn chưa thấy author thì tìm bằng tag
    if author == "Unknown":
        try:
            author = driver.find_element(
                by=By.XPATH, value="//*[contains(@class, 'author')]"
            ).text
        except:
            pass

    return {
        "url": article_url,
        "title": title,
        "description": description,
        "content": "\n".join(contents),  # join các đoạn bằng \n
        "metadata": {
            "cat": main_cat,
            "subcat": sub_cat,
            "published_date": publish_date,
            "author": author,
        },
    }


def get_data(
    urls: list[str], output_file_path: str, driver: webdriver.Chrome | None = None
):
    count_crawled = 0
    cat_data = []
    if not driver:
        driver = webdriver.Chrome(options=chrome_options)
    for id_url, url in enumerate(urls):
        print(f"id_url={id_url}")
        try:
            cat_data.append(get_content_metadata(driver, url))
            count_crawled += 1
        except (StaleElementReferenceException, NoSuchElementException) as e:
            print(f"Bug at url: {url}, with ElementException")
            driver.refresh()
    with open(output_file_path, "w", encoding="utf-8") as fOut:
        json.dump(cat_data, fOut, ensure_ascii=False, indent=4)
    driver.close()


parser = argparse.ArgumentParser()
parser.add_argument(
    "--home-path",
    type=str,
    required=True,
    help="The home path for starting retrieving data",
)
parser.add_argument(
    "--max-url", type=int, default=10, required=False, help="Maximum of url retrieved"
)
parser.add_argument(
    "--output", type=str, default="./output.json", help="The output json path"
)
# TODO:
parser.add_argument(
    "--start-date", type=str, default=str(date.today()), help="Start date"
)
parser.add_argument(
    "--end-date", type=str, default=str(date.today()), help="Start date"
)
#########################################
# ISSUE: Cannot retrieve Author
# TODO: Multi-thread
args = parser.parse_args()

if __name__ == "__main__":
    urls = get_url(home_path=args.home_path, max_url=args.max_url)
    get_data(urls=urls, output_file_path=args.output)
