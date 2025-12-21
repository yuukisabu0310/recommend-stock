import pathlib, re, shutil
p = pathlib.Path('src/html_generator.py')
text = p.read_text(encoding='utf-8')
shutil.copyfile(p, p.with_suffix('.py.bak_charts2'))

# Replace MA scalar getters with historical arrays (only in chart scripts area)
text = text.replace('            ma20 = first_index.get("ma20", 0)\n            ma75 = first_index.get("ma75", 0)\n            ma200 = first_index.get("ma200", 0)\n',
                    '            historical_ma20 = first_index.get("historical_ma20", [])\n            historical_ma75 = first_index.get("historical_ma75", [])\n            historical_ma200 = first_index.get("historical_ma200", [])\n')

# Insert ma*_js after prices_js
if 'ma20_js' not in text:
    text = text.replace('                prices_js = json.dumps(prices_data, ensure_ascii=False)\n',
                        '                prices_js = json.dumps(prices_data, ensure_ascii=False)\n                ma20_js = json.dumps(historical_ma20 if len(historical_ma20) == len(prices_data) else [None] * len(prices_data), ensure_ascii=False)\n                ma75_js = json.dumps(historical_ma75 if len(historical_ma75) == len(prices_data) else [None] * len(prices_data), ensure_ascii=False)\n                ma200_js = json.dumps(historical_ma200 if len(historical_ma200) == len(prices_data) else [None] * len(prices_data), ensure_ascii=False)\n')

# Replace Array(fill(...)) with ma*_js (f-string placeholders)
text = re.sub(r"data: Array\(\{len\(prices_data\)\}\)\.fill\(\{ma20\}\)", "data: {ma20_js}", text)
text = re.sub(r"data: Array\(\{len\(prices_data\)\}\)\.fill\(\{ma75\}\)", "data: {ma75_js}", text)
text = re.sub(r"data: Array\(\{len\(prices_data\)\}\)\.fill\(\{ma200\}\)", "data: {ma200_js}", text)

# Conditionally show canvases for rate/CPI in HTML blocks by inserting has_* flags and canvas
# This is a targeted replace using the existing chart_id lines as anchors.
text = text.replace('chart_id = f"rateChart_{country_code}_{timeframe_code}"\n                html += f"""',
                    'chart_id = f"rateChart_{country_code}_{timeframe_code}"\n                has_rate_ts = bool(financial.get("long_term_rate_history"))\n                html += f"""')
text = text.replace('<h3 class="text-lg font-semibold text-gray-900 mb-2">髟ｷ譛滄≡蛻ｩ・・0蟷ｴ蛯ｵ・・/h3>\n                        <div class="bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded mb-3">',
                    '<h3 class="text-lg font-semibold text-gray-900 mb-2">髟ｷ譛滄≡蛻ｩ・・0蟷ｴ蛯ｵ・・/h3>\n"""\n                if not has_rate_ts:\n                    html += """\n                        <div class="bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded mb-3">')
# add canvas after note block close for rate
text = text.replace('</div>\n                        <div class="mt-3 pt-3 border-t border-gray-200">',
                    '</div>\n"""\n                else:\n                    html += f"""\n                        <canvas id="{chart_id}"></canvas>\n"""\n                html += f"""\n                        <div class="mt-3 pt-3 border-t border-gray-200">', 1)
