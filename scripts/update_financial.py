"""
바텍 재무제표 자동 업데이트 스크립트
- DART API로 연간/분기 재무데이터 조회
- yfinance로 연말 종가 → PER/PBR 자동 계산
- 공시 목록 체크 → 새 보고서 있을 때만 갱신
"""
import json, os, sys, urllib.request, urllib.parse
from datetime import datetime, timedelta

import yfinance as yf

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DART_KEY = os.environ.get('DART_API_KEY', '')

# ===== 종목 설정 =====
STOCKS = [
    {
        'name': '바텍',
        'code': '043150',
        'corp_code': '00264255',
        'ticker': '043150.KQ',
        'capital': 7427128000,  # 자본금 (고정)
        'annual_file': 'vatech_financial.html',
        'quarter_file': 'vatech_financial_q.html',
    },
    {
        'name': 'SKC',
        'code': '011790',
        'corp_code': '00139889',
        'ticker': '011790.KS',
        'capital': 16312750000,  # 자본금 약 163억원 (2024 사업보고서 기준)
        'annual_file': 'skc_financial.html',
        'quarter_file': 'skc_financial_q.html',
    },
    {
        'name': '한글과컴퓨터',
        'code': '030520',
        'corp_code': '00204262',
        'ticker': '030520.KQ',
        'capital': 13465674000,  # 자본금 약 134.6억원
        'annual_file': 'hancom_financial.html',
        'quarter_file': 'hancom_financial_q.html',
    },
    {
        'name': '삼성전기',
        'code': '009150',
        'corp_code': '00126371',
        'ticker': '009150.KS',
        'capital': 388003400000,
        'annual_file': 'samsungelectro_financial.html',
        'quarter_file': 'samsungelectro_financial_q.html',
    },
    {
        'name': '필옵틱스',
        'code': '161580',
        'corp_code': '00938721',
        'ticker': '161580.KQ',
        'capital': 11814031000,
        'annual_file': 'philoptics_financial.html',
        'quarter_file': 'philoptics_financial_q.html',
    },
    {
        'name': '오픈엣지테크놀로지',
        'code': '394280',
        'corp_code': '01571107',
        'ticker': '394280.KQ',
        'capital': 2482346300,
        'annual_file': 'openedge_financial.html',
        'quarter_file': 'openedge_financial_q.html',
    },
    {
        'name': '이스트소프트',
        'code': '047560',
        'corp_code': '00273420',
        'ticker': '047560.KQ',
        'capital': 5803921000,
        'annual_file': 'eastsoft_financial.html',
        'quarter_file': 'eastsoft_financial_q.html',
    },
    {
        'name': '픽셀플러스',
        'code': '087600',
        'corp_code': '00495086',
        'ticker': '087600.KQ',
        'capital': 4083279000,
        'annual_file': 'pixelplus_financial.html',
        'quarter_file': 'pixelplus_financial_q.html',
    },
    {
        'name': '퀄리타스반도체',
        'code': '432720',
        'corp_code': '01584183',
        'ticker': '432720.KQ',
        'capital': 6964596000,
        'annual_file': 'qualitas_financial.html',
        'quarter_file': 'qualitas_financial_q.html',
    },
    {
        'name': '이수페타시스',
        'code': '007660',
        'corp_code': '00107613',
        'ticker': '007660.KS',
        'capital': 63246419000,
        'annual_file': 'isupetasys_financial.html',
        'quarter_file': 'isupetasys_financial_q.html',
    },
    {
        'name': '대덕전자',
        'code': '353200',
        'corp_code': '01478712',
        'ticker': '353200.KS',
        'capital': 25756222000,
        'annual_file': 'daeduck_financial.html',
        'quarter_file': 'daeduck_financial_q.html',
    },
    {
        'name': '쎄트렉아이',
        'code': '099320',
        'corp_code': '00449254',
        'ticker': '099320.KQ',
        'capital': 5475639000,
        'annual_file': 'satrec_financial.html',
        'quarter_file': 'satrec_financial_q.html',
    },
    {
        'name': '인텔리안테크',
        'code': '189300',
        'corp_code': '00664181',
        'ticker': '189300.KQ',
        'capital': 5366667000,
        'annual_file': 'intellian_financial.html',
        'quarter_file': 'intellian_financial_q.html',
    },
    {
        'name': 'AP위성',
        'code': '211270',
        'corp_code': '00874803',
        'ticker': '211270.KQ',
        'capital': 7541152000,
        'annual_file': 'apsatellite_financial.html',
        'quarter_file': 'apsatellite_financial_q.html',
    },
    {
        'name': '제노코',
        'code': '361390',
        'corp_code': '01014718',
        'ticker': '361390.KQ',
        'capital': 3782394500,
        'annual_file': 'genco_financial.html',
        'quarter_file': 'genco_financial_q.html',
    },
    {
        'name': '켄코아에어로스페이스',
        'code': '274090',
        'corp_code': '01158553',
        'ticker': '274090.KQ',
        'capital': 6456613000,
        'annual_file': 'kencoa_financial.html',
        'quarter_file': 'kencoa_financial_q.html',
    },
    {
        'name': '이노스페이스',
        'code': '462350',
        'corp_code': '01700587',
        'ticker': '462350.KQ',
        'capital': 9375694000,
        'annual_file': 'innospace_financial.html',
        'quarter_file': 'innospace_financial_q.html',
    },
    {
        'name': '비츠로테크',
        'code': '042370',
        'corp_code': '00103644',
        'ticker': '042370.KQ',
        'capital': 13100012500,
        'annual_file': 'vitzrotech_financial.html',
        'quarter_file': 'vitzrotech_financial_q.html',
    },
    {
        'name': '루미르',
        'code': '474170',
        'corp_code': '01636565',
        'ticker': '474170.KQ',
        'capital': 8863848000,
        'annual_file': 'lumir_financial.html',
        'quarter_file': 'lumir_financial_q.html',
    },
]

