import pandas as pd
import numpy as np
from strategys import TechnicalIndicator as ti


class AcceleratedUpPoints:
    """
    加速起涨点（量价、布林线、SAR）
    1.	量：之前两个交易日左右出现阶段地量后，近两天连续小阳线温和放量；
    2.	价：当前处于持续温和调整或震荡中；
    3.	布林线（BOLL）：上轨开口逐渐扩大，中轨线开始上翘；
    4.	SAR：由绿变红；
    """
    def __init__(self):
        self.strategy = pd.DataFrame(columns=["ts_code", "trade_date", "open",
                                              "high", "low", "close", "vol",
                                              "ma20", "strategy", 'from', 'reason'
                                              ])

    def initData(self, data, hot_date='20180101'):
        # 1、计算BOLL线
        df = ti.boll(data=data)
        df = df[df['trade_date'] >= hot_date]
        df = df.reset_index(drop=True)
        print(df.shape)
        print(df)
        # 2、计算SAR







        data['ma' + str(20)] = pd.Series.rolling(data['close'], window=20).mean()
        data['ma' + str(120)] = pd.Series.rolling(data['close'], window=120).mean()
        df = data.dropna(axis=0, subset=['ma20', 'ma120'], how='all')  # 去掉ma20和ma120均为nan
        df = df[df['trade_date'] >= hot_date]
        if df.ma120.isnull().any():
            df.ma120 = None
        df = df.reset_index(drop=True)
        return df


if __name__ == '__main__':
    from tools import GetDaily

    # 显示所有列
    pd.set_option('display.max_columns', None)
    # 显示所有行
    pd.set_option('display.max_rows', None)
    # 设置value的显示长度为100，默认为50
    pd.set_option('max_colwidth', 100)

    g = GetDaily()
    df = g.getDaily('002655.SZ')

    ac = AcceleratedUpPoints()
    df = ac.initData(df, hot_date='20190101')


