// v2 Market Report - Main JavaScript
// CSP準拠: インラインJS禁止、addEventListener方式のみ使用

(function() {
    'use strict';
    
    // localStorage用のキー
    const STATE_KEY = 'recommend-stock-state';
    
    // DOMContentLoaded後に初期化
    document.addEventListener('DOMContentLoaded', function() {
        initPeriodButtons();
        initMarketSelector();
        initTimeframeSelector();
        restoreState();
        initHeatmap();
    });
    
    // 期間選択ボタンの初期化
    function initPeriodButtons() {
        const periodButtons = document.querySelectorAll('.period-btn[data-years]');
        periodButtons.forEach(function(btn) {
            btn.addEventListener('click', function() {
                const years = parseInt(btn.dataset.years, 10);
                const chartId = btn.dataset.chartId || 'default';
                switchPeriod(years, chartId, btn);
            });
        });
    }
    
    // 期間切替処理
    function switchPeriod(years, chartId, clickedBtn) {
        // 同じチャートIDのボタンからactiveクラスを削除
        const chartButtons = document.querySelectorAll(`.period-btn[data-chart-id="${chartId}"]`);
        chartButtons.forEach(function(btn) {
            btn.classList.remove('active');
        });
        
        // クリックされたボタンにactiveクラスを追加
        if (clickedBtn) {
            clickedBtn.classList.add('active');
        }
        
        // チャートの再描画処理
        updateChartsForPeriod(years, chartId);
    }
    
    // 期間に応じてチャートを更新
    function updateChartsForPeriod(years, chartId) {
        // Plotlyが読み込まれているか確認
        if (typeof Plotly === 'undefined') {
            console.warn('Plotly is not loaded');
            return;
        }
        
        // チャートデータが存在するか確認
        if (typeof window.chartData === 'undefined' || !window.chartData) {
            console.warn('Chart data is not available');
            return;
        }
        
        // チャートIDに応じて対応するチャートを更新
        const chartTypeMap = {
            'price-chart': 'price',
            'rate-chart': 'rate',
            'cpi-chart': 'cpi'
        };
        
        const chartType = chartTypeMap[chartId];
        if (!chartType || !window.chartData[chartType]) {
            return;
        }
        
        // チャートコンテナを探す
        const chartContainer = document.querySelector(`[data-chart-type="${chartType}"]`);
        if (!chartContainer) {
            return;
        }
        
        // チャートdivを探す
        const chartDiv = chartContainer.querySelector('.plotly-graph-div');
        if (!chartDiv || !chartDiv.id) {
            return;
        }
        
        // 期間に応じてデータをフィルタリング
        const chartData = window.chartData[chartType];
        if (!chartData || !chartData.dates || !chartData.columns || !chartData.values) {
            console.warn('Invalid chart data structure for', chartType);
            return;
        }
        
        const endDate = new Date();
        const startDate = new Date();
        startDate.setFullYear(endDate.getFullYear() - years);
        
        // 日付でフィルタリング
        const filteredIndices = [];
        for (let i = 0; i < chartData.dates.length; i++) {
            const date = new Date(chartData.dates[i]);
            if (date >= startDate && date <= endDate) {
                filteredIndices.push(i);
            }
        }
        
        if (filteredIndices.length === 0) {
            console.warn('No data found for period:', years, 'years');
            return;
        }
        
        // 市場名を取得（ページタイトルから）
        const pageTitle = document.querySelector('h1');
        let marketName = '米国';
        if (pageTitle) {
            const titleText = pageTitle.textContent;
            if (titleText.includes('日本')) {
                marketName = '日本';
            }
        }
        
        // チャートタイプに応じてtracesとlayoutを生成
        let traces = [];
        let layout = {};
        
        if (chartType === 'rate') {
            // rateチャート: 政策金利と長期金利の2つのtrace
            const dates = filteredIndices.map(i => chartData.dates[i]);
            const columns = chartData.columns;
            const values = filteredIndices.map(i => {
                const row = chartData.values[i];
                // valuesが配列の配列の場合と、単一の配列の場合の両方に対応
                return Array.isArray(row) ? row : [row];
            });
            
            // 政策金利のtrace
            const policyRateIndex = columns.indexOf('policy_rate');
            if (policyRateIndex !== -1 && policyRateIndex < columns.length) {
                const policyData = dates.map((date, idx) => ({
                    x: date,
                    y: values[idx][policyRateIndex]
                })).filter(item => item.y !== null && item.y !== undefined);
                if (policyData.length > 0) {
                    traces.push({
                        x: policyData.map(item => item.x),
                        y: policyData.map(item => item.y),
                        mode: 'lines',
                        name: '政策金利（名目）',
                        line: { color: '#2563eb', width: 2 },
                        type: 'scatter'
                    });
                }
            }
            
            // 長期金利のtrace
            const longRateIndex = columns.indexOf('long_rate_10y');
            if (longRateIndex !== -1 && longRateIndex < columns.length) {
                const longRateData = dates.map((date, idx) => ({
                    x: date,
                    y: values[idx][longRateIndex]
                })).filter(item => item.y !== null && item.y !== undefined);
                if (longRateData.length > 0) {
                    traces.push({
                        x: longRateData.map(item => item.x),
                        y: longRateData.map(item => item.y),
                        mode: 'lines',
                        name: '長期金利（10年）',
                        line: { color: '#f59e0b', width: 2 },
                        type: 'scatter'
                    });
                }
            }
            
            layout = {
                title: marketName + ' - 政策金利・長期金利',
                xaxis: { title: '日付' },
                yaxis: { title: '金利 (%)' },
                hovermode: 'x unified',
                height: 400,
                margin: { l: 50, r: 50, t: 50, b: 50 },
                legend: { orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 }
            };
        } else if (chartType === 'cpi') {
            // cpiチャート: CPI前年比の1つのtrace + 0%の基準線
            const dates = filteredIndices.map(i => chartData.dates[i]);
            const columns = chartData.columns;
            const values = filteredIndices.map(i => {
                const row = chartData.values[i];
                // valuesが配列の配列の場合と、単一の配列の場合の両方に対応
                return Array.isArray(row) ? row : [row];
            });
            
            const cpiIndex = columns.indexOf('CPI_YoY');
            if (cpiIndex !== -1 && cpiIndex < columns.length) {
                const cpiData = dates.map((date, idx) => ({
                    x: date,
                    y: values[idx][cpiIndex]
                })).filter(item => item.y !== null && item.y !== undefined);
                if (cpiData.length > 0) {
                    traces.push({
                        x: cpiData.map(item => item.x),
                        y: cpiData.map(item => item.y),
                        mode: 'lines+markers',
                        name: 'CPI前年比',
                        line: { color: '#2563eb', width: 2 },
                        marker: { size: 4 },
                        type: 'scatter'
                    });
                }
            }
            
            layout = {
                title: marketName + ' - CPI（消費者物価指数）前年比',
                xaxis: { title: '日付' },
                yaxis: { title: 'CPI前年比 (%)' },
                hovermode: 'x unified',
                height: 400,
                margin: { l: 50, r: 50, t: 50, b: 50 },
                legend: { orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 },
                shapes: [{
                    type: 'line',
                    xref: 'x domain',
                    yref: 'y',
                    x0: 0,
                    x1: 1,
                    y0: 0,
                    y1: 0,
                    line: { color: 'gray', dash: 'dash', opacity: 0.5 }
                }]
            };
        } else if (chartType === 'price') {
            // priceチャート: 株価指数の1つのtrace
            const dates = filteredIndices.map(i => chartData.dates[i]);
            const columns = chartData.columns;
            const values = filteredIndices.map(i => {
                const row = chartData.values[i];
                // valuesが配列の配列の場合と、単一の配列の場合の両方に対応
                return Array.isArray(row) ? row : [row];
            });
            
            const closeIndex = columns.indexOf('Close');
            if (closeIndex !== -1 && closeIndex < columns.length) {
                const priceData = dates.map((date, idx) => ({
                    x: date,
                    y: values[idx][closeIndex]
                })).filter(item => item.y !== null && item.y !== undefined);
                if (priceData.length > 0) {
                    traces.push({
                        x: priceData.map(item => item.x),
                        y: priceData.map(item => item.y),
                        mode: 'lines',
                        name: '株価指数',
                        line: { color: '#2563eb', width: 2 },
                        type: 'scatter'
                    });
                }
            }
            
            layout = {
                title: marketName + ' - 株価指数',
                xaxis: { title: '日付' },
                yaxis: { title: '株価' },
                hovermode: 'x unified',
                height: 400,
                margin: { l: 50, r: 50, t: 50, b: 50 },
                legend: { orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'right', x: 1 }
            };
        }
        
        if (traces.length === 0) {
            return;
        }
        
        // 既存のチャートをdestroyしてから再描画
        Plotly.purge(chartDiv);
        Plotly.newPlot(chartDiv.id, traces, layout, { responsive: true });
    }
    
    // 市場選択の初期化
    function initMarketSelector() {
        const marketButtons = document.querySelectorAll('.market-btn[data-market]');
        marketButtons.forEach(function(btn) {
            btn.addEventListener('click', function() {
                const market = btn.dataset.market;
                switchMarket(market, btn);
            });
        });
    }
    
    // 市場切替処理
    function switchMarket(market, clickedBtn) {
        // Skeleton表示
        showSkeleton();
        
        // すべての市場ボタンからactiveクラスを削除
        const marketButtons = document.querySelectorAll('.market-btn');
        marketButtons.forEach(function(btn) {
            btn.classList.remove('active');
        });
        
        // クリックされたボタンにactiveクラスを追加
        if (clickedBtn) {
            clickedBtn.classList.add('active');
        }
        
        // ページ遷移（現在の実装では別ページとして実装されているため）
        const currentPath = window.location.pathname;
        const newPath = currentPath.replace(/(US|JP)-(short|medium|long)/, market + '-' + getCurrentTimeframe());
        if (newPath !== currentPath) {
            // 状態を保存してから遷移
            saveState(market, getCurrentTimeframe());
            window.location.href = newPath;
        } else {
            // 同じページの場合はSkeletonを非表示
            hideSkeleton();
            saveState(market, getCurrentTimeframe());
        }
    }
    
    // 期間選択の初期化
    function initTimeframeSelector() {
        const timeframeButtons = document.querySelectorAll('.timeframe-btn[data-timeframe]');
        timeframeButtons.forEach(function(btn) {
            btn.addEventListener('click', function() {
                const timeframe = btn.dataset.timeframe;
                switchTimeframe(timeframe, btn);
            });
        });
    }
    
    // 期間切替処理
    function switchTimeframe(timeframe, clickedBtn) {
        // Skeleton表示
        showSkeleton();
        
        // すべての期間ボタンからactiveクラスを削除
        const timeframeButtons = document.querySelectorAll('.timeframe-btn');
        timeframeButtons.forEach(function(btn) {
            btn.classList.remove('active');
        });
        
        // クリックされたボタンにactiveクラスを追加
        if (clickedBtn) {
            clickedBtn.classList.add('active');
        }
        
        // ページ遷移
        const currentPath = window.location.pathname;
        const newPath = currentPath.replace(/(US|JP)-(short|medium|long)/, getCurrentMarket() + '-' + timeframe);
        if (newPath !== currentPath) {
            // 状態を保存してから遷移
            saveState(getCurrentMarket(), timeframe);
            window.location.href = newPath;
        } else {
            // 同じページの場合はSkeletonを非表示
            hideSkeleton();
            saveState(getCurrentMarket(), timeframe);
        }
    }
    
    // 現在の市場を取得
    function getCurrentMarket() {
        const path = window.location.pathname;
        const match = path.match(/(US|JP)-(short|medium|long)/);
        return match ? match[1] : 'US';
    }
    
    // 現在の期間を取得
    function getCurrentTimeframe() {
        const path = window.location.pathname;
        const match = path.match(/(US|JP)-(short|medium|long)/);
        return match ? match[2] : 'short';
    }
    
    // Skeleton表示
    function showSkeleton() {
        const skeleton = document.getElementById('skeleton');
        if (skeleton) {
            skeleton.classList.remove('hidden');
        }
    }
    
    // Skeleton非表示
    function hideSkeleton() {
        const skeleton = document.getElementById('skeleton');
        if (skeleton) {
            skeleton.classList.add('hidden');
        }
    }
    
    // 状態を保存
    function saveState(market, period) {
        try {
            localStorage.setItem(STATE_KEY, JSON.stringify({
                market: market,
                period: period
            }));
        } catch (e) {
            console.warn('Failed to save state:', e);
        }
    }
    
    // 状態を読み込み
    function loadState() {
        try {
            const s = localStorage.getItem(STATE_KEY);
            return s ? JSON.parse(s) : null;
        } catch (e) {
            console.warn('Failed to load state:', e);
            return null;
        }
    }
    
    // 状態を復元
    function restoreState() {
        const state = loadState();
        if (!state) {
            return;
        }
        
        const currentMarket = getCurrentMarket();
        const currentTimeframe = getCurrentTimeframe();
        
        // 保存された状態と現在のページが異なる場合は遷移
        if (state.market !== currentMarket || state.period !== currentTimeframe) {
            const newPath = window.location.pathname.replace(
                /(US|JP)-(short|medium|long)/,
                state.market + '-' + state.period
            );
            if (newPath !== window.location.pathname) {
                window.location.href = newPath;
                return;
            }
        }
        
        // 現在のページに状態を反映
        if (state.market) {
            const marketBtn = document.querySelector(`.market-btn[data-market="${state.market}"]`);
            if (marketBtn) {
                // 既存のactiveを削除
                document.querySelectorAll('.market-btn').forEach(function(btn) {
                    btn.classList.remove('active');
                });
                marketBtn.classList.add('active');
            }
        }
        
        if (state.period) {
            const timeframeBtn = document.querySelector(`.timeframe-btn[data-timeframe="${state.period}"]`);
            if (timeframeBtn) {
                // 既存のactiveを削除
                document.querySelectorAll('.timeframe-btn').forEach(function(btn) {
                    btn.classList.remove('active');
                });
                timeframeBtn.classList.add('active');
            }
        }
    }
    
    // 後方互換性のため残す（非推奨）
    function saveUserPreferences(market, timeframe) {
        saveState(market, timeframe);
    }
    
    // 市場ヒートマップを初期化
    function initHeatmap() {
        const heatmapContainer = document.getElementById('market-heatmap');
        if (!heatmapContainer) {
            return;
        }
        
        // グローバル変数からヒートマップデータを取得
        if (typeof window.heatmapData === 'undefined' || !window.heatmapData || window.heatmapData.length === 0) {
            return;
        }
        
        // ヒートマップを描画
        window.heatmapData.forEach(function(item) {
            const tile = document.createElement('div');
            tile.className = 'heat-tile heat-' + item.direction + '-' + item.strength;
            tile.textContent = item.symbol;
            heatmapContainer.appendChild(tile);
        });
    }
})();

