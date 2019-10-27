from pyecharts.charts import Kline, Line, Bar, EffectScatter, Grid
from pyecharts import options as opts


def plot_K(data, strategy=None, lineModle=None, path='.'):
    date = data["trade_date"].apply(lambda x: str(x)).tolist()
    k_plot_value = data.apply(lambda record: [record['open'], record['close'], record['low'], record['high']],
                              axis=1).tolist()
    # 1、K chart
    kline = Kline()
    kline.add_xaxis(date)
    kline.add_yaxis(
        data['ts_code'].values.tolist()[0],
        k_plot_value,
        # 修改K线颜色
        itemstyle_opts=opts.ItemStyleOpts(
            color="#ec0000",
            color0="#00da3c",
            border_color="#8A0000",
            border_color0="#008F28",
        ),
    )
    kline.set_global_opts(
        # 显示分割区域
        xaxis_opts=opts.AxisOpts(is_scale=True),
        yaxis_opts=opts.AxisOpts(
            is_scale=True,
            splitarea_opts=opts.SplitAreaOpts(
                is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)
            ),
        ),
        # 设置滑动条
        datazoom_opts=[
            # Grid中第一张图的滑动条
            opts.DataZoomOpts(
                is_show=False,
                type_="inside",
                xaxis_index=[0, 1],
                range_start=0,
                range_end=100,
            ),
            # Grid中第二张图的滑动条
            opts.DataZoomOpts(
                is_show=True,
                type_="slider",
                xaxis_index=[0, 1],
                pos_top="90%",
                range_start=0,
                range_end=100,
            ),
        ],
        # 设置title
        title_opts=opts.TitleOpts(title=data['ts_code'].values.tolist()[0]),
        # 设置十字，显示具体信息，对grid中所有的图起效
        tooltip_opts=opts.TooltipOpts(
            trigger="axis",
            axis_pointer_type="cross",
            background_color="rgba(245, 245, 245, 0.8)",
            border_width=1,
            border_color="#ccc",
            textstyle_opts=opts.TextStyleOpts(color="#000"),
        ),
        # 多grid中的十字，显示的信息合并为一个
        axispointer_opts=opts.AxisPointerOpts(
            is_show=True,
            link=[{"xAxisIndex": "all"}],
            label=opts.LabelOpts(background_color="#777"),
        ),
        # 增加右上角的选择框
        brush_opts=opts.BrushOpts(
            x_axis_index="all",
            brush_link="all",
            out_of_brush={"colorAlpha": 0.1},
            brush_type="lineX",
        ),
    )

    # 2、BS Point
    if strategy is None:
        overlap_kline_line = kline
    else:
        es = EffectScatter()
        for row in strategy.itertuples():
            if row.strategy == 'sell':
                es.add_xaxis([row.trade_date])
                es.add_yaxis("sell", [row.high], color='#008F28', symbol="pin")
            if row.strategy == 'buy':
                es.add_xaxis([row.trade_date])
                es.add_yaxis("buy", [row.high], color='#8A0000')
        overlap_kline_line = kline.overlap(es)

    # 3、Line
    if lineModle is not None:
        line = Line()
        line.add_xaxis(date)
        for m in lineModle:
            try:
                line.add_yaxis(
                    series_name=m,
                    y_axis=data[m].values.tolist(),
                    is_smooth=True,
                    is_hover_animation=False,
                    linestyle_opts=opts.LineStyleOpts(width=3, opacity=0.5),
                    label_opts=opts.LabelOpts(is_show=False),
                )
                line.set_global_opts(
                    # 'category': 类目轴，适用于离散的类目数据，
                    # 为该类型时必须通过 data 设置类目数据。
                    xaxis_opts=opts.AxisOpts(type_="category")
                )
            except Exception as e:
                print('error: No ', e, ' in data')
                return
        overlap_kline_line = overlap_kline_line.overlap(line)

    # 4、Bar
    bar = Bar()
    bar.add_xaxis(xaxis_data=date)
    bar.add_yaxis(
        series_name="Volume",
        yaxis_data=data['vol'].values.tolist(),
        xaxis_index=1,
        yaxis_index=1,
        label_opts=opts.LabelOpts(is_show=False),
    )
    bar.set_global_opts(
        # 去除BAR的x轴
        xaxis_opts=opts.AxisOpts(
            type_="category",
            is_scale=True,
            grid_index=1,
            boundary_gap=False,
            axisline_opts=opts.AxisLineOpts(is_on_zero=False),
            axistick_opts=opts.AxisTickOpts(is_show=False),
            splitline_opts=opts.SplitLineOpts(is_show=False),
            axislabel_opts=opts.LabelOpts(is_show=False),
            split_number=20,
            min_="dataMin",
            max_="dataMax",
        ),
        # 去除BAR的y轴
        yaxis_opts=opts.AxisOpts(
            grid_index=1,
            is_scale=True,
            split_number=2,
            axislabel_opts=opts.LabelOpts(is_show=False),
            axisline_opts=opts.AxisLineOpts(is_show=False),
            axistick_opts=opts.AxisTickOpts(is_show=False),
            splitline_opts=opts.SplitLineOpts(is_show=False),
        ),
        # 去除BAR的头部中间的图例说明
        legend_opts=opts.LegendOpts(is_show=False),
    )

    # 5、Grid Overlap + Bar
    grid_chart = Grid()
    grid_chart.add(
        overlap_kline_line,
        grid_opts=opts.GridOpts(pos_left="10%", pos_right="8%", height="50%"),
    )
    grid_chart.add(
        bar,
        grid_opts=opts.GridOpts(
            pos_left="10%", pos_right="8%", pos_top="70%", height="16%"
        ),
    )
    grid_chart.render(path + '/render.html')
    

if __name__ == '__main__':
    import pandas as pd
    df = pd.read_excel('./data.xlsx', header=0)
    s = pd.read_excel('./re.xlsx', header=0)
    plot_K(df, s, ['ma20'])
