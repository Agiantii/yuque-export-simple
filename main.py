"""
book_id https://www.yuque.com/api/docs?book_id=xxx
book_stack https://www.yuque.com/api/mine/book_stacks  -> data[0].books[0].id
book_catalog https://www.yuque.com/api/catalog_nodes?book_id={book_id}
export https://www.yuque.com/api/docs/{book_id}/export data.url
                                          
download https://www.yuque.com/{login_name}/{ book_slug }/{md_slug}/markdown?attachment=true&latexcode=true&anchor=false&linebreak=false
"""


from gettext import Catalog
from itertools import count
from httpx import get
import requests
import os
import yaml
import time
import json
import random

with open('config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)

# with open('test_config.yaml', 'r', encoding='utf-8') as file:
#     config = yaml.safe_load(file)
DEBUG_MODE = True
cookie = config['cookie']
target_dir = config['target_dir']
sleep_time = config['sleep_time']

count_md=0
node_info = {}

headers = {
    'Referer': 'https://www.yuque.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    "Cookie": cookie
}
login_name=""
download_url_template = "https://www.yuque.com/{}/{}/{}/markdown?attachment=true&latexcode=true&anchor=false&linebreak=false"

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

def debug(*args, **kwargs):
    """
    自定义调试函数，类似于 print，但可以根据 DEBUG_MODE 控制是否输出。
    """
    if DEBUG_MODE:
        print("[DEBUG]", *args, **kwargs)
def get_login_name():
    response = requests.get(
        'https://www.yuque.com/api/mine/book_stacks', headers=headers)
    book_stack = response.json()
    # debug(book_stack)
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

def dir_check(dir_path):
    if(os.path.exists(dir_path) == False):
        os.makedirs(dir_path)
def dfs(tree,root,output_dir,book_slug):
    global node_info
    for node in tree[root]:
        if(node['type']=='TITLE'):
            dir_check(os.path.join(output_dir,node['title']))
            debug(node["uuid"])
            dfs(tree,node['uuid'],os.path.join(output_dir,node['title']),book_slug)
        else:
            global count_md
            try:
                md_slug = node_info[node['id']]['slug']
                md_title = node_info[node['id']]['title']
                download_url = download_url_template.format(
                login_name, book_slug, md_slug)
                debug(download_url,os.path.join(output_dir, md_title+'.md'))
                download_md(download_url, os.path.join(output_dir, md_title+'.md'))
                time.sleep(sleep_time)
                count_md+=1
            except Exception as e:
                print(e)
def get_md(book_id, book_slug, output_dir):
    global node_info
    docs_params = (
        ('book_id', book_id),
    )

    docs_response = requests.get('https://www.yuque.com/api/docs',
                                 headers=headers, params=docs_params)
    docs_json = docs_response.json()
    # print(docs_json)
    if (os.path.exists(output_dir) == False):
        os.makedirs(output_dir)
    for node in docs_json["data"]:
        node_info[node["id"]] = node
    tree = build_tree(book_id)
    dfs(tree,"0",output_dir,book_slug)
    

    # md_ids = [el["id"] for el in docs_json["data"]]
    # md_slugs = [el["slug"] for el in docs_json["data"]]
    # md_title = [el["title"] for el in docs_json["data"]]
    # # print(md_ids)
    # download_urls = []
    # download_url_template = "https://www.yuque.com/{}/{}/{}/markdown?attachment=true&latexcode=true&anchor=false&linebreak=false"
    # for md in md_slugs:
    #     download_urls.append(
    #         download_url_template.format(login_name, book_slug, md))

    # # print(download_urls)
    # for (md_slug, md_title) in zip(md_slugs, md_title):
    #     download_url = download_url_template.format(
    #         login_name, book_slug, md_slug)
    #     # print(download_url)

    #     response = requests.get(download_url, headers=headers)
    #     global count_md
    #     download_md(download_url, os.path.join(output_dir, md_title+'.md'))
    #     time.sleep(sleep_time)
def get_book_catalog(book_id):
    catalog_params = (
        ('book_id', book_id),
    )
    catalog_res = requests.get('https://www.yuque.com/api/catalog_nodes', headers=headers, params=catalog_params).json()
    return catalog_res
def build_tree(book_id):
    catalog_res = get_book_catalog(book_id)
    tree = {}
    with open('temp/catalog.json', 'w', encoding='utf-8') as file:
        json.dump(catalog_res, file, ensure_ascii=False)
    # debug(catalog_res['data'])
    catalog_res = [node for node in catalog_res['data']]
    catalog_res.sort(key=lambda x: x['level'])
    # debug(catalog_res)
    # debug(catalog_res)
    tree["0"]=[]
    for node in catalog_res:
        if(tree.get(node['uuid'])==None):
            tree[node['uuid']]=[]
        if(node['parent_uuid']==""):
            tree["0"].append(node)
        else:          
            tree[node['parent_uuid']].append(node)
    return tree
@retries(times=3, gap=1)
def download_md(download_url,output_dir):
    global count_md
    response = requests.get(download_url, headers=headers)
    count_md += 1
    with open(output_dir, 'w', encoding='utf-8') as file:
        print(f'{output_dir}下载完成 第{count_md}篇文章',response.status_code)
        file.write(response.text)

def test():
    book_id = 42070265
    catalog_res = get_book_catalog(book_id)
    tree = build_tree(catalog_res)
    # with open('temp/tree.json', 'w', encoding='utf-8') as file:
    #     json.dump(tree, file, ensure_ascii=False)
if __name__ == "__main__":
    start_time = time.time()
    # debug(cookie)
    login_name = get_login_name()
    # debug(login_name)

    # test()
    book_list = get_books()
    for book in book_list:
        print('开始下载', book["name"])
        get_md(book["id"], book["slug"],
               output_dir=os.path.join(target_dir, book["name"]))
        
    end_time = time.time()
    print(f'共下载{count_md}篇文章')
    print(f"下载完成，耗时{end_time-start_time}秒")