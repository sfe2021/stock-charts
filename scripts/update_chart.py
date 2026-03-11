import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ===== 종목 설정 =====
STOCKS = [
    {"ticker": "043150.KQ", "name": "바텍", "code": "043150", "filename": "vatech.html"},
]

MA_DAYS = 60
MA_COLOR = '#FF9800'

autofit_js = """
<script>
(function() {
    var gd = document.querySelectorAll('.plotly-graph-div')[0];
    if (!gd) return;

    var busy = false;
    var dataXMin, dataXMax;

    function calcBounds() {
        dataXMin = Infinity; dataXMax = -Infinity;
        for (var t = 0; t < gd.data.length; t++) {
            var tr = gd.data[t];
            if (!tr.x) continue;
            for (var i = 0; i < tr.x.length; i++) {
                if (tr.x[i] == null) continue;
                var ts = new Date(tr.x[i]).getTime();
                if (ts < dataXMin) dataXMin = ts;
                if (ts > dataXMax) dataXMax = ts;
            }
        }
    }

    function autofit() {
        if (dataXMin === undefined) calcBounds();

        var xRange = gd._fullLayout.xaxis.range;
        if (!xRange) return;
        var xMin = new Date(xRange[0]).getTime();
        var xMax = new Date(xRange[1]).getTime();

        var clamped = false;
        if (xMin < dataXMin) { xMin = dataXMin; clamped = true; }
        if (xMax > dataXMax) { xMax = dataXMax; clamped = true; }

        var yMin = Infinity, yMax = -Infinity;
        for (var t = 0; t < gd.data.length; t++) {
            var tr = gd.data[t];
            if (!tr.x || !tr.y) continue;
            for (var i = 0; i < tr.x.length; i++) {
                var ts = new Date(tr.x[i]).getTime();
                if (ts < xMin || ts > xMax || tr.y[i] == null) continue;
                if (tr.y[i] < yMin) yMin = tr.y[i];
                if (tr.y[i] > yMax) yMax = tr.y[i];
            }
        }

        if (yMin < Infinity && yMax > -Infinity) {
            var range = yMax - yMin;
            var pad = Math.max(range * 0.08, yMax * 0.02, 100);
            var update = { 'yaxis.range': [yMin - pad, yMax + pad] };
            if (clamped) {
                update['xaxis.range'] = [new Date(xMin).toISOString(), new Date(xMax).toISOString()];
            }
            busy = true;
            Plotly.relayout(gd, update).then(function() {
                setTimeout(function() { busy = false; }, 50);
            });
        }
    }

    gd.on('plotly_relayout', function(ed) {
        if (busy) return;
        var keys = Object.keys(ed || {});
        for (var i = 0; i < keys.length; i++) {
            if (keys[i].indexOf('xaxis') === 0) {
                setTimeout(autofit, 50);
                return;
            }
        }
    });

    setTimeout(autofit, 500);
})();
</script>
"""

chart_config = {
    'displayModeBar': True,
    'displaylogo': False,
    'locale': 'ko',
    'scrollZoom': False,
}


