# coding:utf-8
import time
import urllib.request
import requests
import re
import os
import pymysql
import shutil  # 高级文件操作
import smtplib  # 发送邮件
import logging
import ColorUtil
import socks  # 翻墙代理
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime
from os.path import getsize

lang = "chinese"
index_page = "https://hitomi.la/index-chinese-1.html"
# base_path = "./"
base_path = "/Volumes/CrazyBunQnQ/视频/Don't See It/H漫画/Hitomi/"
# zip_path = "./zips/"
zip_path = "/Volumes/CrazyBunQnQ/视频/Don't See It/H漫画/Hitomi/zips/"
# video_path = "./videos/"
# video_path = "H:/视频/Don't See It/HitomiVideos/"
video_path = "/Volumes/CrazyBunQnQ/视频/Don't See It/HitomiVideos/"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
referer = "https://hitomi.la"

socks.set_default_proxy(socks.SOCKS5, '127.0.0.1', 1086)
socket.socket = socks.socksocket
opener = urllib.request.build_opener()
headers = {'User-agent': user_agent, 'Referer': referer}
opener.addheaders = [('User-agent', user_agent), ('Referer', referer)]
mode = 'wb'
# 当为True时，设置header，断点续传
header_flag = False

is_send_email = False
is_down_image = True
is_down_video = False
is_delete_src = False
min_video_size = 921600
download_only_color_images = True
zip_size = 48000000
min_colors_count = 3
max_email_count = 90
cur_email_count = 0
target_page = 200000
# target_page = 200

# Database information
DB_HOST = ""
DB_USER = "root"
DB_PWD = ""
DB_NAME = "Hitomi"
DB_CHARSET = "utf8mb4"

# 正则表达式
# TODO chinese 改为 lang
rex_pagin = r'(<a href="/index-chinese-(\d+)\.html">)'
rex_comic_info = r'(<div class="manga">.*</div>)'
rex_comic_info2 = r'(<div class="gallery\s+([a-z]+)-gallery[\u0000-\uffff]+</span>\s+</div>\s+</div>)'
rex_redirect = r'(If you are not redirected automatically)'
rex_name = r'(<h1><a href="/reader/\d+.html">(.+)</a></h1>)'
rex_anime_name = r'(<h1>(.+)</h1>)'
rex_lang = r'(<td>Language</td><td><a href="/index-[a-zA-Z]+-\d+.html">(.+)</a></td>)'
rex_acg_lang = r'(<td>Language</td><td>(.+)</td>)'
rex_data = r'(<span class="date">(.+)</span>)'
rex_big_pic = r'(src="//(\w)\.hitomi\.la/galleries/\d+/.+\.((jpg)|(bmp)|(png)|(gif))")'
rex_pic = r'(//g.*?\.((jpg)|(bmp)|(png)|(gif)))'
# rex_jwplayer = r'(file:\s+"(.+)",)'
rex_jwplayer = r'(url_from_url\(\'(.+)\'\);)'
rex_windows_name = r'([/\?\*:\|\\<>])'

# Email
mail_host = "smtp.163.com"  # 设置服务器
mail_user = "crazybunqnq@163.com"  # 用户名
mail_pass = "2y26cghC2r63"  # 口令
sender = 'crazybunqnq@163.com'
receivers = ['494225231@qq.com', '729383855@qq.com']  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱
mail_port = 25
mail_from = '李经理'
mail_to = "小包"
# 主题
subject = '任务进度预览'

# 日志设置
logging.basicConfig(
    filename='logs/app' + datetime.now().strftime('%Y-%m-%d') + '.log',
    format='%(asctime)s - %(module)s - %(levelname)s :  %(message)s',
    datefmt='%H:%M:%S %p',
    level=logging.DEBUG
)


def get_download_status():
    logging.error("")


