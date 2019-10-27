import pandas as pd


def simplifyStrategies(*strategies):
    _strategy = pd.DataFrame(columns=["ts_code", "trade_date", 'open', 'high', 'low',
                                      'close', 'strategy', 'from', 'reason'])
    for strategy in strategies:
        tmp = strategy[["ts_code", "trade_date", 'open', 'high', 'low',
                        'close', 'strategy', 'from', 'reason']]
        _strategy = pd.concat([_strategy, tmp], ignore_index=True)

    # 对日期进行处理
    def deal(data):
        if data.shape[0] == 1:
            return data
        _r = data[0:1]
        _r['reason'] = '；'.join(data['reason'].tolist())
        _r['from'] = '；'.join(data['from'].tolist())
        return _r

    _strategy = _strategy.groupby(['trade_date', 'strategy']).apply(deal)
    #_strategy = _strategy.sort_values(by='trade_date', ascending=True)
    _strategy = _strategy.reset_index(drop=True)
    return _strategy


if __name__ == '__main__':
    s = pd.DataFrame({
        'ts_code': ['300525', '300525', '300525', '300525', '300525'],
        'trade_date': ['20190101', '20190101', '20190102', '20190102', '20190103'],
        'open': [21, 21, 23, 23, 25],
        'high': [23, 23, 25, 25, 27],
        'low': [19, 19, 17, 17, 15],
        'close': [25, 25, 27, 27, 29],
        'strategy': ['buy', 'sell', 'sell', 'sell', 'sell'],
        'from': ['ma20', 'expma', 'ma20', 'expma', 'expma'],
        'reason': ['res1', 'res0', 'res2', 'res3', 'res4']
    })
    ss = simplifyStrategies(s)
    print(ss)

