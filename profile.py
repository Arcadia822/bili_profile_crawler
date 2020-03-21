#!coding:utf-8
import datetime
import json
import time
import traceback
import urllib.error
import urllib.request


CARD_API = "https://api.bilibili.com/x/web-interface/card?mid={:d}&article=true"  # basicinfo
FOLLOWING_API = "https://api.bilibili.com/x/relation/followings?vmid={:d}&pn={:d}"  # follower
ANNOUNCEMENT_API = "https://api.bilibili.com/x/space/notice?mid={:d}"  #space announcement
RECENT_VIDEO_API = "https://api.bilibili.com/x/space/arc/search?mid={:d}&pn={:d}&ps=25&order=ts"  # video
SPACE_URL = "https://space.bilibili.com/{:d}" # space


class BilibiliProfile(object):

    def __init__(self, uid):
        self.uid = uid
        self.name = ""
        self.level = 0
        self.introduction = ""
        self.verified_reason = ""
        self.announcement = ""
        self.role = -1
        self.fans = 0
        self.following_uids = []
        self.video_summary = {}
        self.last_update_ts = 0
        self.max_play_count = 0
        self.max_comment_count = 0
        self.sum_play_count = 0
        self.sum_comment_count = 0
        self.sum_video_count = 0

    def crawl(self):
        self._crawl_base_info()
        self._crawl_recent_video(second_limit=60*86400)
        self._crawl_following()

    def _crawl_base_info(self):
        self._crawl_card()
        self._crawl_announcement()

    def _crawl_card(self):
        card_text = get_card_by_uid(self.uid)
        card_info = json.loads(card_text)

        code = card_info.get("code", -1)

        if code != 0:
            print("FAIL FETCH CARD INFO FOR UID: {:d} RESPONSE: {:s}".format(self.uid, card_text.decode("utf-8")))
            return

        card_obj = card_info["data"]["card"]

        self.name = card_obj["name"]
        self.introduction = card_obj["sign"]
        self.fans = card_obj["fans"]
        self.level = card_obj["level_info"]["current_level"]

        if "Official" in card_obj:
            official_obj = card_obj["Official"]
            if "title" in official_obj:
                self.verified_reason = official_obj["title"]
            if "role" in official_obj:
                self.role = official_obj["role"]
        
    def _crawl_announcement(self):
        announcement_text = get_announcement_by_uid(self.uid)
        announcement_info = json.loads(announcement_text)

        code = announcement_info.get("code", -1)
        if code != 0:
            print("FAIL FETCH ANNOUNCEMENT INFO FOR UID: {:d} RESPONSE: {:s}".format(self.uid, announcement_text.decode("utf-8")))
            return
        
        self.announcement = announcement_info["data"]

    def _crawl_following(self, page=1):
        if page>5:
            return
        following_text = get_following_by_uid(self.uid, page)
        following_info = json.loads(following_text)

        code = following_info.get("code", -1)

        if code != 0:
            print("FAIL FETCH FOLLOWING INFO FOR UID: {:d} PAGE: {:d} RESPONSE: {:s}".format(self.uid, page, following_text.decode("utf-8")))
            return

        following_list = following_info["data"]["list"]

        for item in following_list:
            self.following_uids.append(item["mid"])

        if following_list:
            self._crawl_following(page+1)

    def _crawl_recent_video(self, page=1, second_limit=0):
        """
        获取发布视频统计
        获取最近一个发布的视频的信息
        获取最近second_limit秒发布的视频的聚合统计
        """
        now = int(time.time())

        recent_video_text = get_recent_video_by_uid(self.uid, page)
        recent_video_info = json.loads(recent_video_text)

        code = recent_video_info.get("code", -1)

        if code != 0:
            print("FAIL FETCH FOLLOWING INFO FOR UID: {:d} PAGE: {:d} RESPONSE: {:s}".format(self.uid, page, following_text.decode("utf-8")))
            return

        video_list = recent_video_info.get("data").get("list").get("vlist")

        if not video_list:
            return

        if page == 1:
            video_summary_raw = recent_video_info.get("data").get("list").get("tlist")
            self.video_summary = dict([[value["name"], value["count"]] for value in video_summary_raw.values()])
                
            most_recent_video = video_list[0]
            self.last_update_ts = most_recent_video["created"]

        for video in video_list:
            create_ts = video["created"]

            if now - create_ts > second_limit:
                return

            play_count = video["play"]
            comment_count = video["comment"]

            if play_count > self.max_play_count:
                self.max_play_count = play_count

            if comment_count > self.max_comment_count:
                self.max_comment_count = comment_count

            self.sum_play_count += play_count
            self.sum_comment_count += comment_count

            self.sum_video_count += 1
        
        self._crawl_recent_video(page + 1, second_limit)

    def get_profile(self):
        profile = {
            "uid": self.uid,
            "name": self.name,
            "level": self.level,
            "fans": self.fans,
            "role": self.role,
            "introduction": self.introduction,
            "verified_reason": self.verified_reason,
            "announcement": self.announcement
        }
        return profile

    def format_profile(self):
        text = "\t".join((
            SPACE_URL.format(self.uid),
            json.dumps(self.name),
            str(self.fans),
            datetime.datetime.fromtimestamp(self.last_update_ts).strftime("%Y-%m-%d"),
            str(self.sum_video_count),
            str(self.sum_play_count),
            str(self.sum_comment_count),
            str(self.max_play_count),
            str(self.max_comment_count),
            json.dumps(self.announcement),
            json.dumps(self.introduction),
            json.dumps(self.verified_reason),
            str(self.uid),
            str(self.level),
            ",".join([k + "@" + str(v) for k, v in sorted(self.video_summary.items(), key=lambda x:x[1], reverse=True)])
        )) + "\n"
        return text

    def following(self):
        return self.following_uids




def get(url, timeout_wait = 0):
   
    request = urllib.request.Request(url=url)
    request.add_header("User_Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36")
    try:
        result = urllib.request.urlopen(request).read()
    except urllib.error.URLError as e:
        if timeout_wait >= 3:
            raise
        traceback.print_exc()
        print("Timeout.. Sleep 1min.")
        time.sleep(60)
        return get(url, timeout_wait+1)
    return result


def get_card_by_uid(uid):
    url = CARD_API.format(uid)
    result = get(url)
    return result


def get_following_by_uid(uid, page=0):
    url = FOLLOWING_API.format(uid, page)
    result = get(url)
    return result


def get_announcement_by_uid(uid):
    url = ANNOUNCEMENT_API.format(uid)
    result = get(url)
    return result


def get_recent_video_by_uid(uid, page=0):
    url = RECENT_VIDEO_API.format(uid, page)
    result = get(url)
    return result


if __name__ == "__main__":
    scboy = BilibiliProfile(9717562)
    scboy.crawl()

    scboy_info = scboy.get_profile()
    for k,v in scboy_info.items():
        print(k + "\t" + str(v))

    scboy_following = scboy.following()
    print(scboy_following)
