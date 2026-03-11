import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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

    var skipNext = false;

    function autofit() {
        var xRange = gd._fullLayout.xaxis.range;
        if (!xRange) return;
        var xMin = new Date(xRange[0]).getTime();
        var xMax = new Date(xRange[1]).getTime();

        var yMin = Infinity, yMax = -Infinity, vMax = 0;

        for (var t = 0; t < gd.data.length; t++) {
            var tr = gd.data[t];
            if (!tr.x || !tr.y) continue;
            var isVol = (tr.yaxis === 'y2');
            for (var i = 0; i < tr.x.length; i++) {
                var ts = new Date(tr.x[i]).getTime();
                if (ts < xMin || ts > xMax || tr.y[i] == null) continue;
                if (isVol) {
                    if (tr.y[i] > vMax) vMax = tr.y[i];
                } else {
                    if (tr.y[i] < yMin) yMin = tr.y[i];
                    if (tr.y[i] > yMax) yMax = tr.y[i];
                }
            }
        }

        if (yMin < Infinity && yMax > -Infinity) {
            var range = yMax - yMin;
            var pad = Math.max(range * 0.08, yMax * 0.02, 100);
            skipNext = true;
            Plotly.relayout(gd, {
                'yaxis.range': [yMin - pad, yMax + pad],
                'yaxis2.range': [0, vMax * 1.1]
            });
        }
    }

    gd.on('plotly_relayout', function(ed) {
        if (skipNext) { skipNext = false; return; }
        if (ed && (ed['xaxis.range[0]'] || ed['xaxis.range'] || ed['xaxis.autorange'])) {
            setTimeout(autofit, 100);
        }
    });

    gd.on('plotly_afterplot', function() {
        setTimeout(autofit, 200);
    });
})();
</script>
"""

chart_config = {
    'displayModeBar': False,
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
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.03, row_heights=[0.75, 0.25]
    )

    # 종가 라인
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Close'], mode='lines', name='종가',
        line=dict(color='#333333', width=1.5),
        hovertemplate='%{x|%Y-%m-%d}<br>종가: %{y:,.0f}원<extra></extra>'
    ), row=1, col=1)

    # 60일 이동평균선
    ma_data = df[f'MA{MA_DAYS}'].dropna()
    fig.add_trace(go.Scatter(
        x=ma_data.index, y=ma_data, mode='lines', name='60일선',
        line=dict(color=MA_COLOR, width=1.2),
        hovertemplate='60일선: %{y:,.0f}원<extra></extra>'
    ), row=1, col=1)

    # 거래량
    vol_colors = []
    for i in range(len(df)):
        if i == 0 or df['Close'].iloc[i] >= df['Close'].iloc[i-1]:
            vol_colors.append('#EF5350')
        else:
            vol_colors.append('#2962FF')

    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'], name='거래량',
        marker_color=vol_colors, opacity=0.7,
        width=6 * 24 * 3600 * 1000,
        hovertemplate='%{x|%Y-%m-%d}<br>거래량: %{y:,.0f}<extra></extra>'
    ), row=2, col=1)

    # 레이아웃
    fig.update_layout(
        title=dict(text=f'{name} ({code}) 주가 차트 (주봉)',
                   font=dict(size=18, color='#333333'), x=0.5, y=0.97),
        template='plotly_white', height=750, showlegend=True,
        legend=dict(orientation='h', yanchor='top', y=1.025,
                    xanchor='right', x=1.0, font=dict(size=10)),
        hovermode='x unified',
        margin=dict(l=10, r=10, t=105, b=30),
        dragmode=False,
        xaxis2=dict(rangeslider=dict(visible=False), type='date'),
        yaxis=dict(tickformat=',', side='right', fixedrange=True, automargin=True),
        yaxis2=dict(tickformat='.2s', side='right', fixedrange=True, automargin=True),
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
        row=1, col=1
    )

    # HTML 저장 (CDN)
    out_path = os.path.join(BASE, filename)
    html = fig.to_html(include_plotlyjs='cdn', full_html=True, config=chart_config)
    html = html.replace('</body>', autofit_js + '</body>')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[{name}] Done -> {filename}")
    return True


if __name__ == '__main__':
    for s in STOCKS:
        generate_chart(s)
    print("All charts updated.")