# ===== DART API 헬퍼 =====
def dart_get(endpoint, params):
    params['crtfc_key'] = DART_KEY
    url = f'https://opendart.fss.or.kr/api/{endpoint}?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    if data.get('status') == '000':
        return data.get('list', [])
    return []


def check_new_reports(corp_code):
    """최근 60일 내 새 사업/분기보고서가 있는지 체크"""
    today = datetime.now()
    bgn = (today - timedelta(days=60)).strftime('%Y%m%d')
    end = today.strftime('%Y%m%d')
    params = {
        'corp_code': corp_code,
        'bgn_de': bgn,
        'end_de': end,
        'pblntf_ty': 'A',  # 정기공시
        'page_count': '100',
    }
    items = dart_get('list.json', params)
    keywords = ['사업보고서', '분기보고서', '반기보고서']
    for item in items:
        title = item.get('report_nm', '')
        if any(k in title for k in keywords):
            return True
    return False


def fetch_year_data(corp_code, year, reprt_code):
    """한 보고서의 재무 데이터 전체 조회 (CFS 우선, 없으면 OFS fallback)"""
    base_params = {'corp_code': corp_code, 'bsns_year': str(year), 'reprt_code': reprt_code}

    # CFS(연결) 먼저 시도
    acnt = dart_get('fnlttSinglAcnt.json', {**base_params, 'fs_div': 'CFS'})
    acnt_all = dart_get('fnlttSinglAcntAll.json', {**base_params, 'fs_div': 'CFS'})

    # CFS 데이터가 없으면 OFS(별도)로 fallback
    has_cfs = any(item.get('fs_div') == 'CFS' for item in acnt) if acnt else False
    if not has_cfs:
        print(f"    CFS 없음 → OFS fallback ({year}, {reprt_code})")
        acnt = dart_get('fnlttSinglAcnt.json', {**base_params, 'fs_div': 'OFS'})
        acnt_all = dart_get('fnlttSinglAcntAll.json', {**base_params, 'fs_div': 'OFS'})

    div_data = dart_get('alotMatter.json', base_params)
    stock_data = dart_get('stockTotqySttus.json', base_params)

    return acnt, acnt_all, div_data, stock_data


def parse_num(s):
    if not s or s.strip() in ['-', '']:
        return None
    return int(s.replace(',', ''))


