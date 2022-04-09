import time

from simhash import Simhash


def spammer_checker(msg):
    global ANTISPAMMER, SPAM2_VL
    group = msg.group.id
    user = msg.sender.id
    if group not in ANTISPAMMER:
        ANTISPAMMER[group] = {}
    if user not in ANTISPAMMER[group]:
        ANTISPAMMER[group][user] = [0, 0]
    if time.time() - ANTISPAMMER[group][user][0] <= 15:
        ANTISPAMMER[group][user][1] += 1
    else:
        ANTISPAMMER[group][user][0] = time.time()
        ANTISPAMMER[group][user][1] = 1
    if ANTISPAMMER[group][user][1] >= 8:
        ANTISPAMMER[group][user] = [0, 0]
        return True
    elif SPAM2_VL[msg.sender.id] >= 50 and ANTISPAMMER[group][user][1] >= 6:
        ANTISPAMMER[group][user] = [0, 0]
        SPAM2_VL[msg.sender.id] -= 5
        return True
    else:
        if msg.text.count("\n") >= 15:
            return True

    return False


def simhash_similarity(text1: str, text2: str) -> float:
    """
    :param text1: 文本1
    :param text2: 文本2
    :return: 返回两篇文章的相似度
    """
    aa_simhash = Simhash(text1)
    bb_simhash = Simhash(text2)
    max_hashbit = max(len(bin(aa_simhash.value)), (len(bin(bb_simhash.value))))
    # 汉明距离
    distince = aa_simhash.distance(bb_simhash)
    similar = 1 - distince / max_hashbit
    return similar


def strQ2B(ustring):
    rstring = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 12288:
            inside_code = 32
        elif 65281 <= inside_code <= 65374:
            inside_code -= 65248

        rstring += chr(inside_code)
    return rstring