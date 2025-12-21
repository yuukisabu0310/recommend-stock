import re, shutil, pathlib
p = pathlib.Path('src/data_fetcher.py')
text = p.read_text(encoding='utf-8')
shutil.copyfile(p, p.with_suffix('.py.bak3'))

# --- long_term_rate_history ---
if 'long_term_rate_history' not in text:
    m = re.search(r"(?m)^(\s*)long_term_rate\s*=\s*None\s*$", text)
    if not m:
        raise SystemExit('ERROR: long_term_rate = None not found')
    ind = m.group(1)
    text = re.sub(r"(?m)^"+re.escape(ind)+r"long_term_rate\s*=\s*None\s*$",
                  ind+"long_term_rate = None\n"+ind+"long_term_rate_history = None  # chart-only (6mo)",
                  text, count=1)

    fred_line = '            long_term_rate = self._get_fred_data(fred_series["US"]["long_term_rate"], country_code)\n'
    if fred_line not in text:
        raise SystemExit('ERROR: US long_term_rate FRED line not found')
    insert = fred_line + (
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
    )
    text = text.replace(fred_line, insert)

    anchor = '                    logger.warning(f"髟ｷ譛滄≡蛻ｩ蜿門ｾ励お繝ｩ繝ｼ (yfinance, {country_code}): {e}")\n'
    if anchor in text:
        text = text.replace(anchor, anchor +
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
        )

    text, n = re.subn(r"(\s*\"long_term_rate\"\s*:\s*long_term_rate,\n)", r"\1            \"long_term_rate_history\": long_term_rate_history,\n", text, count=1)
    if n != 1:
        raise SystemExit('ERROR: could not add long_term_rate_history to result dict')

# --- CPI_history ---
if 'CPI_history' not in text:
    text, n = re.subn(r"(?m)^(\s*)cpi\s*=\s*None\s*$", r"\1cpi = None\n\1cpi_history = None  # chart-only (YoY monthly)", text, count=1)
    if n != 1:
        raise SystemExit('ERROR: could not declare cpi_history')

    err_line = '                        logger.error(f"CPI險育ｮ励お繝ｩ繝ｼ ({country_code}): {e}")\n'
    if err_line not in text:
        raise SystemExit('ERROR: CPI calculation error log line not found')
    text = text.replace(err_line, err_line +
        "\n                        # chart-only: YoY history (>=12 months)\n"
        "                        try:\n"
        "                            levels = self.fred_client.get_series(fred_series[\"US\"][\"CPI\"], limit=25)\n"
        "                            if len(levels) >= 25:\n"
        "                                yoy_points = []\n"
        "                                for i in range(12, len(levels)):\n"
        "                                    cur = float(levels.iloc[i])\n"
        "                                    prev = float(levels.iloc[i - 12])\n"
        "                                    yoy = ((cur / prev) - 1) * 100\n"
        "                                    dt = levels.index[i].strftime('%Y-%m-%d')\n"
        "                                    yoy_points.append({\"date\": dt, \"value\": yoy})\n"
        "                                cpi_history = yoy_points[-12:] if len(yoy_points) >= 12 else yoy_points\n"
        "                        except Exception as e:\n"
        "                            logger.warning(f\"CPI history error ({country_code}): {e}\")\n"
    )

    text, n = re.subn(r"(\s*\"CPI\"\s*:\s*cpi,\n)", r"\1            \"CPI_history\": cpi_history,\n", text, count=1)
    if n != 1:
        raise SystemExit('ERROR: could not add CPI_history to result dict')

p.write_text(text, encoding='utf-8')
print('OK')
