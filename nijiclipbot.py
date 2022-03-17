from datetime import timedelta, datetime, timezone
import time
import json
import urllib.request
import urllib.parse

import tweepy

from tag_dict import tag_dict
import config


start_time = time.perf_counter()


def generate_tweet():
    nico_res = get_clip_info()
    twit_content_list = format_info(nico_res)

    if twit_content_list == []:
        return
    else:
        count = 0
        while count < len(twit_content_list):
            make_api().update_status(status=twit_content_list[count])
            print(
                twit_content_list[count] + "\n"
                + "ツイート完了"
            )
            count = count + 1
            time.sleep(300)
        print("完了" + "\n" + "ツイート数:" + str(count))


def get_clip_info():  # ネスト多いし長いから関数分けたい
    t_delta = timedelta(hours=9)
    JST = timezone(t_delta, 'JST')
    tdy = datetime.now(JST).replace(hour=0, minute=0, second=0, microsecond=0)
    ytd = tdy - timedelta(days=1)

    api_req = urllib.request.Request(
        "https://api.search.nicovideo.jp/api/v2/snapshot/version"
    )
    last_modified = datetime.fromisoformat(
        json.loads(urllib.request.urlopen(api_req).read())["last_modified"]
    )
    if last_modified >= tdy:
        nico_endpoint = "https://api.search.nicovideo.jp/api/v2/snapshot/video/contents/search"
        nico_res = []
        nico_tag_dict = list(tag_dict.keys())
        length = len(nico_tag_dict)
        n = 0
        s = 15
        for i in nico_tag_dict:
            split_tag_dict = nico_tag_dict[n:n + s:1]
            search_q = " OR ".join(split_tag_dict) + " -MMD -にじさんじMMD"
            n += s
            if n >= length:
                break
            nico_params = {
                "q": search_q,
                "targets": "tagsExact",
                "fields": "title,startTime,tags,contentId,userId",
                "filters[startTime][gte]": ytd.isoformat(),
                "filters[startTime][lt]": tdy.isoformat(),
                "_sort": "+startTime",
                "_context": "2434os_clipFilter",
                "_limit": 100}
            nico_req = urllib.request.Request("{}?{}".format(
                nico_endpoint, urllib.parse.urlencode(nico_params)))
            split_nico_res = json.loads(
                urllib.request.urlopen(nico_req).read())
            if split_nico_res["meta"]["status"] == 200:
                if split_nico_res["data"] != []:
                    nico_res.append(split_nico_res["data"][0])
                    nico_res = list(map(json.loads, set(map(json.dumps, nico_res))))
                    nico_res = sorted(nico_res, key=lambda x: x["startTime"])
            else:
                print("エラー:10分後に再度アクセスします")
                time.sleep(600)
                med_time = time.perf_counter()
                elapsed_time = med_time - start_time
                if elapsed_time <= 7200:
                    get_clip_info()
                else:
                    print("タイムアウト:終了します")
                    return
    else:
        print("切り替え日時:" + last_modified.strftime("%Y/%m/%d %H:%M"))
        nico_res = []
    return nico_res


def format_info(nico_res):
    twit_content_list = []
    ng_id_list = [9264517, 92490088, 91829394]

    if nico_res == []:
        print("新着動画なし")
    else:
        for info in nico_res:
            if info["userId"] not in ng_id_list:
                post_date = datetime.fromisoformat(
                    info["startTime"]).strftime("%Y/%m/%d %H:%M")
                twit_tag = make_hashtag(info)
                twit_content = "新着動画" + "\n"\
                    + info["title"] + "\n"\
                    + post_date + "投稿" + "\n"\
                    + twit_tag + "\n"\
                    + "https://nico.ms/" + info["contentId"]
                twit_content_list.append(twit_content)
    return twit_content_list


def make_hashtag(info):
    tag = info["tags"].replace("（", "(").replace("）", ")")
    nico_tag_list = tag.casefold().split()
    tag_list = []
    hashtag_list = []
    twit_tag = ""

    for nico_tag in nico_tag_list:
        if nico_tag in tag_dict:
            tag_list.append(tag_dict[nico_tag])
    for tag in tag_list:
        if tag not in hashtag_list:
            hashtag_list.append(tag)
    for tag in hashtag_list:
        twit_tag += "#" + tag + " "
    twit_tag = twit_tag[:-1]
    return twit_tag


def make_api():
    CK = config.API_KEY
    CS = config.API_KEY_SECRET
    AT = config.ACCESS_TOKEN
    AS = config.ACCESS_TOKEN_SECRET

    auth = tweepy.OAuthHandler(CK, CS)
    auth.set_access_token(AT, AS)
    return tweepy.API(auth)


if __name__ == "__main__":
    generate_tweet()
