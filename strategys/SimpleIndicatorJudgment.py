# coding:utf-8


def yangOverYin(data, cur_index, multiple=4/5):
    if cur_index == 0:
        return False
    cur = data.loc[cur_index]
    pre = data.loc[cur_index - 1]
    # 今天阳线
    if cur.close > cur.open:
        cur_high = cur.close
    else:
        return False
    # 前一天阴线
    if pre.close < pre.open:
        pre_low = pre.close
    else:
        return False
    # 严格来说：第二根K线的实体将第一根K线包住，这里仅包住4/5即可
    if cur_high > abs(pre.close - pre.open) * multiple + pre_low and pre.open > cur.open:
        return True
    else:
        return False


def judgeVOL(data, cur_index, multiple):
    if cur_index == 0:
        return False
    cur = data.loc[cur_index]
    pre = data.loc[cur_index - 1]
    if cur.vol >= pre.vol * multiple:
        return True
    else:
        return False


def overMA20Bais(data, cur_index, multiple=0.2):
    cur = data.loc[cur_index]
    bais = abs(cur.close - cur.ma20)/cur.ma20
    if bais > multiple:
        return True
    else:
        return False


def firstBreak(data, cur_index):
    if cur_index == 0:
        return True
    cur = data.loc[cur_index]
    pre = data.loc[cur_index - 1]
    if cur.close > cur.ma20 and pre.close < pre.ma20:
        return True
    else:
        pass
    if cur.close > cur.ma20 \
            and overMA20Bais(data, cur_index, 0.08) \
            and not overMA20Bais(data, cur_index-1, 0.04):
        return True
    else:
        return False


def MATrend(data, cur_index, ma, thread=0.03):
    if cur_index == 0:
        return False
    cur = data.loc[cur_index]
    pre = data.loc[cur_index - 1]
    if cur[ma] >= pre[ma] - thread:
        return True
    else:
        return False

