// Lightweight Charts実装（CSP準拠）
import { createChart } from 'https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.esm.production.js';

// チャートインスタンスを保持
let priceChart = null;
let candleSeries = null;
let ma20Series = null;
let ma75Series = null;
let ma200Series = null;

// チャート初期化
function initPriceChart() {
    const container = document.getElementById('price-chart');
    if (!container) {
        return;
    }

    // チャート作成
    priceChart = createChart(container, {
        layout: {
            background: { color: '#0b0f19' },
            textColor: '#d1d5db'
        },
        grid: {
            vertLines: { color: '#1f2933' },
            horzLines: { color: '#1f2933' }
        },
        rightPriceScale: { borderColor: '#374151' },
        timeScale: { borderColor: '#374151' },
        crosshair: { mode: 1 },
        width: container.clientWidth,
        height: 420
    });

    // ローソク足シリーズ
    candleSeries = priceChart.addCandlestickSeries({
        upColor: '#10b981',
        downColor: '#ef4444',
        wickUpColor: '#10b981',
        wickDownColor: '#ef4444',
        borderVisible: false
    });

    // 移動平均シリーズ
    ma20Series = priceChart.addLineSeries({
        color: '#f59e0b',
        lineWidth: 1,
        lineStyle: 1, // 破線
        title: 'MA20'
    });

    ma75Series = priceChart.addLineSeries({
        color: '#10b981',
        lineWidth: 1,
        lineStyle: 1, // 破線
        title: 'MA75'
    });

    ma200Series = priceChart.addLineSeries({
        color: '#ef4444',
        lineWidth: 1,
        lineStyle: 1, // 破線
        title: 'MA200'
    });

    // レスポンシブ対応
    const resize = () => {
        if (priceChart && container) {
            priceChart.applyOptions({ width: container.clientWidth });
        }
    };
    window.addEventListener('resize', resize);
    resize();

    // 初期データ読み込み
    const defaultPeriod = getCurrentPeriod();
    if (defaultPeriod) {
        updateChart(defaultPeriod);
    }
}

// 現在の期間を取得
function getCurrentPeriod() {
    const activeBtn = document.querySelector('.period-btn.active[data-chart-id="price-chart"]');
    if (activeBtn) {
        const years = parseInt(activeBtn.dataset.years, 10);
        if (years === 1) return 'short';
        if (years === 5) return 'medium';
        if (years === 10) return 'long';
    }
    return 'short'; // デフォルト
}

// チャート更新関数
window.updateChart = function(period) {
    if (!candleSeries || !ma20Series || !ma75Series || !ma200Series) {
        console.warn('Chart series not initialized');
        return;
    }

    // チャートデータが存在するか確認
    if (typeof window.chartData === 'undefined' || !window.chartData || !window.chartData.price) {
        console.warn('Chart data not available');
        return;
    }

    const chartData = window.chartData.price;
    if (!chartData.dates || !chartData.values) {
        console.warn('Invalid chart data structure');
        return;
    }

    // 期間に応じてデータをフィルタリング
    const endDate = new Date();
    const startDate = new Date();
    
    let years = 1;
    if (period === 'medium') years = 5;
    if (period === 'long') years = 10;
    
    startDate.setFullYear(endDate.getFullYear() - years);

    // データを変換
    const candles = [];
    const ma20Data = [];
    const ma75Data = [];
    const ma200Data = [];

    for (let i = 0; i < chartData.dates.length; i++) {
        const dateStr = chartData.dates[i];
        const date = new Date(dateStr);
        
        if (date >= startDate && date <= endDate) {
            const values = chartData.values[i];
            const columns = chartData.columns;
            
            // カラムインデックスを取得
            const openIdx = columns.indexOf('Open');
            const highIdx = columns.indexOf('High');
            const lowIdx = columns.indexOf('Low');
            const closeIdx = columns.indexOf('Close');
            const ma20Idx = columns.indexOf('MA20');
            const ma75Idx = columns.indexOf('MA75');
            const ma200Idx = columns.indexOf('MA200');

            // タイムスタンプ（Unix時間、秒単位）
            const time = Math.floor(date.getTime() / 1000);

            // ローソク足データ
            if (openIdx >= 0 && highIdx >= 0 && lowIdx >= 0 && closeIdx >= 0) {
                const open = parseFloat(values[openIdx]);
                const high = parseFloat(values[highIdx]);
                const low = parseFloat(values[lowIdx]);
                const close = parseFloat(values[closeIdx]);
                
                if (!isNaN(open) && !isNaN(high) && !isNaN(low) && !isNaN(close)) {
                    candles.push({
                        time: time,
                        open: open,
                        high: high,
                        low: low,
                        close: close
                    });
                }
            }

            // 移動平均データ
            if (closeIdx >= 0) {
                const close = parseFloat(values[closeIdx]);
                if (!isNaN(close)) {
                    if (ma20Idx >= 0 && !isNaN(parseFloat(values[ma20Idx]))) {
                        ma20Data.push({ time: time, value: parseFloat(values[ma20Idx]) });
                    }
                    if (ma75Idx >= 0 && !isNaN(parseFloat(values[ma75Idx]))) {
                        ma75Data.push({ time: time, value: parseFloat(values[ma75Idx]) });
                    }
                    if (ma200Idx >= 0 && !isNaN(parseFloat(values[ma200Idx]))) {
                        ma200Data.push({ time: time, value: parseFloat(values[ma200Idx]) });
                    }
                }
            }
        }
    }

    // データを設定
    if (candles.length > 0) {
        candleSeries.setData(candles);
    }
    if (ma20Data.length > 0) {
        ma20Series.setData(ma20Data);
    }
    if (ma75Data.length > 0) {
        ma75Series.setData(ma75Data);
    }
    if (ma200Data.length > 0) {
        ma200Series.setData(ma200Data);
    }

    // チャートを自動スケール
    priceChart.timeScale().fitContent();
};

// DOMContentLoaded後に初期化
document.addEventListener('DOMContentLoaded', function() {
    initPriceChart();

    // 期間タブとの連動
    const periodButtons = document.querySelectorAll('.period-btn[data-chart-id="price-chart"]');
    periodButtons.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const years = parseInt(btn.dataset.years, 10);
            let period = 'short';
            if (years === 5) period = 'medium';
            if (years === 10) period = 'long';
            
            updateChart(period);
        });
    });
});

