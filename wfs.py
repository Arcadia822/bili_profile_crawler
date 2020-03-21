#! coding: utf-8
import os
import pdb
import time
import traceback

from profile import BilibiliProfile



crawled_uid_set = set()

crawl_target_uids = []

crawl_count = 0
max_crawl_count = 100

output_name = "user_info.txt"
log_name = "crawl.log"


if not os.path.exists(output_name):
    os.system("touch {:s}".format(output_name))


with open(output_name) as f:
    for line in f:
        uid = int(line.strip("\n").split("\t")[-3])
        crawled_uid_set.add(int(uid))


output_file = open(output_name, "a")


if not os.path.exists(log_name):
    os.system("touch {:s}".format(log_name))


with open(log_name) as f:
    for line in f:
        uid = int(line.strip())
        if uid not in crawled_uid_set:
            crawl_target_uids.append(uid)


log_file = open(log_name, "a")


seed_crawl_target = [
    12113,
    116683,
    2374194,
    423442,
    282994
]


if not crawl_target_uids:
    crawl_target_uids.extend(seed_crawl_target)


while crawl_target_uids and crawl_count < max_crawl_count:
    target_uid = crawl_target_uids[0]

    profile = BilibiliProfile(target_uid)
    profile.crawl()



    if profile.level >= 4:
        if target_uid not in crawled_uid_set:
            print("Crawl[{:d}]: {:d}_{:s}".format(crawl_count, profile.uid, profile.name))
            output_file.write(profile.format_profile())
            crawled_uid_set.add(target_uid)
            crawl_count += 1
    
    del crawl_target_uids[0]
    
    for uid in profile.following_uids:
        if uid not in crawled_uid_set:
            crawl_target_uids.append(uid)
            log_file.write(str(uid) + "\n")

    time.sleep(1)
