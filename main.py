"""
book_id https://www.yuque.com/api/docs?book_id=xxx
book_stack https://www.yuque.com/api/mine/book_stacks  -> data[0].books[0].id

export https://www.yuque.com/api/docs/{book_id}/export data.url
                                          
download https://www.yuque.com/{login_name}/{ book_slug }/{md_slug}/markdown?attachment=true&latexcode=true&anchor=false&linebreak=false
"""


import requests
import os
import yaml
import time
import random

with open('config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)

# with open('test_config.yaml', 'r', encoding='utf-8') as file:
#     config = yaml.safe_load(file)

cookie = config['cookie']
target_dir = config['target_dir']
sleep_time = config['sleep_time']

count_md=0


headers = {
    'Referer': 'https://www.yuque.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    "Cookie": cookie
}
login_name=""

# retryies(times=3,gap=1)
def retries(times=3, gap=1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    print(f"Retrying in {gap} seconds...")
                    time.sleep(gap)
            raise Exception(
                f"Function {func.__name__} failed after {times} retries.")
        return wrapper
    return decorator


def get_login_name():
    response = requests.get(
        'https://www.yuque.com/api/mine/book_stacks', headers=headers)
    book_stack = response.json()
    login_name = book_stack["data"][0]["books"][0]["summary"][0]["user"]["login"]
    return login_name


def get_books():
    response = requests.get(
        'https://www.yuque.com/api/mine/book_stacks', headers=headers)
    book_stack = response.json()
    book_list = []
    for book in book_stack['data'][0]['books']:
        dic = {}
        dic["name"] = book['name']
        dic["id"] = book['id']
        dic["slug"] = book["slug"]
        book_list.append(dic)
    print(book_list)
    return book_list


def get_md(book_id, book_slug, output_dir):
    docs_params = (
        ('book_id', book_id),
    )

    docs_response = requests.get('https://www.yuque.com/api/docs',
                                 headers=headers, params=docs_params)
    docs_json = docs_response.json()
    # print(docs_json)
    md_ids = [el["id"] for el in docs_json["data"]]
    md_slugs = [el["slug"] for el in docs_json["data"]]
    md_title = [el["title"] for el in docs_json["data"]]
    # print(md_ids)
    download_urls = []
    download_url_template = "https://www.yuque.com/{}/{}/{}/markdown?attachment=true&latexcode=true&anchor=false&linebreak=false"
    for md in md_slugs:
        download_urls.append(
            download_url_template.format(login_name, book_slug, md))
    if (os.path.exists(output_dir) == False):
        os.makedirs(output_dir)
    # print(download_urls)
    for (md_slug, md_title) in zip(md_slugs, md_title):
        download_url = download_url_template.format(
            login_name, book_slug, md_slug)
        # print(download_url)

        response = requests.get(download_url, headers=headers)
        global count_md

        download_md(download_url, os.path.join(output_dir, md_title+'.md'))
        time.sleep(sleep_time)

@retries(times=3, gap=1)
def download_md(download_url,output_dir):
    global count_md
    response = requests.get(download_url, headers=headers)
    count_md += 1
    with open(output_dir, 'w', encoding='utf-8') as file:
        print(f'{output_dir}下载完成 第{count_md}篇文章',response.status_code)
        file.write(response.text)

if __name__ == "__main__":
    start_time = time.time()

    login_name = get_login_name()
    print(login_name)
    book_list = get_books()
    for book in book_list:
        print('开始下载', book["name"])
        get_md(book["id"], book["slug"],
               output_dir=os.path.join(target_dir, book["name"]))
        
    end_time = time.time()
    print(f'共下载{count_md}篇文章')
    print(f"下载完成，耗时{end_time-start_time}秒")