# period label update for rate
text = text.replace('譛滄俣・・/span>逶ｴ霑・縺区怦・域悴蟇ｾ蠢懶ｼ・, '譛滄俣・・/span>逶ｴ霑・縺区怦{\'\' if has_rate_ts else \'・域悴蟇ｾ蠢懶ｼ噂'}')

# CPI similar
text = text.replace('chart_id = f"cpiChart_{country_code}_{timeframe_code}"\n                html += f"""',
                    'chart_id = f"cpiChart_{country_code}_{timeframe_code}"\n                has_cpi_ts = bool(macro.get("CPI_history"))\n                html += f"""')
text = text.replace('<h3 class="text-lg font-semibold text-gray-900 mb-2">CPI・域ｶ郁ｲｻ閠・黄萓｡謖・焚・・/h3>\n                        <div class="bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded mb-3">',
                    '<h3 class="text-lg font-semibold text-gray-900 mb-2">CPI・域ｶ郁ｲｻ閠・黄萓｡謖・焚・・/h3>\n"""\n                if not has_cpi_ts:\n                    html += """\n                        <div class="bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded mb-3">')
text = text.replace('</div>\n                        <div class="mt-3 pt-3 border-t border-gray-200">',
                    '</div>\n"""\n                else:\n                    html += f"""\n                        <canvas id="{chart_id}"></canvas>\n"""\n                html += f"""\n                        <div class="mt-3 pt-3 border-t border-gray-200">', 1)
text = text.replace('譛滄俣・・/span>逶ｴ霑・2縺区怦・域悴蟇ｾ蠢懶ｼ・, '譛滄俣・・/span>逶ｴ霑・2縺区怦{\'\' if has_cpi_ts else \'・域悴蟇ｾ蠢懶ｼ噂'}')

# Add rate/CPI scripts if not present (ASCII anchor)
if 'rate_history = financial.get("long_term_rate_history")' not in text:
    marker = '        scripts += """\n            </script>\n"""'
    idx = text.find(marker)
    if idx == -1:
        raise SystemExit('ERROR: script closing marker not found')
    extra = (
        "\n        # rate chart (chart-only)\n"
        "        financial = data.get(\"financial\", {}) if isinstance(data.get(\"financial\", {}), dict) else {}\n"
        "        rate_history = financial.get(\"long_term_rate_history\")\n"
        "        if timeframe_code == \"short\" and isinstance(rate_history, list) and len(rate_history) >= 2:\n"
        "            rate_labels = [p.get(\"date\") for p in rate_history if p.get(\"date\") and p.get(\"value\") is not None]\n"
        "            rate_values = [p.get(\"value\") for p in rate_history if p.get(\"date\") and p.get(\"value\") is not None]\n"
        "            if len(rate_labels) == len(rate_values) and len(rate_labels) >= 2:\n"
        "                chart_id = f\"rateChart_{country_code}_{timeframe_code}\"\n"
        "                scripts += f\"\"\"\n"
        "                // rate chart\n"
        "                const ctx_{chart_id.replace('-', '_')} = document.getElementById('{chart_id}');\n"
        "                if (ctx_{chart_id.replace('-', '_')}) {{\n"
        "                    new Chart(ctx_{chart_id.replace('-', '_')}, {{\n"
        "                        type: 'line',\n"
        "                        data: {{\n"
        "                            labels: {json.dumps(rate_labels, ensure_ascii=False)},\n"
        "                            datasets: [{{\n"
        "                                label: '10Y',\n"
        "                                data: {json.dumps(rate_values, ensure_ascii=False)},\n"
        "                                borderColor: 'rgb(239, 68, 68)',\n"
        "                                backgroundColor: 'rgba(239, 68, 68, 0.1)',\n"
        "                                tension: 0.1,\n"
        "                                pointRadius: 0\n"
        "                            }}]\n"
        "                        }},\n"
        "                        options: {{\n"
        "                            responsive: true,\n"
        "                            maintainAspectRatio: true,\n"
        "                            plugins: {{\n"
        "                                legend: {{ display: true, position: 'top' }},\n"
        "                                tooltip: {{ mode: 'index', intersect: false }}\n"
        "                            }},\n"
        "                            scales: {{\n"
        "                                x: {{ ticks: {{ maxRotation: 45, minRotation: 45 }} }},\n"
        "                                y: {{ beginAtZero: false }}\n"
        "                            }}\n"
        "                        }}\n"
        "                    }});\n"
        "                }}\n"
        "                \"\"\"\n"
        "\n        # cpi chart (chart-only)\n"
        "        macro = data.get(\"macro\", {}) if isinstance(data.get(\"macro\", {}), dict) else {}\n"
        "        cpi_history = macro.get(\"CPI_history\")\n"
        "        if timeframe_code == \"short\" and isinstance(cpi_history, list) and len(cpi_history) >= 2:\n"
        "            cpi_labels = [p.get(\"date\") for p in cpi_history if p.get(\"date\") and p.get(\"value\") is not None]\n"
        "            cpi_values = [p.get(\"value\") for p in cpi_history if p.get(\"date\") and p.get(\"value\") is not None]\n"
        "            if len(cpi_labels) == len(cpi_values) and len(cpi_labels) >= 2:\n"
        "                chart_id = f\"cpiChart_{country_code}_{timeframe_code}\"\n"
        "                scripts += f\"\"\"\n"
        "                // cpi chart\n"
        "                const ctx_{chart_id.replace('-', '_')} = document.getElementById('{chart_id}');\n"
        "                if (ctx_{chart_id.replace('-', '_')}) {{\n"
        "                    new Chart(ctx_{chart_id.replace('-', '_')}, {{\n"
        "                        type: 'line',\n"
        "                        data: {{\n"
        "                            labels: {json.dumps(cpi_labels, ensure_ascii=False)},\n"
        "                            datasets: [{{\n"
        "                                label: 'CPI YoY (%)',\n"
        "                                data: {json.dumps(cpi_values, ensure_ascii=False)},\n"
        "                                borderColor: 'rgb(59, 130, 246)',\n"
        "                                backgroundColor: 'rgba(59, 130, 246, 0.1)',\n"
        "                                tension: 0.1,\n"
        "                                pointRadius: 2,\n"
        "                                pointHoverRadius: 4\n"
        "                            }}]\n"
        "                        }},\n"
        "                        options: {{\n"
        "                            responsive: true,\n"
        "                            maintainAspectRatio: true,\n"
        "                            plugins: {{\n"
        "                                legend: {{ display: true, position: 'top' }},\n"
        "                                tooltip: {{ mode: 'index', intersect: false }}\n"
        "                            }},\n"
        "                            scales: {{\n"
        "                                x: {{ ticks: {{ maxRotation: 45, minRotation: 45 }} }},\n"
        "                                y: {{ beginAtZero: false }}\n"
        "                            }}\n"
        "                        }}\n"
        "                    }});\n"
        "                }}\n"
        "                \"\"\"\n"
    )
    text = text[:idx] + extra + text[idx:]

p.write_text(text, encoding='utf-8')
print('OK')
