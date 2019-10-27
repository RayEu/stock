# stock v0.3

优化tools.SimpleIndicatorJudgment模块中的代码；
优化tools包的import方式；
优化MA20StockSelection的sell方法；
优化MA20StockSelection的buy方法的判断条件；
优化并重命名了相关包结构；

调整了相关模块的位置；
调整了MA20StockSelection类中相关API的位置，形成新的函数；

修正了因“三天未突破”的策略数据生成的错误；
修正了实时获取股票时的数据格式错误；
修正了实时股票数据的量能、MA值的计算错误；

增加了网页版的可视化界面；
增加了强弱线(EXPMA线)对股票进行判断；
增加了简化strategy的方法；
