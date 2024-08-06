"""
book_id https://www.yuque.com/api/docs?book_id=xxx
book_stack https://www.yuque.com/api/mine/book_stacks  -> data[0].books[0].id

export https://www.yuque.com/api/docs/{book_id}/export data.url
                                          
download https://www.yuque.com/{login_name}/{ book_slug }/{md_slug}/markdown?attachment=true&latexcode=true&anchor=false&linebreak=false
"""


import requests
import os
import yaml

with open('config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.safe_load(file)

cookie = config['cookie']
target_dir = config['target_dir']

headers = {
    'Referer': 'https://www.yuque.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    "Cookie": cookie
}


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
    print(docs_json)
    md_ids = [el["id"] for el in docs_json["data"]]
    md_slugs = [el["slug"] for el in docs_json["data"]]
    md_title = [el["title"] for el in docs_json["data"]]
    print(md_ids)
    download_urls = []
    download_url_template = "https://www.yuque.com/{}/{}/{}/markdown?attachment=true&latexcode=true&anchor=false&linebreak=false"
    for md in md_slugs:
        download_urls.append(
            download_url_template.format(login_name, book_slug, md))
    if (os.path.exists(output_dir) == False):
        os.makedirs(output_dir)
    print(download_urls)
    for (md_slug, md_title) in zip(md_slugs, md_title):
        download_url = download_url_template.format(
            login_name, book_slug, md_slug)
        print(download_url)

        response = requests.get(download_url, headers=headers)
        with open(os.path.join(output_dir, md_title+'.md'), "w", encoding="utf-8") as f:
            print(f'{md_title}成功{response.status_code}')
            f.write(response.text)


if __name__ == "__main__":
    login_name = get_login_name()
    print(login_name)
    book_list = get_books()
    for book in book_list:
        print('开始下载', book["name"])
        get_md(book["id"], book["slug"],
               output_dir=os.path.join(target_dir, book["name"]))