def get_cur_num():
    try:
        db_connect = pymysql.connect(host=DB_HOST, user=DB_USER, passwd=DB_PWD, db=DB_NAME, charset=DB_CHARSET)
        cursor = db_connect.cursor()
        sql = "select t.num from cur_page t"
        cursor.execute(sql)
        num = cursor.fetchone()[0]
        db_connect.close()
        return num
    except Exception as e:
        logging.error(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + str(e))
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + str(e))
        logging.error(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 获取数据库当前漫画 id 错误")
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 获取数据库当前漫画 id 错误")
        # post_ifttt_webhook_link(EVENT_NAME, "价格提醒脚本出错啦！", "数据库查询出错！有空记得检查一下哟！", "")
        return -1


def update_cur_num(num):
    try:
        db_connect = pymysql.connect(host=DB_HOST, user=DB_USER, passwd=DB_PWD, db=DB_NAME, charset=DB_CHARSET)
        cursor = db_connect.cursor()
        sql = "update cur_page t set t.num = " + str(num)
        # logging.error(sql)
        cursor.execute(sql)
        db_connect.commit()
        db_connect.close()
        return True
    except Exception as e:
        logging.error(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + str(e))
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + str(e))
        logging.error(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 更新数据库当前漫画 id 错误")
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 更新数据库当前漫画 id 错误")
        # post_ifttt_webhook_link(EVENT_NAME, "价格提醒脚本出错啦！", "数据库查询出错！有空记得检查一下哟！", "")
        return False


def get_last_page():
    try:
        response = urllib.request.urlopen(index_page, timeout=20)
        html = response.read()
        html = html.decode('utf-8')
        page_container = re.findall(rex_pagin, html)
        if len(page_container) > 0:
            return page_container[len(page_container) - 1][1]
        return 1
    except Exception as e:
        logging.error(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + str(e))
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + str(e))
        logging.error(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " get last page failure")
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " get last page failure")
        return 1


