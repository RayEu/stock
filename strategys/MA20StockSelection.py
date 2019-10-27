# coding: utf-8

import pandas as pd
import tools
from strategys import SimpleIndicatorJudgment as sij
from strategys import TechnicalIndicator as ti


class MA20StockSelection:

    def __init__(self):
        self.strategy = pd.DataFrame(columns=["ts_code", "trade_date", "open",
                                              "high", "low", "close", "vol",
                                              "ma20", "strategy", 'from', 'reason'
                                              ])

    def initData(self, data, hot_date='20180101'):
        data = ti.ma(data, 20)
        data = ti.ma(data, 120)
        df = data.dropna(axis=0, subset=['ma20', 'ma120'], how='all')  # 去掉ma20和ma120均为nan
        df = df[df['trade_date'] >= hot_date]
        if df.ma120.isnull().any():
            df.ma120 = None
        df = df.reset_index(drop=True)
        return df

    def __write2Strategy(self, record, strategy, reason):
        if type(record) is pd.DataFrame:
            series = pd.Series({"ts_code": record.ts_code.values[0],
                                "trade_date": record.trade_date.values[0],
                                'open': record.open.values[0],
                                'high': record.high.values[0],
                                'low': record.low.values[0],
                                'close': record.close.values[0],
                                'vol': record.vol.values[0],
                                'ma20': record.ma20.values[0],
                                'strategy': strategy,
                                'from': '20MAStockSelection',
                                'reason': reason
                                })
        else:
            series = pd.Series({"ts_code": record.ts_code,
                                "trade_date": record.trade_date,
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

    def __buy(self, data, row):
        '''
        1、收盘突破20日均线，首次突破，量能为前一日的2倍及以上
        2、收盘突破20日均线，阳包阴，量能为前一日的1.5倍及以上
        :param data:
        :param row:
        :return:
        '''
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
                and sij.judgeVOL(data, row.Index, 1.4) \
                and not sij.overMA20Bais(data, row.Index - 1, 0.04):
            for date, va in self.__getLastStrategy(row.trade_date):
                if va is None or va == 'sell' or va == 'monitor':
                    self.__write2Strategy(row, 'buy', '阳包阴 & 量能为前一日的1.5倍及以上')
                    break
                elif va == 'buy':
                    break

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
                self.__buy(data, row)
        else:
            # 20日均线向上
            if sij.MATrend(data, row.Index, 'ma20'):
                self.__buy(data, row)

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
                    self.__write2Strategy(data[data['trade_date'] == da[ind + 3]],
                                          'sell', str(row.trade_date)+'三天未突破')
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
            if row.close > row.open:  # 阳线
                if sij.overMA20Bais(data, row.Index, multiple=0.24):
                    # 量能为突破20的2倍及以上
                    for date, va in self.__getLastStrategy(row.trade_date):
                        if va is None:
                            break
                        if va == 'sell' or va == 'monitor':
                            continue
                        elif va == 'buy':
                            vol = self.strategy[self.strategy['trade_date'] == date]['vol'].values[0]
                            if row.vol >= vol * 1.8:
                                self.__write2Strategy(row, 'sell', '阳线远离20 & 量能为突破20的2倍及以上')
                            break
            else:  # 阴线
                if sij.overMA20Bais(data, row.Index, multiple=0.12):
                    if row.pct_chg < -4.0:  # 大阴线
                        if row.Index > 0:
                            pre = data.loc[row.Index - 1]
                            if row.vol > pre.vol:
                                self.__write2Strategy(row, 'sell', '阴线远离20 & 量能超过前日')
                    elif sij.overMA20Bais(data, row.Index, multiple=0.14):
                        # 量能为突破20的2倍及以上
                        for date, va in self.__getLastStrategy(row.trade_date):
                            if va is None:
                                break
                            if va == 'sell' or va == 'monitor':
                                continue
                            elif va == 'buy':
                                vol = self.strategy[self.strategy['trade_date'] == date]['vol'].values[0]
                                if row.vol >= vol * 1.8:
                                    self.__write2Strategy(row, 'sell', '阴线远离20 & 量能为突破20的2倍及以上')
                                break

    def judge(self, data, ma120=None):
        if ma120 is False:
            _ma = ma120
        if ma120 is None:
            _ma = False if data.ma120.values[0] is None else True
        if ma120 is True:
            _ma = ma120
        for row in data.itertuples(index=True):
            self.dealMonitor(data, row)
            self.buy(data, row, _ma)
            self.sell(data, row)
            #print(row.trade_date)
            #print(self.strategy[['trade_date', 'close', 'vol', 'strategy', 'reason']])
            #print('==================================================================')

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
                                'from': 'MA20StockSelection',
                                'reason': row.reason
                                })
            business = business.append(series, ignore_index=True)
        return business


if __name__ == '__main__':
    from tools import GetDaily
    # 显示所有列
    pd.set_option('display.max_columns', None)
    # 显示所有行
    pd.set_option('display.max_rows', None)
    # 设置value的显示长度为100，默认为50
    pd.set_option('max_colwidth', 100)

    g = GetDaily()
    df = g.getDaily('300525.SZ')
    print(df)
    ma = MA20StockSelection()
    df = ma.initData(df, hot_date='20190101')
    ma.judge(df, ma120=False)
    print(ma.strategy)
    ma.strategy.to_excel('../re.xlsx')
    ss = ma.simplifyStrategy()
    print(ss)
    tools.plot_K_line(df, '一根均线选股法', ss, '..')


