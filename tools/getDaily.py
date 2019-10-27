# coding: utf-8

import tushare as ts
import pandas as pd


class GetDaily:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GetDaily, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, token=None):
        self.token = '90eb9db39113fb8cb7f9f4f6f62a743bb79b2ab2a73306725fd925f9' if token is None else token
        ts.set_token(self.token)
        self.pro = ts.pro_api(token)

    def getDaily(self, ts_code, start_date='20180101'):
        #       代码、     日期、         开、    高、    低、   收、     量能、 涨幅
        col = ['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'vol', 'pct_chg']
        df = None
        # 1、获取历史数据
        df1 = ts.pro_bar(ts_code=ts_code, adj='qfq',
                         start_date=start_date)
        df1 = df1[col]
        # 2、获取当日实时数据
        df2 = ts.get_realtime_quotes(ts_code.split('.')[0])
        df2 = df2[['code', 'date', 'open', 'high', 'low', 'price', 'volume', 'pre_close', 'time']]

        # 3、估值当日最终数据
        tmp = df2.date.values[0].split('-')
        d = tmp[0] + tmp[1] + tmp[2]
        if d in df1.trade_date.tolist():
            print(d, ' date in history date')
            df = df1
        else:
            # 3.1、计算量能
            tmp = df2.time.values[0].split(':')
            now = int(tmp[0]) * 3600 + int(tmp[1]) * 60 + int(tmp[2])
            t1 = 9 * 3600 + 30 * 60
            t2 = 11 * 3600 + 30 * 60
            t3 = 13 * 3600
            t4 = 15 * 3600
            ss = df2.volume.values[0]
            vol = float(ss) if '.' in ss else float(ss[:-2]) + 0.01 * float(ss[-2:])
            if t1 < now < t2:
                vol = vol * 4 * 3600 / (now - t1)
            elif t2 < now < t3:
                vol = vol * 2
            elif t3 < now < t4:
                vol = vol * 4 * 3600 / (now - t3 + t2 - t1)
            # 3.2、计算涨幅
            price = float(df2.price.values[0])
            pre_close = float(df2.pre_close.values[0])
            pct_chg = (price - pre_close) / pre_close

            series = pd.Series({"ts_code": df1.ts_code.values[0],
                                "trade_date": d,
                                'open': float('%.2f' % df2.open.values[0]),
                                'high': float('%.2f' % df2.high.values[0]),
                                'low': float('%.2f' % df2.low.values[0]),
                                'close': float('%.2f' % price),
                                'vol': float('%.2f' % vol),
                                'pct_chg': float('%.2f' % pct_chg)
                                })
            df = df1.append(series, ignore_index=True)
        df = df.sort_values(by="trade_date", ascending=True)  # 升序
        return df


if __name__ == '__main__':
    # 显示所有列
    pd.set_option('display.max_columns', None)
    # 显示所有行
    pd.set_option('display.max_rows', None)
    # 设置value的显示长度为100，默认为50
    pd.set_option('max_colwidth', 100)

    # 第一步：获取数据
    g = GetDaily()
    df = g.getDaily('002850.SZ')
    print(df)
    df['ma_' + str(10)] = pd.Series.rolling(df['close'], window=10).mean()
    print(df)


