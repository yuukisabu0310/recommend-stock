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
        initDetailsToggle();
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
        
        // チャートの再描画処理（必要に応じて実装）
        // 現在の実装では、ページ全体を再読み込みする必要があるため、
        // ここではボタンの状態変更のみを行う
        console.log('Period switched to:', years, 'years for chart:', chartId);
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
    
    // 詳細トグルの初期化
    function initDetailsToggle() {
        const toggleButtons = document.querySelectorAll('.details-toggle');
        toggleButtons.forEach(function(btn) {
            btn.addEventListener('click', function() {
                const content = btn.nextElementSibling;
                if (content && content.classList.contains('details-content')) {
                    content.classList.toggle('expanded');
                    btn.textContent = content.classList.contains('expanded') ? '詳細を閉じる' : '詳細を見る';
                }
            });
        });
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

