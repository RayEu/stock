# coding: utf-8

import pandas as pd


class KShape:
    def __init__(self):
        self.strategy = pd.DataFrame(columns=["ts_code", "trade_date", "open",
                                              "high", "low", "close", "strategy",
                                              'from', 'reason'])

    def pai_xu(self, data):
        tmp = [data[0], data[1], data[2], data[3]]
        tmp.sort(reverse=True)
        return tmp[0], tmp[1], tmp[2], tmp[3]

    def initData(self, data, hot_date='20190101'):
        df = data[["ts_code", "trade_date", "open", "high", "low", "close"]]
        df = df[df['trade_date'] >= hot_date]
        df = df.reset_index(drop=True)
        return df

    def __check_low(self, data, cur_index):
        # 1、有近三天的数据
        if cur_index <= 1:
            return False
        cur = data.loc[cur_index]
        pre = data.loc[cur_index - 1]
        ppre = data.loc[cur_index - 2]
        # 2、近三天最低
        if cur.low < pre.low and cur.low < ppre.low:
            pass
        else:
            return False
        # 3、数据排序
        first, second, third, fourth = self.pai_xu([cur.open, cur.high, cur.low, cur.close])
        return first, second, third, fourth

    def hammer_low(self, data, cur_index):
        """
        低位锤
        :param data:
        :param cur_index:
        :return:
        """
        first, second, third, fourth = self.__check_low(data, cur_index)
        if third - fourth >= (second - third) * 2 \
                and first - second <= (second - third) * 0.5:
            return True
        else:
            return False

    def hammer_low_inverted(self, data, cur_index):
        """
        倒低位锤
        :param data:
        :param cur_index:
        :return:
        """
        first, second, third, fourth = self.__check_low(data, cur_index)
        if first - second >= (second - third) * 2 \
                and third - fourth <= (second - third) * 0.5:
            return True
        else:
            return False

    def cross_star_low(self, data, cur_index):
        """
        低位十字星
        :param data:
        :param cur_index:
        :return:
        """
        first, second, third, fourth = self.__check_low(data, cur_index)
        if third - fourth >= (second - third) * 2  \
                and first - second >= (second - third) * 2 \
                and (second - third) / (first - fourth) <= 0.05:
            return True
        else:
            return False

    def propeller_low(self, data, cur_index):
        """
        低位螺旋桨
        :param data:
        :param cur_index:
        :return:
        """
        first, second, third, fourth = self.__check_low(data, cur_index)
        if first - second >= (second - third) * 2 \
                and third - fourth >= (second - third) * 2 \
                and 1/6 <= (second - third) / (first - fourth) <= 0.3:
            return True
        else:
            return False



if __name__ == '__main__':
    from tools import GetDaily
    # 显示所有列
    pd.set_option('display.max_columns', None)
    # 显示所有行
    pd.set_option('display.max_rows', None)
    # 设置value的显示长度为100，默认为50
    pd.set_option('max_colwidth', 200)

    # 第一步：获取数据
    g = GetDaily()
    df = g.getDaily('300525.SZ')

    e = KShape()
    df = e.initData(df, hot_date='20190101')
    for row in df.itertuples():
        zt = e.hammer_low(df, row.Index)
        print(row.trade_date, zt)

