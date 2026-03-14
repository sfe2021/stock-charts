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
    {"ticker": "009150.KS", "name": "삼성전기", "code": "009150", "filename": "samsungelectro.html"},
    {"ticker": "161580.KQ", "name": "필옵틱스", "code": "161580", "filename": "philoptics.html"},
    {"ticker": "394280.KQ", "name": "오픈엣지테크놀로지", "code": "394280", "filename": "openedge.html"},
    {"ticker": "047560.KQ", "name": "이스트소프트", "code": "047560", "filename": "eastsoft.html"},
    {"ticker": "087600.KQ", "name": "픽셀플러스", "code": "087600", "filename": "pixelplus.html"},
    {"ticker": "432720.KQ", "name": "퀄리타스반도체", "code": "432720", "filename": "qualitas.html"},
    {"ticker": "007660.KS", "name": "이수페타시스", "code": "007660", "filename": "isupetasys.html"},
    {"ticker": "353200.KS", "name": "대덕전자", "code": "353200", "filename": "daeduck.html"},
    {"ticker": "099320.KQ", "name": "쎄트렉아이", "code": "099320", "filename": "satrec.html"},
    {"ticker": "189300.KQ", "name": "인텔리안테크", "code": "189300", "filename": "intellian.html"},
    {"ticker": "211270.KQ", "name": "AP위성", "code": "211270", "filename": "apsatellite.html"},
    {"ticker": "361390.KQ", "name": "제노코", "code": "361390", "filename": "genco.html"},
    {"ticker": "274090.KQ", "name": "켄코아에어로스페이스", "code": "274090", "filename": "kencoa.html"},
    {"ticker": "462350.KQ", "name": "이노스페이스", "code": "462350", "filename": "innospace.html"},
    {"ticker": "042370.KQ", "name": "비츠로테크", "code": "042370", "filename": "vitzrotech.html"},
    {"ticker": "474170.KQ", "name": "루미르", "code": "474170", "filename": "lumir.html"},
    {"ticker": "218410.KQ", "name": "RFHIC", "code": "218410", "filename": "rfhic.html"},
    {"ticker": "049080.KQ", "name": "기가레인", "code": "049080", "filename": "gigalane.html"},
    {"ticker": "032500.KQ", "name": "케이엠더블유", "code": "032500", "filename": "kmw.html"},
    {"ticker": "178320.KQ", "name": "서진시스템", "code": "178320", "filename": "seojin.html"},
    {"ticker": "050890.KQ", "name": "쏠리드", "code": "050890", "filename": "solid.html"},
    {"ticker": "138080.KQ", "name": "오이솔루션", "code": "138080", "filename": "oisolution.html"},
    {"ticker": "105840.KQ", "name": "우진", "code": "105840", "filename": "woojin.html"},
    {"ticker": "083650.KQ", "name": "비에이치아이", "code": "083650", "filename": "bhi.html"},
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

    function hasLen(a) { return a && typeof a.length === 'number' && a.length > 0; }

    function calcBounds() {
        dataXMin = Infinity; dataXMax = -Infinity;
        var traces = gd._fullData || gd.data;
        for (var t = 0; t < traces.length; t++) {
            var tr = traces[t];
            if (!hasLen(tr.x)) continue;
            for (var i = 0; i < tr.x.length; i++) {
                if (tr.x[i] == null) continue;
                var ts = new Date(tr.x[i]).getTime();
                if (!isNaN(ts)) {
                    if (ts < dataXMin) dataXMin = ts;
                    if (ts > dataXMax) dataXMax = ts;
                }
            }
        }
    }

    function autofit() {
        if (!gd._fullData || !gd._fullLayout) return;
        if (dataXMin === undefined) calcBounds();

        var xRange = gd._fullLayout.xaxis.range;
        if (!xRange) return;
        var xMin = new Date(xRange[0]).getTime();
        var xMax = new Date(xRange[1]).getTime();
        if (isNaN(xMin) || isNaN(xMax)) return;

        // x축 클램핑 (데이터 범위 밖으로 이동 방지)
        var update = {};
        var clamped = false;
        if (xMin < dataXMin) { xMin = dataXMin; clamped = true; }
        if (xMax > dataXMax) { xMax = dataXMax; clamped = true; }
        if (clamped) {
            update['xaxis.range'] = [new Date(xMin).toISOString(), new Date(xMax).toISOString()];
        }

        // y축 최적화 (주가 영역만 - 거래량 서브플롯 제외)
        var yMin = Infinity, yMax = -Infinity;
        var traces = gd._fullData;
        for (var t = 0; t < traces.length; t++) {
            var tr = traces[t];
            if (!hasLen(tr.x)) continue;
            // 거래량(yaxis2) 트레이스는 주가 y축 계산에서 제외
            if (tr.yaxis === 'y2' || tr.type === 'bar') continue;
            if (tr.type === 'candlestick' || tr.type === 'ohlc') {
                var high = tr.high, low = tr.low;
                if (!hasLen(high) || !hasLen(low)) continue;
                for (var i = 0; i < tr.x.length; i++) {
                    var ts = new Date(tr.x[i]).getTime();
                    if (ts < xMin || ts > xMax) continue;
                    var h = high[i], l = low[i];
                    if (h === h && h > yMax) yMax = h;
                    if (l === l && l < yMin) yMin = l;
                }
            } else if (hasLen(tr.y)) {
                for (var i = 0; i < tr.x.length; i++) {
                    var ts = new Date(tr.x[i]).getTime();
                    if (ts < xMin || ts > xMax) continue;
                    var v = tr.y[i];
                    if (v === v) {
                        if (v < yMin) yMin = v;
                        if (v > yMax) yMax = v;
                    }
                }
            }
        }

        if (yMin < Infinity && yMax > -Infinity) {
            var range = yMax - yMin;
            var pad = Math.max(range * 0.08, yMax * 0.02, 100);
            update['yaxis.range'] = [yMin - pad, yMax + pad];
            update['yaxis.autorange'] = false;
        }

        if (Object.keys(update).length > 0) {
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

    // === Clear Lines 버튼 추가 ===
    function addClearBtn() {
        var modeBar = document.querySelector('.modebar-group');
        if (!modeBar) { setTimeout(addClearBtn, 300); return; }
        var btn = document.createElement('a');
        btn.className = 'modebar-btn';
        btn.setAttribute('data-title', 'Clear lines');
        btn.setAttribute('data-toggle', 'false');
        btn.style.cursor = 'pointer';
        btn.innerHTML = '<svg viewBox="0 0 1000 1000" height="1em" width="1em"><path d="M742 167L500 408 258 167 167 258 408 500 167 742 258 833 500 592 742 833 833 742 592 500 833 258z" fill="currentColor"/></svg>';
        btn.addEventListener('click', function() {
            Plotly.relayout(gd, {shapes: []});
        });
        modeBar.appendChild(btn);
    }
    setTimeout(addClearBtn, 600);
})();
</script>
"""

chart_config = {
    'displayModeBar': True,
    'displaylogo': False,
    'scrollZoom': False,
    'modeBarButtonsToAdd': ['drawline'],
    'modeBarButtonsToRemove': [
        'toImage', 'zoom2d', 'select2d', 'lasso2d',
        'autoScale2d', 'resetScale2d', 'zoomIn2d', 'zoomOut2d',
    ],
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

    # 차트 생성 (서브플롯: 주가 75% + 거래량 25%)
    from plotly.subplots import make_subplots
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.75, 0.25],
    )

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
    ), row=1, col=1)

    # 60일 이동평균선
    ma_data = df[f'MA{MA_DAYS}'].dropna()
    fig.add_trace(go.Scatter(
        x=ma_data.index, y=ma_data, mode='lines', name='60일선',
        line=dict(color=MA_COLOR, width=1.2),
        hovertemplate='60일선: %{y:,.0f}원<extra></extra>'
    ), row=1, col=1)

    # 거래량 면적 차트 (모바일에서도 항상 보이도록 bar→area 변경)
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Volume'],
        name='거래량',
        mode='lines',
        fill='tozeroy',
        line=dict(color='#7986CB', width=0.5),
        fillcolor='rgba(121,134,203,0.4)',
        hovertemplate='거래량: %{y:,.0f}<extra></extra>'
    ), row=2, col=1)

    # 레이아웃
    fig.update_layout(
        title=dict(text=f'{name} ({code}) 주가 차트 (주봉)',
                   font=dict(size=18, color='#333333'), x=0.5, y=0.97),
        template='plotly_white', height=500, showlegend=True,
        legend=dict(orientation='h', yanchor='top', y=1.025,
                    xanchor='right', x=1.0, font=dict(size=10)),
        hovermode='x unified',
        margin=dict(l=10, r=10, t=105, b=30),
        dragmode='pan',
        newshape=dict(line=dict(color='#000000', width=2)),
        xaxis2=dict(type='date'),
        xaxis=dict(type='date', rangeslider=dict(visible=False)),
        yaxis=dict(tickformat=',', hoverformat=',.0f', side='right', fixedrange=True, automargin=True),
        yaxis2=dict(showticklabels=False, fixedrange=True),
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
