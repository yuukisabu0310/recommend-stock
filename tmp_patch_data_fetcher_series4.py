import re, shutil, pathlib
p = pathlib.Path('src/data_fetcher.py')
text = p.read_text(encoding='utf-8')
shutil.copyfile(p, p.with_suffix('.py.bak4'))

# Ensure import math exists
if '\nimport math\n' not in text:
    text = text.replace('import time\n', 'import time\nimport math\n')

# ---- long_term_rate_history ----
if 'long_term_rate_history' not in text:
    # declare after first long_term_rate = None
    text, n = re.subn(r"(?m)^(\s*)long_term_rate\s*=\s*None\s*$", r"\1long_term_rate = None\n\1long_term_rate_history = None  # chart-only (6mo)", text, count=1)
    if n != 1:
        raise SystemExit('ERROR: declare long_term_rate_history failed')

    # insert US FRED history right after the US latest FRED fetch
    us_fetch = '            long_term_rate = self._get_fred_data(fred_series["US"]["long_term_rate"], country_code)\n'
    if us_fetch not in text:
        raise SystemExit('ERROR: US long_term_rate FRED fetch line not found')
    text = text.replace(us_fetch, us_fetch + (
        "            # chart-only: 6mo history (FRED)\n"
        "            if self.fred_client:\n"
        "                try:\n"
        "                    start = (datetime.now() - timedelta(days=183)).strftime('%Y-%m-%d')\n"
        "                    series = self.fred_client.get_series(fred_series[\"US\"][\"long_term_rate\"], observation_start=start)\n"
        "                    if not series.empty:\n"
        "                        pts = []\n"
        "                        for dt, val in series.items():\n"
        "                            try:\n"
        "                                fv = float(val)\n"
        "                                if math.isnan(fv):\n"
        "                                    continue\n"
        "                                pts.append({\"date\": dt.strftime('%Y-%m-%d'), \"value\": fv})\n"
        "                            except Exception:\n"
        "                                continue\n"
        "                        long_term_rate_history = pts if len(pts) >= 2 else None\n"
        "                except Exception as e:\n"
        "                    logger.warning(f\"Long-term rate history error (FRED, {country_code}): {e}\")\n"
    ))

    # yfinance fallback history (after yfinance latest fetch block if present)
    # insert near the end of US long_term_rate section by locating the string '^TNX'
    if '^TNX' in text:
        # Insert once after the yfinance 5d fetch block end (logger.warning for yfinance fetch)
        yfetch_anchor = re.search(r"logger\.warning\(f\"髟ｷ譛滄≡蛻ｩ蜿門ｾ励お繝ｩ繝ｼ \(yfinance, \{country_code\}\): \{e\}\"\)\n", text)
        if yfetch_anchor:
            pos = yfetch_anchor.end()
            text = text[:pos] + (
                "            # chart-only: 6mo history (yfinance fallback)\n"
                "            if long_term_rate_history is None and yf:\n"
                "                try:\n"
                "                    rate_stock = yf.Ticker(\"^TNX\")\n"
                "                    hist6 = rate_stock.history(period=\"6mo\")\n"
                "                    if not hist6.empty:\n"
                "                        pts = []\n"
                "                        for dt, val in hist6['Close'].items():\n"
                "                            try:\n"
                "                                pts.append({\"date\": dt.strftime('%Y-%m-%d'), \"value\": float(val)})\n"
                "                            except Exception:\n"
                "                                continue\n"
                "                        long_term_rate_history = pts if len(pts) >= 2 else None\n"
                "                except Exception as e:\n"
                "                    logger.warning(f\"Long-term rate history error (yfinance, {country_code}): {e}\")\n"
            ) + text[pos:]

    # add to result dict
    text, n = re.subn(r"(\s*\"long_term_rate\"\s*:\s*long_term_rate,\n)", r"\1            \"long_term_rate_history\": long_term_rate_history,\n", text, count=1)
    if n != 1:
        raise SystemExit('ERROR: add long_term_rate_history to result failed')

# ---- CPI_history ----
if 'CPI_history' not in text:
    text, n = re.subn(r"(?m)^(\s*)cpi\s*=\s*None\s*$", r"\1cpi = None\n\1cpi_history = None  # chart-only (YoY monthly)", text, count=1)
    if n != 1:
        raise SystemExit('ERROR: declare cpi_history failed')

    # Insert YoY history after the CPI calculation error log line (mojibake-safe regex)
    m = re.search(r"(?m)^(\s*)logger\.error\(f\"CPI.*\{e\}\"\)\s*$", text)
    if not m:
        raise SystemExit('ERROR: CPI calc error logger line not found')
    ind = m.group(1)
    insert_block = (
        "\n" + ind + "# chart-only: YoY history (>=12 months)\n" +
        ind + "try:\n" +
        ind + "    levels = self.fred_client.get_series(fred_series[\"US\"][\"CPI\"], limit=25)\n" +
        ind + "    if len(levels) >= 25:\n" +
        ind + "        yoy_points = []\n" +
        ind + "        for i in range(12, len(levels)):\n" +
        ind + "            cur = float(levels.iloc[i])\n" +
        ind + "            prev = float(levels.iloc[i - 12])\n" +
        ind + "            yoy = ((cur / prev) - 1) * 100\n" +
        ind + "            dt = levels.index[i].strftime('%Y-%m-%d')\n" +
        ind + "            yoy_points.append({\"date\": dt, \"value\": yoy})\n" +
        ind + "        cpi_history = yoy_points[-12:] if len(yoy_points) >= 12 else yoy_points\n" +
        ind + "except Exception as e:\n" +
        ind + "    logger.warning(f\"CPI history error ({country_code}): {e}\")\n"
    )
    # Insert right after the matched line
    pos = m.end()
    text = text[:pos] + insert_block + text[pos:]

    text, n = re.subn(r"(\s*\"CPI\"\s*:\s*cpi,\n)", r"\1            \"CPI_history\": cpi_history,\n", text, count=1)
    if n != 1:
        raise SystemExit('ERROR: add CPI_history to result failed')

p.write_text(text, encoding='utf-8')
print('OK')
