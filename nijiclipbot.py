from datetime import timedelta, datetime, timezone
import time
import json
import urllib.request
import urllib.parse

import tweepy

import config


start_time = time.perf_counter()


def main():
    nico_res = get_clip_info()
    twit_content_list = format_info(nico_res)
    if twit_content_list == []:
        return
    else:
        count = 0
        for twit_content in twit_content_list:
            make_api().update_status(twit_content)
            # APIがエラー吐いたときの処理を実装する．Twitter,ニコニコのエラー処理は統合してもいいかも？
            print(twit_content + "\n" + "ツイート完了")
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
        nico_params = {
            "q": "nijisanji_kr OR nijisanji_id OR nijisanji_en OR nijisanji_in OR virtuareal OR にじさんじKR OR にじさんじEN OR にじさんじID OR にじさんじIN",
            "targets": "tagsExact",
            "fields": "title,startTime,contentId",
            "filters[startTime][gte]": ytd.isoformat(),
            "filters[startTime][lt]": tdy.isoformat(),
            "_sort": "+startTime",
            "_context": "2434os_clipFilter",
            "_limit": 100
        }
        nico_req = urllib.request.Request(
            "{}?{}".format(nico_endpoint, urllib.parse.urlencode(nico_params))
        )
        nico_res = json.loads(urllib.request.urlopen(nico_req).read())
        if nico_res["meta"]["status"] == 200:
            nico_res = nico_res["data"]
        else:
            print("エラー:10分後に再度アクセスします")
            time.sleep(600)
            med_time = time.perf_counter()
            elapsed_time = med_time - start_time
            if elapsed_time <= 7200:
                get_clip_info()
            else:
                print("タイムアウト:終了します")
                nico_res = []
                return
    else:
        print("切り替え日時:" + last_modified.strftime("%Y/%m/%d %H:%M"))
        nico_res = []
    return nico_res


def format_info(nico_res):
    twit_content_list = []
    if nico_res == []:
        print("新着動画なし")
    else:
        for info in nico_res:
            post_date = datetime.fromisoformat(
                info["startTime"]).strftime("%Y/%m/%d %H:%M")
            twit_content = info["title"] + "\n"\
                + post_date + "投稿" + "\n"\
                + "https://nico.ms/" + info["contentId"]
            twit_content_list.append(twit_content)
    return twit_content_list


def make_api():
    CK = config.API_KEY
    CS = config.API_KEY_SECRET
    AT = config.ACCESS_TOKEN
    AS = config.ACCSESS_TOKEN_SECRET

    auth = tweepy.OAuthHandler(CK, CS)
    auth.set_access_token(AT, AS)
    return tweepy.API(auth)


if __name__ == "__main__":
    main()
