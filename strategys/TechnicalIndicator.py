import pandas as pd
import numpy as np


def ma(data, num, name='ma'):
    if name == 'ma':
        _name = name + str(num)
    else:
        _name = name
    data[_name] = pd.Series.rolling(data['close'], window=num).mean()
    data[_name] = data[_name].round(decimals=2)
    return data


def boll(data):
    data = ma(data, 20, 'BOLL')
    values = []
    tmp = pd.DataFrame(columns=['trade_date', 'MD'])
    for index, row in data.iterrows():
        values.append(row['close'])
        if len(values) == 20:
            v = np.sqrt(np.sum((np.array(values) - np.mean(values)) ** 2) / 19)
            tmp = tmp.append(
                pd.Series({
                    'trade_date': row['trade_date'],
                    'MD': v
                }),
                ignore_index=True
            )
            del values[0]
    df = pd.merge(data, tmp, on='trade_date', how='outer')
    df = df.dropna(axis=0, subset=['BOLL', 'MD'], how='all')  # 去掉ma20和ma120均为nan
    df['BOLL_UP'] = df['BOLL'] + 2 * df['MD']
    df['BOLL_DN'] = df['BOLL'] - 2 * df['MD']
    del df['MD']
    return df


