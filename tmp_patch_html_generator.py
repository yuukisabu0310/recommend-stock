import pathlib, re, shutil
p = pathlib.Path('src/html_generator.py')
text = p.read_text(encoding='utf-8')
shutil.copyfile(p, p.with_suffix('.py.bak_charts'))

# --- Update chart HTML blocks: add canvas only when history exists ---
# Long-term rate block
rate_start = '            if financial.get("long_term_rate") is not None:'
if rate_start in text:
    # Replace the whole existing f-string block for rate with a conditional-canvas version
    pattern = re.compile(r"\n\s*if financial\.get\(\"long_term_rate\"\) is not None:[\s\S]*?\n\s*\"\"\"\n", re.MULTILINE)
    # We will only replace the first occurrence inside the short timeframe section
    def repl_rate(m):
        block = m.group(0)
        # Ensure this is the short timeframe block by checking it contains rateChart_
        if 'rateChart_' not in block:
            return block
        # Build new block (keep existing HTML but insert canvas conditionally)
        return (
            "\n            if financial.get(\"long_term_rate\") is not None:\n"
            "                rate = financial.get(\"long_term_rate\")\n"
            "                chart_id = f\"rateChart_{country_code}_{timeframe_code}\"\n"
            "                has_rate_ts = bool(financial.get(\"long_term_rate_history\"))\n"
            "                html += f\"\"\"\n"
            "                    <div class=\"bg-gray-50 p-4 rounded-lg\">\n"
            "                        <h3 class=\"text-lg font-semibold text-gray-900 mb-2\">髟ｷ譛滄≡蛻ｩ・・0蟷ｴ蛯ｵ・・/h3>\n"
            "\"\"\"\n"
            "                if not has_rate_ts:\n"
            "                    html += \"\"\"\n"
            "                        <div class=\"bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded mb-3\">\n"
            "                            <p class=\"text-xs text-yellow-800\">\n"
            "                                窶ｻ 迴ｾ蝨ｨ縺ｯ譛譁ｰ蛟､縺ｮ縺ｿ蜿門ｾ励＠縺ｦ縺翫ｊ縲∵凾邉ｻ蛻励メ繝｣繝ｼ繝医・譛ｪ蟇ｾ蠢彌n"
            "                            </p>\n"
            "                        </div>\n"
            "\"\"\"\n"
            "                else:\n"
            "                    html += f\"\"\"\n"
            "                        <canvas id=\"{chart_id}\"></canvas>\n"
            "\"\"\"\n"
            "                html += f\"\"\"\n"
            "                        <div class=\"mt-3 pt-3 border-t border-gray-200\">\n"
            "                            <div class=\"grid grid-cols-2 gap-2 text-xs text-gray-600\">\n"
            "                                <div><span class=\"font-semibold\">謖・ｨ吝錐・・/span>髟ｷ譛滄≡蛻ｩ・・0蟷ｴ蛯ｵ・・/div>\n"
            "                                <div><span class=\"font-semibold\">邉ｻ蛻暦ｼ・/span>蛻ｩ蝗槭ｊ</div>\n"
            "                                <div><span class=\"font-semibold\">譛滄俣・・/span>逶ｴ霑・縺区怦{'' if has_rate_ts else '・域悴蟇ｾ蠢懶ｼ・}</div>\n"
            "                                <div><span class=\"font-semibold\">蜿門ｾ怜・・・/span>FRED / 蜷・嵜荳ｭ螟ｮ驫陦・/div>\n"
            "                            </div>\n"
            "                        </div>\n"
            "                        <p class=\"text-xs text-gray-600 mt-2\">迴ｾ蝨ｨ縺ｮ髟ｷ譛滄≡蛻ｩ縺ｯ{rate:.2f}%縺ｧ縺吶・/p>\n"
            "                    </div>\n"
            "\"\"\"\n"
        )
    text = pattern.sub(repl_rate, text, count=1)

# CPI block
pattern_cpi = re.compile(r"\n\s*if macro\.get\(\"CPI\"\) is not None:[\s\S]*?\n\s*\"\"\"\n", re.MULTILINE)

