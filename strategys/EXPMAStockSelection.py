# coding: utf-8

import pandas as pd
import tools


class EXPMAStockSelection:
    """
    不靠谱
    对于个股的抄底和逃顶提供了较好的点位，是投资者采用中短线决策的好帮手。
    EXPMA指标，我们通过设置EXPMA1，默认参数为10天（白线）和EXPMA2，默认参数为60天（黄线），
    在实战中优化成【强弱线战法】：
    	当白线由下往上穿越黄线时，股价随后通常会不断上升，那么这两根线形成金叉之日便是买入良机。
        最为稳健的买点就是在金叉后以一根中阳线突破前期的平台。
    	当一只个股的股价远离白线后，该股的股价随后很快便会回落，然后再沿着白线上移，可见白线是一大支撑点。
    	当白线由上往下击穿黄线时，股价往往已经发生转势，日后将会以下跌为主，则这两根线的交叉之日便是卖出时机。
    """
    def __init__(self):
        self.strategy = pd.DataFrame(columns=["ts_code", "trade_date", "open",
                                              "high", "low", "close", "expma10",
                                              "expma60", "strategy", 'from', 'reason'
                                              ])

    def initData(self, data, hot_date='20190101'):
        data['EXPMA_10'] = 0
        data['EXPMA_60'] = 0
        data['EXPMA_10'] = pd.DataFrame.ewm(data['close'], span=10).mean()
        data['EXPMA_10'] = data['EXPMA_10'].round(decimals=2)
        data['EXPMA_60'] = pd.DataFrame.ewm(data['close'], span=60).mean()
        data['EXPMA_60'] = data['EXPMA_60'].round(decimals=2)
        df = data[data['trade_date'] >= hot_date]
        df = df.dropna(axis=0, subset=['EXPMA_10', 'EXPMA_60'], how='any')  # 去掉ma20和ma120均为nan
        df = df.reset_index(drop=True)
        return df

    def __write2Strategy(self, record, strategy, reason):
        series = pd.Series({"ts_code": record.ts_code,
                            "trade_date": record.trade_date,
                            'open': record.open,
                            'high': record.high,
                            'low': record.low,
                            'close': record.close,
                            'expma10': record.EXPMA_10,
                            'expma60': record.EXPMA_60,
                            'strategy': strategy,
                            'from': 'EXPMAStockSelection',
                            'reason': reason
                            })
        self.strategy = self.strategy.append(series, ignore_index=True)
        self.strategy = self.strategy.drop_duplicates(subset=None, keep='first')
        # ascending=False 从大到小
        self.strategy.sort_values(by='trade_date', ascending=True, inplace=True)

    def goldenCross(self, data, row):
        if row.Index == 0:
            return
        cur = data.loc[row.Index]
        pre = data.loc[row.Index-1]
        if cur.EXPMA_10 > cur.EXPMA_60 and cur.EXPMA_10 > pre.EXPMA_10:
            self.__write2Strategy(row, 'buy', 'EXPMA10上穿60')

    def deathCross(self, data, row):
        if row.Index == 0:
            return
        cur = data.loc[row.Index]
        pre = data.loc[row.Index - 1]
        if cur.EXPMA_10 < cur.EXPMA_60 and cur.EXPMA_10 < pre.EXPMA_10:
            self.__write2Strategy(row, 'sell', 'EXPMA10下穿60')

    def judge(self, data):
        for row in data.itertuples(index=True):
            self.goldenCross(data, row)
            self.deathCross(data, row)

    def simplifyStrategy(self):
        flag = 'sell'
        tmp = pd.DataFrame(columns=["ts_code", "trade_date", "open",
                                     "high", "low", "close", "expma10",
                                     "expma60", "strategy", 'from', 'reason'])
        for row in self.strategy.itertuples():
            if row.Index == 0:
                flag = row.strategy
            if flag == row.strategy:
                tmp = tmp.append(pd.Series({
                    "ts_code": row.ts_code,
                    "trade_date": row.trade_date,
                    "open": row.open,
                    "high": row.high,
                    "low": row.low,
                    "close": row.close,
                    "expma10": row.expma10,
                    "expma60": row.expma60,
                    "strategy": row.strategy,
                    'from': 'EXPMAStockSelection',
                    'reason': row.reason
                }), ignore_index=True)
                flag = 'sell' if flag == 'buy' else 'buy'
        return tmp


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

    e = EXPMAStockSelection()
    df = e.initData(df, hot_date='20190101')
    print(df)
    e.judge(df)
    print(e.strategy)
    s = e.simplifyStrategy()
    print(s)

    tools.plot_K_line(df, 'EXPMA强弱线', s, '..')