def process_financial(acnt, acnt_all, div_data, stock_data, capital):
    """재무 데이터 파싱 및 계산"""
    r = {}

    # --- fnlttSinglAcnt (주요계정) ---
    # CFS 또는 OFS 중 실제 데이터가 있는 것을 사용 (fetch에서 이미 결정됨)
    target_fs = 'CFS'
    if acnt and not any(item.get('fs_div') == 'CFS' for item in acnt):
        target_fs = 'OFS'
    for item in acnt:
        if item.get('fs_div') != target_fs:
            continue
        acct = item.get('account_nm', '')
        val = item.get('thstrm_amount', '')
        if not val or val.strip() in ['-', '']:
            continue
        v = int(val.replace(',', ''))
        if '매출액' in acct:
            r['매출액'] = v
        elif acct == '영업수익' or acct == '수익(매출액)' or acct == '수익':
            # 일부 기업은 "매출액" 대신 "영업수익" 또는 "수익" 사용
            if '매출액' not in r:
                r['매출액'] = v
        elif '영업이익' in acct and '매출' not in acct:
            r['영업이익'] = v
        elif '법인세차감전' in acct:
            r['세전이익'] = v
        elif '당기순이익' in acct or '당기순손실' in acct:
            r['당기순이익'] = v
        elif acct == '자산총계':
            r['자산총계'] = v
        elif acct == '부채총계':
            r['부채총계'] = v
        elif acct == '자본총계':
            r['자본총계'] = v

    # --- fnlttSinglAcntAll (세부 항목) ---
    for item in acnt_all:
        sj = item.get('sj_nm', '')
        acct = item.get('account_nm', '')
        amt_s = item.get('thstrm_amount', '')
        if not amt_s or amt_s.strip() in ['-', '']:
            continue
        amt = int(amt_s.replace(',', ''))

        # 영업수익/수익을 매출로 처리 (매출액이 주요계정에 없는 경우)
        if ('손익' in sj or '포괄' in sj) and acct in ('영업수익', '수익', '수익(매출액)'):
            if '매출액' not in r:
                r['매출액'] = amt

        if '포괄손익' in sj:
            if '지배기업' in acct or '지배주주' in acct:
                if '당기순이익' in acct or '당기순손익' in acct or '소유주지분' in acct or '귀속' in acct:
                    r['순이익_지배'] = amt
            elif '비지배지분' in acct and ('당기순이익' in acct or '당기순손익' in acct or acct.strip() == '비지배지분'):
                r['순이익_비지배'] = amt

        if '재무상태표' in sj:
            if '지배기업' in acct and ('귀속' in acct or '소유' in acct):
                r['자본_지배'] = amt
            elif acct == '비지배지분':
                r['자본_비지배'] = amt
            elif '단기차입금' in acct or ('유동' in acct and '차입금' in acct):
                r.setdefault('차입금_유동', 0)
                r['차입금_유동'] += amt
            elif ('장기차입금' in acct or ('장기' in acct and '차입금' in acct)) and '유동' not in acct:
                r.setdefault('차입금_비유동', 0)
                r['차입금_비유동'] += amt

        if '현금흐름' in sj:
            if '영업활동' in acct and '현금흐름' in acct:
                r['영업CF'] = amt
            elif '투자활동' in acct and '현금흐름' in acct:
                r['투자CF'] = amt
            elif '재무활동' in acct and '현금흐름' in acct:
                r['재무CF'] = amt
            elif '유형자산' in acct and '취득' in acct and '무형' not in acct:
                r['CAPEX'] = amt

    # --- 자본금 ---
    r['자본금'] = capital

    # --- 배당 정보 ---
    for item in div_data:
        se = item.get('se', '')
        stock_knd = item.get('stock_knd', '')
        thstrm = item.get('thstrm', '')
        if not thstrm or thstrm.strip() == '-':
            continue
        if '주당 현금배당금' in se and ('보통주' in stock_knd or stock_knd == ''):
            val = parse_num(thstrm)
            if val and val > 0:
                r['DPS'] = val
        elif '현금배당수익률' in se and ('보통주' in stock_knd or stock_knd == ''):
            try:
                val = float(thstrm.replace(',', ''))
                if val > 0:
                    r['배당수익률'] = val
            except:
                pass
        elif '현금배당성향' in se and '연결' in se:
            try:
                val = float(thstrm.replace(',', ''))
                if val > 0:
                    r['배당성향'] = val
            except:
                pass

    # --- 주식수 ---
    for item in stock_data:
        se = item.get('se', '')
        if '보통주' in se:
            istc = item.get('istc_totqy', '')
            if istc and istc.strip() != '-':
                r['발행주식수'] = parse_num(istc)

    # --- 계산 ---
    r.setdefault('차입금_유동', 0)
    r.setdefault('차입금_비유동', 0)
    r['이자발생부채'] = r.get('차입금_유동', 0) + r.get('차입금_비유동', 0)

    if r.get('영업CF') is not None:
        r['FCF'] = r.get('영업CF', 0) - r.get('CAPEX', 0)

    if r.get('매출액') and r['매출액'] != 0:
        r['영업이익률'] = r.get('영업이익', 0) / r['매출액'] * 100
        r['순이익률'] = r.get('당기순이익', 0) / r['매출액'] * 100

    if r.get('자본_지배') and r['자본_지배'] != 0:
        r['ROE'] = r.get('순이익_지배', 0) / r['자본_지배'] * 100

    if r.get('자산총계') and r['자산총계'] != 0:
        r['ROA'] = r.get('당기순이익', 0) / r['자산총계'] * 100

    if r.get('자본총계') and r['자본총계'] != 0:
        r['부채비율'] = r.get('부채총계', 0) / r['자본총계'] * 100

    if capital and capital != 0:
        r['자본유보율'] = (r.get('자본_지배', 0) - capital) / capital * 100

    if r.get('발행주식수') and r['발행주식수'] != 0:
        if r.get('순이익_지배'):
            r['EPS'] = round(r['순이익_지배'] / r['발행주식수'])
        if r.get('자본_지배'):
            r['BPS'] = round(r['자본_지배'] / r['발행주식수'])

    return r