def repl_cpi(m):
    block = m.group(0)
    if 'cpiChart_' not in block:
        return block
    return (
        "\n            if macro.get(\"CPI\") is not None:\n"
        "                cpi = macro.get(\"CPI\")\n"
        "                chart_id = f\"cpiChart_{country_code}_{timeframe_code}\"\n"
        "                has_cpi_ts = bool(macro.get(\"CPI_history\"))\n"
        "                html += f\"\"\"\n"
        "                    <div class=\"bg-gray-50 p-4 rounded-lg\">\n"
        "                        <h3 class=\"text-lg font-semibold text-gray-900 mb-2\">CPI・域ｶ郁ｲｻ閠・黄萓｡謖・焚・・/h3>\n"
        "\"\"\"\n"
        "                if not has_cpi_ts:\n"
        "                    html += \"\"\"\n"
        "                        <div class=\"bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded mb-3\">\n"
        "                            <p class=\"text-xs text-yellow-800\">\n"
        "                                窶ｻ 迴ｾ蝨ｨ縺ｯ譛譁ｰ蛟､縺ｮ縺ｿ蜿門ｾ励＠縺ｦ縺翫ｊ縲∵凾邉ｻ蛻励メ繝｣繝ｼ繝医・譛ｪ蟇ｾ蠢彌n"
        "                            </p>\n"
        "                        </div>\n"
        "\"\"\"\n"
        "                else:\n"
        "                    html += f\"\"\"\n"
        "                        <canvas id=\"{chart_id}\"></canvas>\n"
        "\"\"\"\n"
        "                html += f\"\"\"\n"
        "                        <div class=\"mt-3 pt-3 border-t border-gray-200\">\n"
        "                            <div class=\"grid grid-cols-2 gap-2 text-xs text-gray-600\">\n"
        "                                <div><span class=\"font-semibold\">謖・ｨ吝錐・・/span>CPI・域ｶ郁ｲｻ閠・黄萓｡謖・焚・・/div>\n"
        "                                <div><span class=\"font-semibold\">邉ｻ蛻暦ｼ・/span>蜑榊ｹｴ蜷梧怦豈・/div>\n"
        "                                <div><span class=\"font-semibold\">譛滄俣・・/span>逶ｴ霑・2縺区怦{'' if has_cpi_ts else '・域悴蟇ｾ蠢懶ｼ・}</div>\n"
        "                                <div><span class=\"font-semibold\">蜿門ｾ怜・・・/span>FRED / 蜷・嵜邨ｱ險域ｩ滄未</div>\n"
        "                            </div>\n"
        "                        </div>\n"
        "                        <p class=\"text-xs text-gray-600 mt-2\">CPI蜑榊ｹｴ蜷梧怦豈斐・{cpi:.2f}%縺ｧ縺吶・/p>\n"
        "                    </div>\n"
        "\"\"\"\n"
    )
text = pattern_cpi.sub(repl_cpi, text, count=1)

# --- Update chart scripts: use MA series arrays + add rate/CPI scripts ---
# Replace MA scalar getters with historical MA arrays
text = text.replace('            ma20 = first_index.get("ma20", 0)\n            ma75 = first_index.get("ma75", 0)\n            ma200 = first_index.get("ma200", 0)\n',
                    '            historical_ma20 = first_index.get("historical_ma20", [])\n            historical_ma75 = first_index.get("historical_ma75", [])\n            historical_ma200 = first_index.get("historical_ma200", [])\n')

# Insert ma*_js after prices_js
if 'ma20_js' not in text:
    text = text.replace('                prices_js = json.dumps(prices_data, ensure_ascii=False)\n',
                        '                prices_js = json.dumps(prices_data, ensure_ascii=False)\n                ma20_js = json.dumps(historical_ma20 if len(historical_ma20) == len(prices_data) else [None] * len(prices_data), ensure_ascii=False)\n                ma75_js = json.dumps(historical_ma75 if len(historical_ma75) == len(prices_data) else [None] * len(prices_data), ensure_ascii=False)\n                ma200_js = json.dumps(historical_ma200 if len(historical_ma200) == len(prices_data) else [None] * len(prices_data), ensure_ascii=False)\n')

