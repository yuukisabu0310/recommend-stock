import re, shutil, pathlib
p = pathlib.Path('src/data_fetcher.py')
text = p.read_text(encoding='utf-8')
shutil.copyfile(p, p.with_suffix('.py.bak2'))

# --- financial: add long_term_rate_history ---
if 'long_term_rate_history' not in text:
    # declare variable
    text, n = re.subn(r"(\s*# 髟ｷ譛滄≡蛻ｩ: FRED API縺ｾ縺溘・yfinance縺九ｉ蜿門ｾ予n\s*long_term_rate = None\n)", r"\1        long_term_rate_history = None  # 繝√Ε繝ｼ繝育畑・育峩霑・縺区怦・噂n", text, count=1)
    if n != 1:
        raise SystemExit('ERROR: could not insert long_term_rate_history declaration')

    # US: after FRED fetch, add history fetch
    us_pat = r"(\s*# FRED API縺九ｉ蜿門ｾ予n\s*long_term_rate = self\._get_fred_data\(fred_series\[\"US\"\]\[\"long_term_rate\"\], country_code\)\n)"
    us_ins = (
        "\\1"
        "            # 繝√Ε繝ｼ繝育畑・夂峩霑・縺区怦縺ｮ譎らｳｻ蛻暦ｼ・RED・噂\n"
        "            if self.fred_client:\\n"
        "                try:\\n"
        "                    start = (datetime.now() - timedelta(days=183)).strftime('\\%Y-\\%m-\\%d')\\n"
        "                    series = self.fred_client.get_series(fred_series[\\\"US\\\"][\\\"long_term_rate\\\"], observation_start=start)\\n"
        "                    if not series.empty:\\n"
        "                        pts = []\\n"
        "                        for dt, val in series.items():\\n"
        "                            try:\\n"
        "                                fv = float(val)\\n"
        "                                if math.isnan(fv):\\n"
        "                                    continue\\n"
        "                                pts.append({\\\"date\\\": dt.strftime('\\%Y-\\%m-\\%d'), \\\"value\\\": fv})\\n"
        "                            except Exception:\\n"
        "                                continue\\n"
        "                        long_term_rate_history = pts if len(pts) >= 2 else None\\n"
        "                except Exception as e:\\n"
        "                    logger.warning(f\\\"髟ｷ譛滄≡蛻ｩ譎らｳｻ蛻怜叙蠕励お繝ｩ繝ｼ (FRED, {country_code}): {e}\\\")\\n"
    )
    text, n = re.subn(us_pat, us_ins, text, count=1)
    if n != 1:
        raise SystemExit('ERROR: could not insert US long_term_rate_history fetch')

    # yfinance fallback history if still None
    yf_pat = r"(\s*# FRED API縺悟､ｱ謨励＠縺溷ｴ蜷医・yfinance縺九ｉ蜿門ｾ予n\s*if long_term_rate is None and yf:\n\s*try:\n\s*rate_stock = yf\.Ticker\(\"\^TNX\"\)[\s\S]*?except Exception as e:\n\s*logger\.warning\(f\"髟ｷ譛滄≡蛻ｩ蜿門ｾ励お繝ｩ繝ｼ \(yfinance, \{country_code\}\): \{e\}\"\)\n)"
    # insert after that block
    text, n = re.subn(yf_pat, r"\1            # 繝√Ε繝ｼ繝育畑・夂峩霑・縺区怦縺ｮ譎らｳｻ蛻暦ｼ・finance繝輔か繝ｼ繝ｫ繝舌ャ繧ｯ・噂n            if long_term_rate_history is None and yf:\n                try:\n                    rate_stock = yf.Ticker(\"^TNX\")\n                    hist6 = rate_stock.history(period=\"6mo\")\n                    if not hist6.empty:\n                        pts = []\n                        for dt, val in hist6['Close'].items():\n                            try:\n                                pts.append({\"date\": dt.strftime('%Y-%m-%d'), \"value\": float(val)})\n                            except Exception:\n                                continue\n                        long_term_rate_history = pts if len(pts) >= 2 else None\n                except Exception as e:\n                    logger.warning(f\"髟ｷ譛滄≡蛻ｩ譎らｳｻ蛻怜叙蠕励お繝ｩ繝ｼ (yfinance, {country_code}): {e}\")\n", text, count=1)
    if n != 1:
        raise SystemExit('ERROR: could not insert yfinance long_term_rate_history fallback')

    # add to result dict
    text, n = re.subn(r"(\s*\"long_term_rate\": long_term_rate,\n)", r"\1            # logs繝√Ε繝ｼ繝育畑・亥愛譁ｭ繝ｭ繧ｸ繝・け縺ｫ縺ｯ荳堺ｽｿ逕ｨ・噂n            \"long_term_rate_history\": long_term_rate_history,\n", text, count=1)
    if n != 1:
        raise SystemExit('ERROR: could not add long_term_rate_history to result')

# --- macro: add CPI_history ---
if 'CPI_history' not in text:
    text, n = re.subn(r"(\s*# CPI: FRED API縺九ｉ蜿門ｾ予n\s*cpi = None\n)", r"\1        cpi_history = None  # 繝√Ε繝ｼ繝育畑・亥燕蟷ｴ豈・縲∵怦谺｡・噂n", text, count=1)
    if n != 1:
        raise SystemExit('ERROR: could not declare cpi_history')

    # US: insert history fetch after CPI險育ｮ葉ry/except block close (after logger.error CPI險育ｮ励お繝ｩ繝ｼ...)
    anchor = "                        logger.error(f\"CPI險育ｮ励お繝ｩ繝ｼ ({country_code}): {e}\")\n"
    if anchor not in text:
        raise SystemExit('ERROR: CPI險育ｮ励お繝ｩ繝ｼ anchor not found')
    insert = (
        anchor +
        "\n                        # 繝√Ε繝ｼ繝育畑・壼燕蟷ｴ豈斐・譎らｳｻ蛻暦ｼ域怙菴・2縺区怦・噂n"
        "                        try:\n"
        "                            levels = self.fred_client.get_series(fred_series[\"US\"][\"CPI\"], limit=25)\n"
        "                            if len(levels) >= 25:\n"
        "                                yoy_points = []\n"
        "                                for i in range(12, len(levels)):\n"
        "                                    cur = float(levels.iloc[i])\n"
        "                                    prev = float(levels.iloc[i - 12])\n"
        "                                    yoy = ((cur / prev) - 1) * 100\n"
        "                                    dt = levels.index[i].strftime(\"%Y-%m-%d\")\n"
        "                                    yoy_points.append({\"date\": dt, \"value\": yoy})\n"
        "                                cpi_history = yoy_points[-12:] if len(yoy_points) >= 12 else yoy_points\n"
        "                        except Exception as e:\n"
        "                            logger.warning(f\"CPI譎らｳｻ蛻怜叙蠕励お繝ｩ繝ｼ ({country_code}): {e}\")\n"
    )
    text = text.replace(anchor, insert)

    # add to result dict
    text, n = re.subn(r"(\s*\"CPI\": cpi,\n)", r"\1            # logs繝√Ε繝ｼ繝育畑・亥愛譁ｭ繝ｭ繧ｸ繝・け縺ｫ縺ｯ荳堺ｽｿ逕ｨ・噂n            \"CPI_history\": cpi_history,\n", text, count=1)
    if n != 1:
        raise SystemExit('ERROR: could not add CPI_history to result')

p.write_text(text, encoding='utf-8')
print('OK')