def get_comic_info(num):
    dic = {}
    comic_info_page = "https://hitomi.la/galleries/%s.html" % str(num)
    logging.debug(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 进入 %s 页面..." % comic_info_page)
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 进入 %s 页面..." % comic_info_page)
    try:
        response = urllib.request.urlopen(comic_info_page, timeout=20)
        html = response.read()
        html = html.decode('utf-8')
        arr = re.findall(rex_redirect, html)
        if len(arr) > 0:
            return -2
        info_txt = re.findall(rex_comic_info2, html)[0]
        # logging.error(info_txt)
        comic_type = info_txt[1]
        info_txt = info_txt[0]
        if comic_type == "anime":
            comic_name = re.findall(rex_anime_name, info_txt)[0][1]
        else:
            comic_name = re.findall(rex_name, info_txt)[0][1]
        if comic_type == "acg" or comic_type == "cg":
            comic_lang = re.findall(rex_acg_lang, info_txt)[0][1]
        else:
            comic_lang = re.findall(rex_lang, info_txt)[0][1]
        # logging.error("name: %s, lang: %s" % (comic_name, comic_lang))
        if comic_lang == "中文" or comic_type == "anime" or comic_type == "acg" or comic_type == "cg":
            dic['name'] = comic_name
            dic['langguage'] = comic_lang
            dic['type'] = comic_type
            return dic
        else:
            return -1

        # page_container = re.findall(rex_pagin, html)
    except Exception as e:
        logging.error(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + str(e))
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + str(e))
        logging.error(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 获取漫画信息失败")
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 获取漫画信息失败")
        if str(e).find("Error 404: Not Found"):
            return -3
        if str(e).find("Errno 11001"):
            return 2
        return -1


def down_pic(url, save_path):
    logging.debug(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "正在下载 %s" % url)
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "正在下载 %s" % url)
    pic_name = url[str(url).rfind("/") + 1:]
    # logging.error(pic_name)
    pic_full_name = save_path + '/' + pic_name
    try:
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(url, pic_full_name)
        if download_only_color_images:
            logging.debug(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 判断是否是彩色图片...")
            print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 判断是否是彩色图片...")
            colors = ColorUtil.get_color_structure(pic_full_name)
            if len(colors) < min_colors_count:
                logging.debug(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 非彩色图片，删除该图片...")
                print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 非彩色图片，删除该图片...")
                os.remove(pic_full_name)
        return "成功"
    except Exception as e:
        logging.error(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + str(e))
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + str(e))
        logging.error(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 下载漫画出错")
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 下载漫画出错")
        return e


def zip_file(file_name, down_path):
    logging.debug(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 开始压缩漫画...")
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 开始压缩漫画...")
    zip_name = shutil.make_archive(zip_path + file_name, "zip", down_path)
    zip_name = zip_name[zip_name.rfind("/") + 1:]
    if file_name + ".zip" == zip_name:
        logging.debug(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 压缩完成，删除目录...")
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 压缩完成，删除目录...")
        if is_delete_src:
            shutil.rmtree(down_path)
        return zip_name
    else:
        logging.debug(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 压缩漫画失败，保留漫画目录")
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 压缩漫画失败，保留漫画目录")
        return -1


def zip_comic(file_name, file_path, size):
    file_num = 1
    cur_size = 0
    zips = []
    for root, dirs, files in os.walk(file_path):
        os.makedirs(file_path + '_' + str(file_num), mode=0o777)
        for name in files:
            file_size = getsize(file_path + '/' + name)
            cur_size += file_size
            # print("当前文件大小为 %s, 总大小为 %s" % (file_size, cur_size))
            if cur_size < size:
                os.rename(file_path + '/' + name, file_path + '_' + str(file_num) + '/' + name)
            else:
                zip_name = zip_file(file_name + '_' + str(file_num), file_path + '_' + str(file_num))
                if zip_name != -1:
                    zips.append(zip_path + zip_name)
                else:
                    logging.error(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 压缩文件失败，请检查.................")
                    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 压缩文件失败，请检查..........................")
                cur_size = file_size
                file_num += 1
                os.mkdir(file_path + '_' + str(file_num), mode=0o777)
                os.rename(file_path + '/' + name, file_path + '_' + str(file_num) + '/' + name)
        if cur_size < size:
            zip_name = zip_file(file_name + '_' + str(file_num), file_path + '_' + str(file_num))
            # 删除源目录
            if is_delete_src:
                shutil.rmtree(file_path)
            if zip_name != -1:
                zips.append(zip_path + zip_name)
            else:
                logging.error(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 压缩文件失败，请检查.................")
                print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 压缩文件失败，请检查..........................")
    if len(zips) == 0:
        return -1
    else:
        return zips


def send_email(name, attachments):
    logging.debug(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 发送邮件...")
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 发送邮件...")
    message = MIMEMultipart()
    message['From'] = Header(mail_from + '<' + sender + '>', 'utf-8')
    # message['To'] = Header(mail_to, 'utf-8')
    message['To'] = ','.join(receivers)
    # 主题
    message['Subject'] = Header(subject, 'utf-8')
    # 正文
    comic_name = name[:name.find("_")]
    message.attach(MIMEText("请及时添加新功能 %s，详情请查阅附件" % comic_name, 'plain', 'utf-8'))
    # 附件
    try:
        for zip_name in attachments:
            attachment = MIMEText(open(zip_name, 'rb').read(), 'base64', 'utf-8')
            attachment["Content-Type"] = 'application/octet-stream'
            # 这里的 filename 可以任意写，写什么名字，邮件中显示什么名字
            filename = zip_name[zip_name.rfind('/') + 1:]
            attachment["Content-Disposition"] = 'attachment; filename="' + filename + '"'
            message.attach(attachment)

        smtp_obj = smtplib.SMTP()
        smtp_obj.connect(mail_host, mail_port)  # 25 为 SMTP 端口号
        smtp_obj.login(mail_user, mail_pass)
        smtp_obj.sendmail(sender, receivers, message.as_string())
        logging.debug(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 邮件发送成功")
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 邮件发送成功")

        return "成功"
    except smtplib.SMTPException as e:
        logging.error(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + str(e))
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + str(e))
        logging.error(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " Error: 无法发送邮件")
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " Error: 无法发送邮件")
        return e


def down_comic(pic_list, name, num):
    # 创建目录
    file_name = name + "_" + datetime.now().strftime('%Y%m%d%H%M%S')
    down_path = base_path + file_name
    os.makedirs(down_path, mode=0o777)
    first_w = "aa"
    for picurl in pic_list:
        url = picurl[0].replace("//g.", "https://%s." % first_w)
        result = down_pic(url, down_path)
        if result != "成功" and str(result).find("403: Forbidden") > 0:
            if first_w == "aa":
                first_w = "ba"
            else:
                first_w = "aa"
            url = picurl[0].replace("//g.", "https://%s." % first_w)
            logging.debug(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 尝试第二个下载网址")
            print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 尝试第二个下载网址")
            down_pic(url, down_path)
        # logging.error(url)
    if not os.listdir(down_path):
        logging.error('目录为空')
        shutil.rmtree(down_path)
        update_cur_num(num + 1)
        logging.debug(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 漫画地址失效，准备下载下一部漫画...")
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 漫画地址失效，准备下载下一部漫画...")
        return 2
    logging.error("完成下载 %s 漫画")

    # 压缩目录
    zips = zip_comic(file_name, down_path, zip_size)
    if zips == -1:
        update_cur_num(num + 1)
        logging.debug(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 准备下载下一部漫画...")
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 准备下载下一部漫画...")
        return 3

    # 发送邮件
    if is_send_email:
        result = send_email(file_name, zips)
        if result == "成功":
            logging.debug(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 删除压缩文件...")
            print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 删除压缩文件...")
            for zip_name in zips:
                os.remove(zip_name)
            update_cur_num(num + 1)
            return 1
        else:
            exit()
            logging.debug(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 保留该漫画的压缩文件")
            print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 保留该漫画的压缩文件")
            update_cur_num(num + 1)
            return 4
    else:
        update_cur_num(num + 1)
        return 1


def download_file(url, save_path):
    re = requests.head(url, allow_redirects=True, timeout=20)
    file_total = re.headers['Content-Length']
    if os.path.exists(save_path) and header_flag:
        headers['Range'] = 'bytes=%d-' %os.path.getsize(save_path)
        mode = 'ab'
    r = requests.get(url, stream=True, headers=headers)
    with open(save_path, mode) as code:
        for chunk in r.iter_content(chunk_size=1024):  # 边下载边存硬盘
            if chunk:
                code.write(chunk)
            else:
                break
    time.sleep(1)


def down_video(url, name, num):
    name = name + "_" + str(num) + url[url.rfind("."):]
    # name = name + "_" + datetime.now().strftime('%Y%m%d%H%M%S') # 不加后缀
    name = re.sub(rex_windows_name, '_', name)
    logging.debug(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 正在下载动画 %s" % name)
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 正在下载动画 %s" % name)
    save_path = video_path + name
    try:
        print(url + " " + save_path)
        urllib.request.install_opener(opener)
        # urllib.request.urlretrieve(url, save_path)
        download_file(url, save_path)
        return 1
    except Exception as e:
        if str(e).find("got only") >= 0 or str(e).find("urlopen error EOF") > 0:
            return 2
        if str(e).find("403: Forbidden") >= 0:
            return 3
        else:
            logging.error(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + str(e))
            print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + str(e))
            logging.error(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 下载动画出错")
            print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 下载动画出错")
            exit()
            # return e


def get_pic_list(num):
    comic = get_comic_info(num)
    while comic == 2:
        print("getaddrinfo failed，重新获取漫画信息")
        comic = get_comic_info(num)
    if comic == -1:
        update_cur_num(num + 1)
        logging.debug(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 不下载非中文漫画，开始下载下一个: %s..." % str(num + 1))
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 不下载非中文漫画，开始下载下一个: %s..." % str(num + 1))
        return True
    if comic == -2:
        update_cur_num(num + 1)
        logging.debug(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 资源被跳转到新页面，直接开始下载下一个: %s..." % str(num + 1))
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 资源被跳转到新页面，直接开始下载下一个: %s..." % str(num + 1))
        return True
    if comic == -3:
        update_cur_num(num + 1)
        logging.debug(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 页面找不到了")
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 页面找不到了")
        return True
    try:
        if comic['type'] == "anime" and is_down_video:
            page_url = "https://hitomi.la/galleries/%s.html" % str(num)
            response = urllib.request.urlopen(page_url, timeout=20)
            html = response.read()
            html = html.decode('utf-8')
            videos_url = re.findall(rex_jwplayer, html)
            if len(videos_url) > 0:
                for video in videos_url:
                    video_url = "https:" + str(video[1]).replace("//g", "//streaming")
                    down_status = down_video(video_url, comic['name'], num)
                    if down_status == 3:
                        video_url = "https:" + str(video[1]).replace("//g", "//a")
                        down_status = down_video(video_url, comic['name'], num)
                    while down_status == 2:
                        print("下载中断，重新下载...")
                        down_status = down_video(video_url, comic['name'], num)
                update_cur_num(num + 1)
            return True
        if is_down_image:
            page_url = "https://hitomi.la/reader/%s.html" % num
            response = urllib.request.urlopen(page_url, timeout=20)
            html = response.read()
            if len(html) < 5000:
                logging.debug(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 页面错误，开始下载下一个...")
                print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 页面错误，开始下载下一个...")
                update_cur_num(num + 1)
                return True
            html = html.decode('utf-8')
            lists = re.findall(rex_pic, html)
            down_comic(lists, comic['name'], num)
            update_cur_num(num + 1)
            return True
        else:
            update_cur_num(num + 1)
            return True


    except Exception as e:
        logging.error(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + str(e))
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + str(e))
        logging.error(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 获取漫画地址列表出错")
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 获取漫画地址列表出错")


def get_comics(page):
    page_url = "https://hitomi.la/index-chinese-%s.html" % page
    try:
        response = urllib.request.urlopen(index_page, timeout=20)
        html = response.read()
        logging.error(html)
        html = html.decode('utf-8')
        comics = re.findall(rex_comic_info, html)
        if len(comics) > 0:
            for comic_html in comics:
                logging.error(comic_html)
    except Exception as e:
        logging.error(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + str(e))
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + str(e))
        logging.error(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " get last page failure")
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " get last page failure")
        return 1


def main():
    # last_page = get_last_page()
    # get_comics(1)
    # zips = zip_comic("make_20180805190837", './make_20180805190837')
    # send_email("Rei-Asuka_20180805141438", ["Rei-Asuka_20180805141438.zip"])
    # down_video()
    result = True
    while result:
        num = get_cur_num()
        if 0 < num <= target_page:
            result = get_pic_list(num)
        else:
            result = False
    # logging.error(last_page)


if __name__ == '__main__':
    main()
