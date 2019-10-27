import strategys as st
import tools
import pandas as pd
from tools import GetDaily, simplifyStrategies
# 显示所有列
pd.set_option('display.max_columns', None)
# 显示所有行
pd.set_option('display.max_rows', None)
# 设置value的显示长度为100，默认为50
pd.set_option('max_colwidth', 100)

# 第一步：获取数据
g = GetDaily()
df = g.getDaily('002655.SZ')

# 第二步：策略选取
ma = st.MA20StockSelection()
df = ma.initData(df, hot_date='20190101')
ma.judge(df)
ma20 = ma.simplifyStrategy()
print('MA20StockSelection')
print(ma20)

exp = st.EXPMAStockSelection()
df = exp.initData(df, hot_date='20190101')
exp.judge(df)
expma = exp.simplifyStrategy()
print('EXPMAStockSelection')
print(expma)

ss = simplifyStrategies(ma20, expma)
print('汇总各策略')
print(ss)
ss.to_excel('./re.xlsx')
# 第三步：绘制图形
tools.plot_K(df, ss, lineModle=['ma20','ma120', 'EXPMA_10', 'EXPMA_60'])