# Replace Array(fill(...)) with ma*_js
text = re.sub(r"data: Array\(\{len\(prices_data\)\}\)\.fill\(\{ma20\}\)", "data: {ma20_js}", text)
text = re.sub(r"data: Array\(\{len\(prices_data\)\}\)\.fill\(\{ma75\}\)", "data: {ma75_js}", text)
text = re.sub(r"data: Array\(\{len\(prices_data\)\}\)\.fill\(\{ma200\}\)", "data: {ma200_js}", text)

# Add rate/CPI scripts before closing </script>
if '// 髟ｷ譛滄≡蛻ｩ繝√Ε繝ｼ繝・ not in text:
    insert_point = text.find('        scripts += """\n            </script>')
    if insert_point == -1:
        raise SystemExit('ERROR: could not find script closing marker')
    extra = (
        "\n        # 髟ｷ譛滄≡蛻ｩ繝√Ε繝ｼ繝茨ｼ域凾邉ｻ蛻励′縺ゅｋ蝣ｴ蜷医・縺ｿ・噂n"
        "        financial = data.get(\"financial\", {}) if isinstance(data.get(\"financial\", {}), dict) else {}\n"
        "        rate_history = financial.get(\"long_term_rate_history\")\n"
        "        if timeframe_code == \"short\" and isinstance(rate_history, list) and len(rate_history) >= 2:\n"
        "            rate_labels = [p.get(\"date\") for p in rate_history if p.get(\"date\") and p.get(\"value\") is not None]\n"
        "            rate_values = [p.get(\"value\") for p in rate_history if p.get(\"date\") and p.get(\"value\") is not None]\n"
        "            if len(rate_labels) == len(rate_values) and len(rate_labels) >= 2:\n"
        "                chart_id = f\"rateChart_{country_code}_{timeframe_code}\"\n"
        "                scripts += f\"\"\"\n"
        "                // 髟ｷ譛滄≡蛻ｩ繝√Ε繝ｼ繝・n"
        "                const ctx_{chart_id.replace('-', '_')} = document.getElementById('{chart_id}');\n"
        "                if (ctx_{chart_id.replace('-', '_')}) {{\n"
        "                    new Chart(ctx_{chart_id.replace('-', '_')}, {{\n"
        "                        type: 'line',\n"
        "                        data: {{\n"
        "                            labels: {json.dumps(rate_labels, ensure_ascii=False)},\n"
        "                            datasets: [{{\n"
        "                                label: '10蟷ｴ蛯ｵ蛻ｩ蝗槭ｊ',\n"
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
        "\n        # CPI繝√Ε繝ｼ繝茨ｼ域凾邉ｻ蛻励′縺ゅｋ蝣ｴ蜷医・縺ｿ・噂n"
        "        macro = data.get(\"macro\", {}) if isinstance(data.get(\"macro\", {}), dict) else {}\n"
        "        cpi_history = macro.get(\"CPI_history\")\n"
        "        if timeframe_code == \"short\" and isinstance(cpi_history, list) and len(cpi_history) >= 2:\n"
        "            cpi_labels = [p.get(\"date\") for p in cpi_history if p.get(\"date\") and p.get(\"value\") is not None]\n"
        "            cpi_values = [p.get(\"value\") for p in cpi_history if p.get(\"date\") and p.get(\"value\") is not None]\n"
        "            if len(cpi_labels) == len(cpi_values) and len(cpi_labels) >= 2:\n"
        "                chart_id = f\"cpiChart_{country_code}_{timeframe_code}\"\n"
        "                scripts += f\"\"\"\n"
        "                // CPI繝√Ε繝ｼ繝茨ｼ亥燕蟷ｴ豈費ｼ噂n"
        "                const ctx_{chart_id.replace('-', '_')} = document.getElementById('{chart_id}');\n"
        "                if (ctx_{chart_id.replace('-', '_')}) {{\n"
        "                    new Chart(ctx_{chart_id.replace('-', '_')}, {{\n"
        "                        type: 'line',\n"
        "                        data: {{\n"
        "                            labels: {json.dumps(cpi_labels, ensure_ascii=False)},\n"
        "                            datasets: [{{\n"
        "                                label: 'CPI蜑榊ｹｴ豈・%)',\n"
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
    text = text[:insert_point] + extra + text[insert_point:]

p.write_text(text, encoding='utf-8')
print('OK')
