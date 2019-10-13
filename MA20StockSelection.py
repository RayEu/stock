# coding: utf-8

import tushare as ts
import pandas as pd

#显示所有列
pd.set_option('display.max_columns', None)
#显示所有行
pd.set_option('display.max_rows', None)
#设置value的显示长度为100，默认为50
pd.set_option('max_colwidth',100)


class MA20StockSelection:

    def __init__(self):
        token = '90eb9db39113fb8cb7f9f4f6f62a743bb79b2ab2a73306725fd925f9'
        ts.set_token(token)
        self.pro = ts.pro_api(token)

        self.strategy = pd.DataFrame(columns=["ts_code", "trade_date", "open",
                                              "high", "low", "close", "vol",
                                              "ma20", "strategy", 'from', 'reason'
                                              ])

    def getDaily(self, ts_code, start_date='20180101', hot_date='20180101'):
        df = ts.pro_bar(ts_code=ts_code, adj='qfq',
                        start_date=start_date,
                        ma=[20, 180])
        df = df[['ts_code', 'trade_date', 'open', 'high',
                 'low', 'close', 'vol', 'ma20', 'pct_chg']]
        df = df.dropna(axis=0, how='any')
        df = df[df['trade_date'] >= hot_date]
        df = df.iloc[::-1]
        df = df.reset_index(drop=True)
        return df

    def yangOverYin(self, data, cur_index):
        if cur_index == 0:
            return False
        cur = data.loc[cur_index]
        pre = data.loc[cur_index - 1]
        # 前一天阴线
        if cur.close > cur.open:
            cur_high = cur.close
        else:
            return False
        # 今天阳线
        if pre.close < pre.open:
            pre_low = pre.close
        else:
            return False
        # 严格来说：第二根K线的实体将第一根K线包住，这里仅包住4/5即可
        if cur_high > abs(pre.close - pre.open) * 4 / 5 + pre_low:
            return True
        else:
            return False

    def judgeVOL(self, data, cur_index, multiple):
        if cur_index == 0:
            return False
        cur = data.loc[cur_index]
        pre = data.loc[cur_index - 1]
        if cur.vol > pre.vol * multiple:
            return True
        else:
            return False

    def overMA20Bais(self, data, cur_index, multiple=0.2):
        cur = data.loc[cur_index]
        bais = (cur.close - cur.ma20)/cur.ma20
        if bais > multiple:
            return True
        else:
            return False

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
        #self.strategy = self.strategy.drop_duplicates(subset=['trade_date', 'strategy'], keep='first')
        self.strategy = self.strategy.drop_duplicates(subset=None, keep='first')
        # ascending=False 从大到小
        self.strategy.sort_values(by='trade_date', ascending=True, inplace=True)

    def __firstBreak(self, data, cur_index):
        if cur_index == 0:
            return True
        cur = data.loc[cur_index]
        pre = data.loc[cur_index - 1]
        if cur.close > cur.ma20 and pre.close < pre.ma20:
            return True
        else:
            return False

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

    def buy(self, data, row):
        '''
        两种买入方式：
        前提：20日均线与半年线向上；20日均线高于半年线；收盘突破20日均线
        1、量能为前一日的2倍及以上
        2、阳包阴，量能为前一日的1.5倍及以上
        :param data:
        :param row:
        :return:
        '''
        # 20日均线高于半年线，收盘突破20日均线
        if row.close > row.ma20:
            # 1、量能为前一日的2倍及以上
            if self.judgeVOL(data, row.Index, 2):
                for date, va in self.__getLastStrategy(row.trade_date):
                    if va is None or va == 'sell' or va == 'monitor':
                        self.__write2Strategy(row, 'buy', '量能为前一日的2倍及以上')
                        break
                    elif va == 'buy':
                        break
            # 2、阳包阴 & 量能为前一日的1.5倍及以上
            if self.yangOverYin(data, row.Index) and self.judgeVOL(data, row.Index, 1.5):
                for date, va in self.__getLastStrategy(row.trade_date):
                    if va is None or va == 'sell' or va == 'monitor':
                        self.__write2Strategy(row, 'buy', '阳包阴 & 量能为前一日的1.5倍及以上')
                        break
                    elif va == 'buy':
                        break

    def dealMonitor(self, data, trade_date):
        '''
        处理monitor信息
        :param data:
        :param trade_date:
        :return:
        '''
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
                        self.strategy = self.strategy[~(self.strategy['trade_date'].isin([row.trade_date]))]
                        break
                else:  # 3天未突破
                    self.strategy = self.strategy[~(self.strategy['trade_date'].isin([row.trade_date]))]
                    self.__write2Strategy(row, 'sell', '三天未突破', trade_date=da[ind + 3])
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
            if self.judgeVOL(data, row.Index, 2.5):
                for date, va in self.__getLastStrategy(row.trade_date):
                    if va is None:
                        break
                    if va == 'sell':
                        break
                    elif va == 'buy' or va == 'monitor':
                        self.__write2Strategy(row, 'sell', '跌破20 & 大量放量')
                        break
            else:
                # 2、非大量 & 三个交易日无法收复
                for date, va in self.__getLastStrategy(row.trade_date):
                    if va is None:
                        break
                    if va == 'sell' or va == 'monitor':
                        break
                    elif va == 'buy':
                        self.__write2Strategy(row, 'monitor', '跌破20 & 非大量')
                        break
        # 3、远离20
        elif self.overMA20Bais(data, row.Index) or row.pct_chg < -5.0:
            # 量能为突破20的2倍及以上
            for date, va in self.__getLastStrategy(row.trade_date):
                if va is None:
                    break
                if va == 'sell' or va == 'monitor':
                    continue
                elif va == 'buy':
                    vol = self.strategy[self.strategy['trade_date'] == date]['vol'].values[0]
                    if row.vol >= vol * 2:
                        self.__write2Strategy(row, 'sell', '远离20 & 量能为突破20的2倍及以上')
                    break

    def judge(self, data):
        for row in data.itertuples(index=True):
            self.dealMonitor(data, row.trade_date)
            self.buy(data, row)
            self.sell(data, row)
            #print(row.trade_date)
            #print(self.strategy[['trade_date', 'close', 'vol', 'strategy', 'reason']])
            #print('==================================================================')

    def deal(self, data):
        flag = 'buy'
        tmp = []
        for row in self.strategy.itertuples():
            if row.strategy == flag:
                tmp.append(row.trade_date)
                tmp.append(row.close)
                flag = 'sell' if flag == 'buy' else 'buy'
            else:
                continue
        if len(tmp) % 4 != 0:
            t = data.iloc[-1:]
            tmp.append(t.trade_date.values[0])
            tmp.append(t.close.values[0])
        business = pd.DataFrame(columns=["ts_code", "buy_date", "buy",
                                         "sell_date", "sell"
                                         ])
        for i in range(0, len(tmp), 4):
            series = pd.Series({"ts_code": data.iloc[-1:].ts_code.values[0],
                                "buy_date": tmp[i],
                                'buy': tmp[i+1],
                                'sell_date': tmp[i+2],
                                'sell': tmp[i+3],
                                })
            business = business.append(series, ignore_index=True)
        print(business)


if __name__ == '__main__':
    ma = MA20StockSelection()
    df = ma.getDaily('300366.SZ', hot_date='20190101')
    ma.judge(df)
    print(ma.strategy[['trade_date', 'close', 'vol', 'strategy', 'reason']])
    ma.deal(df)