def get_yearend_prices(ticker, years):
    """yfinance로 각 연도 연말 종가 조회"""
    prices = {}
    stock = yf.Ticker(ticker)
    for y in years:
        try:
            # 연말 마지막 거래일 종가
            start = f'{y}-12-20'
            end = f'{y+1}-01-05'
            hist = stock.history(start=start, end=end)
            if not hist.empty:
                # 해당 연도 마지막 거래일
                year_data = hist[hist.index.year == y]
                if not year_data.empty:
                    prices[y] = int(year_data['Close'].iloc[-1])
        except:
            pass
    return prices


def calc_per_pbr(r, price):
    """연말종가로 PER/PBR 계산"""
    if price and r.get('EPS') and r['EPS'] > 0:
        r['PER'] = round(price / r['EPS'], 2)
    if price and r.get('BPS') and r['BPS'] > 0:
        r['PBR'] = round(price / r['BPS'], 2)


# ===== HTML 생성 =====
EOK = 100000000

def fmt_eok(v):
    if v is None: return '-'
    return str(round(v / EOK))

def fmt_pct(v, d=1):
    if v is None: return '-'
    return f'{v:.{d}f}'

def fmt_won(v):
    if v is None: return '-'
    return f'{v:,}'

def fmt_int(v):
    if v is None: return '-'
    return f'{v:,}'


