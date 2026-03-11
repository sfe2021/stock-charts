import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ===== 종목 설정 =====
STOCKS = [
    {"ticker": "043150.KQ", "name": "바텍", "code": "043150", "filename": "vatech.html"},
    {"ticker": "011790.KS", "name": "SKC", "code": "011790", "filename": "skc.html"},
    {"ticker": "030520.KQ", "name": "한글과컴퓨터", "code": "030520", "filename": "hancom.html"},
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
            if (!tr.x) continue;
            if (tr.type === 'candlestick') {
                for (var i = 0; i < tr.x.length; i++) {
                    var ts = new Date(tr.x[i]).getTime();
                    if (ts < xMin || ts > xMax) continue;
                    if (tr.high && tr.high[i] != null && tr.high[i] > yMax) yMax = tr.high[i];
                    if (tr.low && tr.low[i] != null && tr.low[i] < yMin) yMin = tr.low[i];
                }
            } else if (tr.y) {
                for (var i = 0; i < tr.x.length; i++) {
                    var ts = new Date(tr.x[i]).getTime();
                    if (ts < xMin || ts > xMax || tr.y[i] == null) continue;
                    if (tr.y[i] < yMin) yMin = tr.y[i];
                    if (tr.y[i] > yMax) yMax = tr.y[i];
                }
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

    # 캔들스틱(봉) 차트 - 상승=빨강, 하락=파랑
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='주봉',
        increasing=dict(line=dict(color='#EF5350'), fillcolor='#EF5350'),
        decreasing=dict(line=dict(color='#2962FF'), fillcolor='#2962FF'),
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
        yaxis=dict(tickformat=',', hoverformat=',.0f', side='right', fixedrange=True, automargin=True),
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
