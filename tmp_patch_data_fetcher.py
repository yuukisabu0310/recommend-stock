import re, shutil, pathlib
p = pathlib.Path('src/data_fetcher.py')
text = p.read_text(encoding='utf-8')
shutil.copyfile(p, p.with_suffix('.py.bak'))

if 'import math' not in text:
    text = text.replace('import time\n', 'import time\nimport math\n')

# Replace the 30-day block (hist_tail...) with 6-month + MA series block
pat = re.compile(
    r"(?P<indent>\s*)hist_tail\s*=\s*hist\.tail\(30\)\n"
    r"(?P=indent)historical_prices\s*=\s*hist_tail\['Close'\]\.tolist\(\)\n"
    r"(?P=indent)historical_dates\s*=\s*\[date\.strftime\('%Y-%m-%d'\)\s*for\s*date\s*in\s*hist_tail\.index\]\n"
)

def repl(m):
    ind = m.group('indent')
    return (
        f"{ind}# 繝√Ε繝ｼ繝育畑縺ｮ譎らｳｻ蛻励ョ繝ｼ繧ｿ・育峩霑・縺区怦・噂n"
        f"{ind}# 窶ｻ蛻､譁ｭ繝ｭ繧ｸ繝・け縺ｯ latest_price / MA / volatility 遲峨・縲取怙譁ｰ蛟､縲上ｒ菴ｿ逕ｨ・亥､画峩遖∵ｭ｢・噂n"
        f"{ind}try:\n"
        f"{ind}    chart_start = hist.index[-1] - timedelta(days=183)\n"
        f"{ind}    chart_hist = hist.loc[hist.index >= chart_start]\n"
        f"{ind}    if chart_hist.empty:\n"
        f"{ind}        chart_hist = hist.tail(30)\n"
        f"{ind}except Exception:\n"
        f"{ind}    chart_hist = hist.tail(30)\n\n"
        f"{ind}historical_dates = [d.strftime('%Y-%m-%d') for d in chart_hist.index]\n"
        f"{ind}historical_prices = [float(x) for x in chart_hist['Close'].tolist()]\n\n"
        f"{ind}# 繝√Ε繝ｼ繝育畑縺ｮ遘ｻ蜍募ｹｳ蝮・ｼ域凾邉ｻ蛻暦ｼ噂n"
        f"{ind}# full series縺ｧrolling繧定ｨ育ｮ励＠縲√メ繝｣繝ｼ繝域悄髢薙↓繧ｹ繝ｩ繧､繧ｹ縺吶ｋ・・A縺檎峩邱壹↓縺ｪ繧倶ｸ榊・蜷医ｒ蝗樣∩・噂n"
        f"{ind}ma20_series_full = hist['Close'].rolling(window=20).mean()\n"
        f"{ind}ma75_series_full = hist['Close'].rolling(window=75).mean()\n"
        f"{ind}ma200_series_full = hist['Close'].rolling(window=200).mean()\n\n"
        f"{ind}def _to_float_or_none(v):\n"
        f"{ind}    try:\n"
        f"{ind}        if v is None:\n"
        f"{ind}            return None\n"
        f"{ind}        fv = float(v)\n"
        f"{ind}        return None if math.isnan(fv) else fv\n"
        f"{ind}    except Exception:\n"
        f"{ind}        return None\n\n"
        f"{ind}historical_ma20 = [_to_float_or_none(v) for v in ma20_series_full.loc[chart_hist.index].tolist()]\n"
        f"{ind}historical_ma75 = [_to_float_or_none(v) for v in ma75_series_full.loc[chart_hist.index].tolist()]\n"
        f"{ind}historical_ma200 = [_to_float_or_none(v) for v in ma200_series_full.loc[chart_hist.index].tolist()]\n"
    )

text, n = pat.subn(repl, text, count=1)
if n != 1:
    raise SystemExit(f'ERROR: hist_tail block replacement count={n}')

# Replace historical fields in dict (first occurrence)
pattern = re.compile(
    r'\s+"historical_prices":\s*historical_prices,\s*#.*\n\s+"historical_dates":\s*historical_dates\s*#.*\n',
    re.MULTILINE
)
replacement = (
"                # logs繝√Ε繝ｼ繝育畑・域凾邉ｻ蛻暦ｼ噂n"
"                \"historical_prices\": historical_prices,   # 逶ｴ霑・縺区怦縺ｮ邨ょ､\n"
"                \"historical_dates\": historical_dates,     # 逶ｴ霑・縺区怦縺ｮ譌･莉假ｼ・yyy-mm-dd蠖｢蠑擾ｼ噂n"
"                \"historical_ma20\": historical_ma20,\n"
"                \"historical_ma75\": historical_ma75,\n"
"                \"historical_ma200\": historical_ma200\n"
)
text, n2 = pattern.subn(replacement, text, count=1)
if n2 != 1:
    raise SystemExit(f'ERROR: historical field replacement count={n2}')

p.write_text(text, encoding='utf-8')
print('OK')