def generate_chart(stock_info):
    ticker = stock_info['ticker']
    name = stock_info['name']
    code = stock_info['code']
    filename = stock_info['filename']

    print(f"[{name}] Downloading daily data...")
    stock = yf.Ticker(ticker)
    df_daily = stock.history(period="max", interval="1d")

    if df_daily.empty:
        print(f"[{name}] ERROR: no data")
        return False

    # 이동평균선 계산 (일봉 기반)
    df_daily[f'MA{MA_DAYS}'] = df_daily['Close'].rolling(window=MA_DAYS).mean()

    # 주봉 리샘플링
    df = df_daily.resample('W').agg({
        'Open': 'first', 'High': 'max', 'Low': 'min',
        'Close': 'last', 'Volume': 'sum'
    }).dropna(subset=['Close'])

    df[f'MA{MA_DAYS}'] = df_daily[f'MA{MA_DAYS}'].resample('W').last()

    # 차트 생성
    fig = go.Figure()

    # 종가 라인 - 상승=빨강, 하락=파랑
    up_x, up_y, dn_x, dn_y = [], [], [], []
    for i in range(1, len(df)):
        is_up = df['Close'].iloc[i] >= df['Close'].iloc[i-1]
        seg_x = [df.index[i-1], df.index[i], None]
        seg_y = [df['Close'].iloc[i-1], df['Close'].iloc[i], None]
        if is_up:
            up_x.extend(seg_x); up_y.extend(seg_y)
        else:
            dn_x.extend(seg_x); dn_y.extend(seg_y)

    fig.add_trace(go.Scatter(
        x=up_x, y=up_y, mode='lines', name='종가',
        line=dict(color='#EF5350', width=1.5), legendgroup='종가',
        hoverinfo='skip',
    ))
    fig.add_trace(go.Scatter(
        x=dn_x, y=dn_y, mode='lines', name='종가',
        line=dict(color='#2962FF', width=1.5), legendgroup='종가',
        showlegend=False, hoverinfo='skip',
    ))

    # 호버용 투명 trace (상승=빨강, 하락=파랑 색상 표시)
    hover_up_x, hover_up_y, hover_dn_x, hover_dn_y = [], [], [], []
    for i in range(len(df)):
        if i == 0 or df['Close'].iloc[i] >= df['Close'].iloc[i-1]:
            hover_up_x.append(df.index[i]); hover_up_y.append(df['Close'].iloc[i])
        else:
            hover_dn_x.append(df.index[i]); hover_dn_y.append(df['Close'].iloc[i])

    hover_tpl = '%{x|%Y-%m-%d}<br>종가: %{y:,.0f}원<extra></extra>'
    fig.add_trace(go.Scatter(
        x=hover_up_x, y=hover_up_y, mode='markers', name='종가',
        marker=dict(color='#EF5350', size=0.1), legendgroup='종가',
        showlegend=False, hovertemplate=hover_tpl,
    ))
    fig.add_trace(go.Scatter(
        x=hover_dn_x, y=hover_dn_y, mode='markers', name='종가',
        marker=dict(color='#2962FF', size=0.1), legendgroup='종가',
        showlegend=False, hovertemplate=hover_tpl,
    ))

    # 60일 이동평균선
    ma_data = df[f'MA{MA_DAYS}'].dropna()
    fig.add_trace(go.Scatter(
        x=ma_data.index, y=ma_data, mode='lines', name='60일선',
        line=dict(color=MA_COLOR, width=1.2),
        hovertemplate='60일선: %{y:,.0f}원<extra></extra>'
    ))

    # 레이아웃
    fig.update_layout(
        title=dict(text=f'{name} ({code}) 주가 차트 (주봉)',
                   font=dict(size=18, color='#333333'), x=0.5, y=0.97),
        template='plotly_white', height=750, showlegend=True,
        legend=dict(orientation='h', yanchor='top', y=1.025,
                    xanchor='right', x=1.0, font=dict(size=10)),
        hovermode='x unified',
        margin=dict(l=10, r=10, t=105, b=30),
        dragmode='pan',
        xaxis=dict(type='date', rangeslider=dict(visible=False)),
        yaxis=dict(tickformat=',', side='right', fixedrange=True, automargin=True),
    )

    # 기간 선택 버튼
    fig.update_xaxes(
        rangeselector=dict(
            buttons=[
                dict(count=3, label="3M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(count=3, label="3Y", step="year", stepmode="backward"),
                dict(count=5, label="5Y", step="year", stepmode="backward"),
                dict(label="ALL", step="all")
            ],
            font=dict(size=10), bgcolor='#f0f0f0', activecolor='#2962FF',
            x=0, y=1.06,
        ),
    )

    # HTML 저장 (Plotly 내장 - 티스토리 iframe 호환)
    out_path = os.path.join(BASE, filename)
    html = fig.to_html(include_plotlyjs=True, full_html=True, config=chart_config)
    html = html.replace('</body>', autofit_js + '</body>')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[{name}] Done -> {filename}")
    return True


if __name__ == '__main__':
    for s in STOCKS:
        generate_chart(s)
    print("All charts updated.")