ANNUAL_ITEMS = [
    ('매출액', lambda r: fmt_eok(r.get('매출액'))),
    ('영업이익', lambda r: fmt_eok(r.get('영업이익'))),
    ('영업이익(발표기준)', lambda r: fmt_eok(r.get('영업이익'))),
    ('세전계속사업이익', lambda r: fmt_eok(r.get('세전이익'))),
    ('당기순이익', lambda r: fmt_eok(r.get('당기순이익'))),
    ('당기순이익(지배)', lambda r: fmt_eok(r.get('순이익_지배'))),
    ('당기순이익(비지배)', lambda r: fmt_eok(r.get('순이익_비지배'))),
    ('자산총계', lambda r: fmt_eok(r.get('자산총계'))),
    ('부채총계', lambda r: fmt_eok(r.get('부채총계'))),
    ('자본총계', lambda r: fmt_eok(r.get('자본총계'))),
    ('자본총계(지배)', lambda r: fmt_eok(r.get('자본_지배'))),
    ('자본총계(비지배)', lambda r: fmt_eok(r.get('자본_비지배'))),
    ('자본금', lambda r: fmt_eok(r.get('자본금'))),
    ('영업활동현금흐름', lambda r: fmt_eok(r.get('영업CF'))),
    ('투자활동현금흐름', lambda r: fmt_eok(r.get('투자CF'))),
    ('재무활동현금흐름', lambda r: fmt_eok(r.get('재무CF'))),
    ('CAPEX', lambda r: fmt_eok(r.get('CAPEX'))),
    ('FCF', lambda r: fmt_eok(r.get('FCF'))),
    ('이자발생부채', lambda r: fmt_eok(r.get('이자발생부채'))),
    ('영업이익률', lambda r: fmt_pct(r.get('영업이익률'))),
    ('순이익률', lambda r: fmt_pct(r.get('순이익률'))),
    ('ROE(%)', lambda r: fmt_pct(r.get('ROE'))),
    ('ROA(%)', lambda r: fmt_pct(r.get('ROA'))),
    ('부채비율', lambda r: fmt_pct(r.get('부채비율'))),
    ('자본유보율', lambda r: fmt_pct(r.get('자본유보율'), 0)),
    ('EPS(원)', lambda r: fmt_won(r.get('EPS'))),
    ('PER(배)', lambda r: fmt_pct(r.get('PER'), 2)),
    ('BPS(원)', lambda r: fmt_won(r.get('BPS'))),
    ('PBR(배)', lambda r: fmt_pct(r.get('PBR'), 2)),
    ('현금DPS(원)', lambda r: fmt_won(r.get('DPS'))),
    ('현금배당수익률', lambda r: fmt_pct(r.get('배당수익률'))),
    ('현금배당성향(%)', lambda r: fmt_pct(r.get('배당성향'))),
    ('발행주식수(보통주)', lambda r: fmt_int(r.get('발행주식수'))),
]

QUARTER_ITEMS = [
    ('매출액', lambda r: fmt_eok(r.get('매출액'))),
    ('영업이익', lambda r: fmt_eok(r.get('영업이익'))),
    ('영업이익(발표기준)', lambda r: fmt_eok(r.get('영업이익'))),
    ('세전계속사업이익', lambda r: fmt_eok(r.get('세전이익'))),
    ('당기순이익', lambda r: fmt_eok(r.get('당기순이익'))),
    ('당기순이익(지배)', lambda r: fmt_eok(r.get('순이익_지배'))),
    ('당기순이익(비지배)', lambda r: fmt_eok(r.get('순이익_비지배'))),
    ('자산총계', lambda r: fmt_eok(r.get('자산총계'))),
    ('부채총계', lambda r: fmt_eok(r.get('부채총계'))),
    ('자본총계', lambda r: fmt_eok(r.get('자본총계'))),
    ('자본총계(지배)', lambda r: fmt_eok(r.get('자본_지배'))),
    ('자본총계(비지배)', lambda r: fmt_eok(r.get('자본_비지배'))),
    ('자본금', lambda r: fmt_eok(r.get('자본금'))),
    ('영업활동현금흐름', lambda r: fmt_eok(r.get('영업CF'))),
    ('투자활동현금흐름', lambda r: fmt_eok(r.get('투자CF'))),
    ('재무활동현금흐름', lambda r: fmt_eok(r.get('재무CF'))),
    ('CAPEX', lambda r: fmt_eok(r.get('CAPEX'))),
    ('FCF', lambda r: fmt_eok(r.get('FCF'))),
    ('이자발생부채', lambda r: fmt_eok(r.get('이자발생부채'))),
]


