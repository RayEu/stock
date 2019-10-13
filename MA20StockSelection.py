# coding: utf-8

import tushare as ts
import pandas as pd
from basic import SimpleIndicatorJudgment as sij


class MA20StockSelection:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(MA20StockSelection, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, token=None):
        self.token = '90eb9db39113fb8cb7f9f4f6f62a743bb79b2ab2a73306725fd925f9' if token is None else token
        ts.set_token(self.token)
        self.pro = ts.pro_api(token)
        self.strategy = pd.DataFrame(columns=["ts_code", "trade_date", "open",
                                              "high", "low", "close", "vol",
                                              "ma20", "strategy", 'from', 'reason'
                                              ])

    def getDaily(self, ts_code, start_date='20180101', hot_date='20180101'):
        #       代码、     日期、         开、    高、    低、   收、     量能、 20日均线、        涨幅
        col = ['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'vol', 'ma20', 'ma120', 'pct_chg']
        df = None
        # 1、获取历史数据
        df1 = ts.pro_bar(ts_code=ts_code, adj='qfq',
                        start_date=start_date,
                        ma=[20, 120])
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
            now = tmp[0] * 3600 + tmp[1] * 60 + tmp[2]
            t1 = 9 * 3600 + 30 * 60
            t2 = 11 * 3600 + 30 * 60
            t3 = 13 * 3600
            t4 = 15 * 3600
            vol = 0
            if t1 < now < t2:
                vol = df2.volume * 4 * 3600 / (now - t1)
            elif t2 < now < t3:
                vol = df2.volume * 2
            elif t3 < now < t4:
                vol = df2.volume * 4 * 3600 / (now - t3 + t2 - t1)
            # 3.2、计算涨幅
            pct_chg = (df2.price - df2.pre_close) / df2.pre_close
            # 3.3、计算20日均线
            ma20 = (df1[0:20]['ma20'].sum() + df2.price) / 20
            # 3.4、计算120日均线
            ma120 = (df1[0:20]['ma20'].sum() + df2.price) / 20 if df1.shape[0] > 119 else None

            series = pd.Series({"ts_code": df1.ts_code,
                                "trade_date": d,
                                'open': df2.open,
                                'high': df2.high,
                                'low': df2.low,
                                'close': df2.price,
                                'vol': vol,
                                'ma20': ma20,
                                'ma120': ma120,
                                'pct_chg': pct_chg
                                })
            df = df1.append(series, ignore_index=True)
        df = df.sort_values(by="trade_date", ascending=True)  # 升序
        df = df.dropna(axis=0, subset=['ma20', 'ma120'], how='all')  # 去掉ma20和ma120均为nan
        df = df[df['trade_date'] >= hot_date]
        if df.ma120.isnull().any():
            df.ma120 = None
        df = df.reset_index(drop=True)
        return df

    def __write2Strategy(self, record, strategy, reason, trade_date=None):
        if trade_date is None:
            da = record.trade_date
        else:
            da = trade_date
        series = pd.Series({"ts_code": record.ts_code,
                            "trade_date": da,
                            'open': record.open,
                            'high': record.high,
                            'low': record.low,
                            'close': record.close,
                            'vol': record.vol,
                            'ma20': record.ma20,
                            'strategy': strategy,
                            'from': '20MAStockSelection',
                            'reason': reason
                            })
        self.strategy = self.strategy.append(series, ignore_index=True)
        # self.strategy = self.strategy.drop_duplicates(subset=['trade_date', 'strategy'], keep='first')
        self.strategy = self.strategy.drop_duplicates(subset=None, keep='first')
        # ascending=False 从大到小
        self.strategy.sort_values(by='trade_date', ascending=True, inplace=True)

    def __getLastStrategy(self, cur_index):
        tmp = self.strategy['trade_date'].tolist()
        if cur_index in tmp:
            yield cur_index, None
        tmp.append(str(cur_index))
        tmp.sort()
        ind = tmp.index(cur_index)
        if ind == 0:
            yield tmp[0], None
        ran = [i for i in tmp[0:ind]]
        ran.sort(reverse=True)  # 降序
        for date in ran:
            va = self.strategy[self.strategy['trade_date'] == date].strategy.values[0]
            yield date, va

    def buy(self, data, row, ma120=False):
        '''
        三种买入方式：
        前提：20日均线与半年线向上；20日均线高于半年线；
        1、收盘突破20日均线，首次突破，量能为前一日的2倍及以上
        2、收盘突破20日均线，阳包阴，量能为前一日的1.5倍及以上
        :param data:
        :param row:
        :return:
        '''
        if ma120:
            # 20日均线与半年线向上；20日均线高于半年线，
            if sij.MATrend(data, row.Index, 'ma20') \
                    and sij.MATrend(data, row.Index, 'ma120') \
                    and row.ma20 > row.ma120:
                # 1、收盘突破20日均线，首次突破，量能为前一日的2倍及以上
                if row.close > row.ma20 \
                        and sij.firstBreak(data, row.Index) \
                        and sij.judgeVOL(data, row.Index, 1.8):
                    for date, va in self.__getLastStrategy(row.trade_date):
                        if va is None or va == 'sell' or va == 'monitor':
                            self.__write2Strategy(row, 'buy', '首次突破 & 量能为前一日的2倍及以上')
                            break
                        elif va == 'buy':
                            break
                # 2、收盘突破20日均线，阳包阴，量能为前一日的1.4倍及以上
                if row.close > row.ma20 \
                        and sij.yangOverYin(data, row.Index) \
                        and sij.judgeVOL(data, row.Index, 1.4):
                    for date, va in self.__getLastStrategy(row.trade_date):
                        if va is None or va == 'sell' or va == 'monitor':
                            self.__write2Strategy(row, 'buy', '阳包阴 & 量能为前一日的1.5倍及以上')
                            break
                        elif va == 'buy':
                            break
        else:
            # 20日均线向上
            if sij.MATrend(data, row.Index, 'ma20'):
                # 1、收盘突破20日均线，首次突破，量能为前一日的2倍及以上
                if row.close > row.ma20 \
                        and sij.firstBreak(data, row.Index) \
                        and sij.judgeVOL(data, row.Index, 1.8):
                    for date, va in self.__getLastStrategy(row.trade_date):
                        if va is None or va == 'sell' or va == 'monitor':
                            self.__write2Strategy(row, 'buy', '首次突破 & 量能为前一日的2倍及以上')
                            break
                        elif va == 'buy':
                            break
                # 2、收盘突破20日均线，阳包阴，量能为前一日的1.4倍及以上
                if row.close > row.ma20 \
                        and sij.yangOverYin(data, row.Index) \
                        and sij.judgeVOL(data, row.Index, 1.4):
                    for date, va in self.__getLastStrategy(row.trade_date):
                        if va is None or va == 'sell' or va == 'monitor':
                            self.__write2Strategy(row, 'buy', '阳包阴 & 量能为前一日的1.5倍及以上')
                            break
                        elif va == 'buy':
                            break

    def dealMonitor(self, data, row):
        '''
        处理monitor信息
        :param data:
        :param trade_date:
        :return:
        '''
        trade_date = row.trade_date
        # 1、找到所有monitor的记录
        tmp = self.strategy[self.strategy['strategy'] == 'monitor']
        if tmp.empty:
            return
        # 2、获取交易时间
        da = data[['trade_date']].values.tolist()
        da = [d[0] for d in da]
        for row in tmp.itertuples(index=True):
            ind = da.index(row.trade_date)  # 当日
            try:
                for i in [1, 2, 3]:
                    if da[ind + i] > trade_date:
                        break
                    day = data[data['trade_date'] == da[ind + i]]
                    if day.close.values > day.ma20.values:
                        # 突破，删除monitor记录
                        self.strategy = self.strategy[~(self.strategy['trade_date'].isin([row.trade_date])
                                                        & self.strategy['strategy'].str.contains('monitor'))]
                        break
                else:  # 3天未突破
                    self.strategy = self.strategy[~(self.strategy['trade_date'].isin([row.trade_date])
                                                    & self.strategy['strategy'].str.contains('monitor'))]
                    self.__write2Strategy(row, 'sell', str(row.trade_date)+'三天未突破', trade_date=da[ind + 3])
                continue
            except Exception as e:
                print(e)

    def sell(self, data, row):
        '''
        三种卖出信号
        1、跌破20 & 大量放量
        2、跌破20 & 非大量 & 三个交易日无法收复
        3、远离20 & 量能为突破20的2倍及以上
        :param data:
        :param row:
        :return:
        '''
        # 跌破20
        if row.close < row.ma20:
            # 1、大量放量
            if sij.judgeVOL(data, row.Index, 2.5):
                self.__write2Strategy(row, 'sell', '跌破20 & 大量放量')
            else:
                # 2、非大量 & 三个交易日无法收复
                for date, va in self.__getLastStrategy(row.trade_date):
                    if va is None or va == 'monitor':  # 若之前是monitor，则不再进行监控
                        break
                    if va == 'sell':  # 若之前是sell，则前溯，因为你不一定卖
                        continue
                    elif va == 'buy':  # 若之前有buy，则监控
                        self.__write2Strategy(row, 'monitor', '跌破20 & 非大量')
                        break
        # 3、远离20
        else:
            write_flag = False
            if row.close > row.open:  # 阳线
                write_flag = True if sij.overMA20Bais(data, row.Index, multiple=0.25) else False
            else:  # 阴线
                write_flag = True if sij.overMA20Bais(data, row.Index, multiple=0.14) else False
            if write_flag:
                # 量能为突破20的2倍及以上
                for date, va in self.__getLastStrategy(row.trade_date):
                    if va is None:
                        break
                    if va == 'sell' or va == 'monitor':
                        continue
                    elif va == 'buy':
                        vol = self.strategy[self.strategy['trade_date'] == date]['vol'].values[0]
                        if row.vol >= vol * 1.8:
                            self.__write2Strategy(row, 'sell', '远离20 & 量能为突破20的2倍及以上')
                        break

    def judge(self, data, ma120=None):
        if ma120 is False:
            ma = ma120
        if ma120 is None:
            ma = False if data.ma120.values[0] is None else True
        if ma120 is True:
            ma = ma120
        for row in data.itertuples(index=True):
            self.dealMonitor(data, row)
            self.buy(data, row, ma)
            self.sell(data, row)
            print(row.trade_date)
            print(self.strategy[['trade_date', 'close', 'vol', 'strategy', 'reason']])
            print('==================================================================')

    def simplifyStrategy(self):
        pre = None
        tmp = []
        for row in self.strategy.itertuples():
            if row.strategy == 'buy':
                tmp.append(row)
                pre = None
            if row.strategy == 'monitor':
                tmp.append(row)
                pre = None
            if row.strategy == 'sell':
                if pre is None:
                    tmp.append(row)
                    pre = row
                else:
                    if '三天未突破' in pre.reason or '跌破20 & 大量放量' in pre.reason:
                        pre = row
                    else:
                        tmp.append(row)
                        pre = row
        business = pd.DataFrame(columns=["ts_code", "trade_date", 'open', 'high', 'low',
                                         'close', 'vol', 'ma20', 'strategy', 'from', 'reason'])
        for row in tmp:
            series = pd.Series({"ts_code": row.ts_code,
                                "trade_date": row.trade_date,
                                'open': row.open,
                                'high': row.high,
                                'low': row.low,
                                'close': row.close,
                                'vol': row.vol,
                                'ma20': row.ma20,
                                'strategy': row.strategy,
                                'from': '20MAStockSelection',
                                'reason': row.reason
                                })
            business = business.append(series, ignore_index=True)
        return business


if __name__ == '__main__':
    # 显示所有列
    pd.set_option('display.max_columns', None)
    # 显示所有行
    pd.set_option('display.max_rows', None)
    # 设置value的显示长度为100，默认为50
    pd.set_option('max_colwidth', 100)
    ma = MA20StockSelection()
    df = ma.getDaily('603121.SH', hot_date='20190101')
    print(df)
    ma.judge(df, ma120=False)
    print(ma.strategy)
    ma.strategy.to_excel('./re.xlsx')
    df = ma.simplifyStrategy()
    print(df)


