#! coding: utf-8
import json
import traceback

count = 0
count_thousand = 0

output = open("output/{:d}.tsv".format(count_thousand), "w")
header = "个人空间网址\t昵称\t粉丝数\t最近视频投稿时间\t60天内投稿视频数" \
         "\t60天内投稿视频总播放\t60天内投稿视频总评论" \
         "\t60天内投稿视频最高播放\t60天内投稿视频最高评论" \
         "\t个人空间公告\t个人简介\tb站认证信息\tuid\tb站等级\t投稿分布"
column_number = 15

output.write(header + "\n")


uids = set()


with open("user_info.txt") as f:
    for line in f:
        try:
            items = line.strip("\n").split("\t")
            if len(items) != column_number:
                print(line)
                continue

            uid = items[12]
            if uid in uids:
                continue

            name = items[1]
            intro = items[10]
            veri = items[11]
            anno = items[9]

            try:
                name = str(json.loads(name)).replace("\t","\\t").replace("\r","\\r").replace("\n","\\n")
                intro = str(json.loads(intro)).replace("\t","\\t").replace("\r","\\r").replace("\n","\\n")
                veri = str(json.loads(veri)).replace("\t","\\t").replace("\r","\\r").replace("\n","\\n")
                anno = str(json.loads(anno)).replace("\t","\\t").replace("\r","\\r").replace("\n","\\n")
            except:
                pass
            
            items[1] = name
            items[9] = anno
            items[10] = intro
            items[11] = veri
            
            output.write("\t".join(items) + "\n")
            uids.add(uid)

            count += 1
            tmp_count_thousand = int(count / 1000)
            if count_thousand != tmp_count_thousand:
                count_thousand = tmp_count_thousand
                output.close()
                output = open("output/{:d}.tsv".format(count_thousand), "w")
                output.write(header + "\n")

        except:
            traceback.print_exc()
            print(line)
            print(count)
            raise