def build_html(results, col_labels, items, market_cap_eok=None):
    """완전한 HTML 문서 생성 (iframe용)"""
    col_w = 74.4186 / len(col_labels)
    table = '<table style="background-color: #ffffff; color: #3c3c3c; text-align: left; border-collapse: collapse; width: 100%; word-break: keep-all; overflow-wrap: normal;" border="1" data-ke-align="alignLeft" data-ke-style="style12">\n<tbody>\n'

    hdr_tr = 'style="background-color: #4a4a4a;"'
    hdr_td = 'font-weight: bold; color: #ffffff;'

    # 시가총액 행 (맨 위, 헤더 스타일)
    if market_cap_eok is not None:
        cap_str = f'{market_cap_eok:,}'
        table += f'<tr {hdr_tr}>\n'
        table += f'<td style="text-align: right; width: 25.5814%; {hdr_td}"><span style="color: #ffffff;">시가총액(억원)</span></td>\n'
        table += f'<td style="text-align: right; width: {col_w * len(col_labels):.4f}%; {hdr_td}" colspan="{len(col_labels)}"><span style="color: #ffffff;"><b>{cap_str}</b></span></td>\n'
        table += '</tr>\n'

    # Header
    table += f'<tr {hdr_tr}>\n'
    table += f'<td style="text-align: right; width: 25.5814%; {hdr_td}"><span style="color: #ffffff;">주요 재무 정보</span></td>\n'
    for label in col_labels:
        table += f'<td style="text-align: right; width: {col_w:.4f}%; {hdr_td}"><span style="color: #ffffff;">{label}</span></td>\n'
    table += '</tr>\n'

    # Data rows
    for row_label, formatter in items:
        table += '<tr>\n'
        table += f'<td style="text-align: right; width: 25.5814%;"><span style="color: #000000;">{row_label}</span></td>\n'
        for key in results:
            val = formatter(results[key])
            # 마이너스(-) 값은 빨간색 표시 (v4 규칙)
            if val.startswith('-') and val != '-':
                color = '#ff0000'
            else:
                color = '#000000'
            table += f'<td style="text-align: right; width: {74.4186/len(col_labels):.4f}%;"><span style="color: {color};">{val}</span></td>\n'
        table += '</tr>\n'

    table += '</tbody>\n</table>'

    # 시가총액 있으면 첫 2행, 없으면 첫 1행에 헤더 스타일 적용
    if market_cap_eok is not None:
        header_css = 'tr:nth-child(-n+2)'
    else:
        header_css = 'tr:first-child'

    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, 'Malgun Gothic', sans-serif; background: #fff; }}
  .table-wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
  table {{ font-size: 13px; word-break: keep-all; overflow-wrap: normal; }}
  td {{ padding: 4px 8px; border: 1px solid #ddd; white-space: nowrap; }}
  tr:nth-child(even) {{ background-color: #f9f9f9; }}
  {header_css} {{ background-color: #4a4a4a; }}
  {header_css} td {{ font-weight: bold; color: #ffffff; }}
</style>
</head>
<body>
<div class="table-wrap">
{table}
</div>
</body>
</html>'''
    return html


# ===== 메인 =====
def update_stock(stock_info, force=False):
    name = stock_info['name']
    corp_code = stock_info['corp_code']

    # 새 보고서 체크 (force=True면 무조건 갱신)
    if not force:
        print(f'[{name}] Checking for new reports...')
        if not check_new_reports(corp_code):
            print(f'[{name}] No new reports found. Skipping.')
            return False
        print(f'[{name}] New report detected!')

    now = datetime.now()
    cur_year = now.year

    # ===== 연간 (최근 5년) =====
    print(f'[{name}] Fetching annual data...')
    annual_results = {}
    annual_years = list(range(cur_year - 6, cur_year + 1))  # 넉넉히 7년 시도, 최근 5년만 사용

    for y in annual_years:
        print(f'  {y}...', end=' ')
        acnt, acnt_all, div_data, stock_data = fetch_year_data(corp_code, y, '11011')
        if not acnt and not acnt_all:
            print('no data')
            continue
        r = process_financial(acnt, acnt_all, div_data, stock_data, stock_info['capital'])
        if r.get('매출액'):
            annual_results[y] = r
            print('OK')
        else:
            print('no data')

    # 최근 5년만 유지
    if len(annual_results) > 5:
        keys = sorted(annual_results.keys())[-5:]
        annual_results = {k: annual_results[k] for k in keys}

    if not annual_results:
        print(f'[{name}] No annual data available.')
        return False

    # PER/PBR 계산 (yfinance 연말 종가)
    print(f'[{name}] Getting year-end prices for PER/PBR...')
    prices = get_yearend_prices(stock_info['ticker'], list(annual_results.keys()))
    for y, r in annual_results.items():
        calc_per_pbr(r, prices.get(y))

    # 실시간 시가총액 (현재가 x 발행주식수)
    market_cap_eok = None
    try:
        stock = yf.Ticker(stock_info['ticker'])
        cur_price = stock.history(period='1d')['Close'].iloc[-1]
        # 최신 연도의 발행주식수 사용
        latest_year = max(annual_results.keys())
        shares = annual_results[latest_year].get('발행주식수')
        if cur_price and shares:
            market_cap_eok = round(cur_price * shares / 100000000)
            print(f'[{name}] Market cap: {market_cap_eok:,} 억원')
    except Exception as e:
        print(f'[{name}] Market cap error: {e}')

    # 연간 HTML 생성
    col_labels = [f'{y}/12' for y in annual_results.keys()]
    annual_html = build_html(annual_results, col_labels, ANNUAL_ITEMS, market_cap_eok)
    annual_path = os.path.join(BASE, stock_info['annual_file'])
    with open(annual_path, 'w', encoding='utf-8') as f:
        f.write(annual_html)
    print(f'[{name}] Annual: {stock_info["annual_file"]}')

    # ===== 분기 (최근 5분기) =====
    print(f'[{name}] Fetching quarterly data...')
    quarter_results = {}
    # 보고서코드: 11013=1Q, 11012=2Q(반기), 11014=3Q, 11011=4Q(사업보고서)
    quarter_codes = [
        ('11013', 'Q1'), ('11012', 'Q2'), ('11014', 'Q3'), ('11011', 'Q4'),
    ]

    # 최근 5분기 역순 탐색
    quarters_found = []
    for check_year in range(cur_year, cur_year - 3, -1):
        for reprt_code, q_label in reversed(quarter_codes):
            if len(quarters_found) >= 5:
                break
            key = f'{check_year}/{q_label}'
            print(f'  {key}...', end=' ')
            acnt, acnt_all, div_data, stock_data = fetch_year_data(corp_code, check_year, reprt_code)
            if not acnt and not acnt_all:
                print('no data')
                continue
            r = process_financial(acnt, acnt_all, div_data, stock_data, stock_info['capital'])
            if r.get('매출액'):
                quarters_found.append((key, r))
                print('OK')
            else:
                print('no data')
        if len(quarters_found) >= 5:
            break

    if quarters_found:
        # 시간 순으로 정렬
        quarters_found.reverse()
        for key, r in quarters_found:
            quarter_results[key] = r

        col_labels_q = list(quarter_results.keys())
        quarter_html = build_html(quarter_results, col_labels_q, QUARTER_ITEMS, market_cap_eok)
        quarter_path = os.path.join(BASE, stock_info['quarter_file'])
        with open(quarter_path, 'w', encoding='utf-8') as f:
            f.write(quarter_html)
        print(f'[{name}] Quarterly: {stock_info["quarter_file"]}')

    return True


if __name__ == '__main__':
    if not DART_KEY:
        # 로컬 실행 시 직접 지정
        DART_KEY = os.environ.get('DART_API_KEY', '')
        if not DART_KEY:
            print('ERROR: DART_API_KEY not set')
            sys.exit(1)

    force = '--force' in sys.argv
    # --only 필터: 특정 종목만 실행 (예: --only pixelplus,qualitas)
    only_filter = None
    for arg in sys.argv:
        if arg.startswith('--only='):
            only_filter = [x.strip() for x in arg.split('=')[1].split(',')]
    for s in STOCKS:
        if only_filter:
            # annual_file에서 회사 키 추출하여 필터
            key = s['annual_file'].replace('_financial.html', '')
            if key not in only_filter:
                continue
        update_stock(s, force=force)
    print('Done.')
