// v2 Market Report - Main JavaScript
// CSP準拠: インラインJS禁止、addEventListener方式のみ使用

(function() {
    'use strict';
    
    // DOMContentLoaded後に初期化
    document.addEventListener('DOMContentLoaded', function() {
        initPeriodButtons();
        initMarketSelector();
        initTimeframeSelector();
        initDetailsToggle();
        restoreUserPreferences();
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
            window.location.href = newPath;
        }
        
        // 選択状態を保存
        saveUserPreferences(market, getCurrentTimeframe());
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
            window.location.href = newPath;
        }
        
        // 選択状態を保存
        saveUserPreferences(getCurrentMarket(), timeframe);
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
    
    // ユーザー設定を保存
    function saveUserPreferences(market, timeframe) {
        try {
            localStorage.setItem('market-report-market', market);
            localStorage.setItem('market-report-timeframe', timeframe);
        } catch (e) {
            console.warn('Failed to save preferences:', e);
        }
    }
    
    // ユーザー設定を復元
    function restoreUserPreferences() {
        try {
            const savedMarket = localStorage.getItem('market-report-market');
            const savedTimeframe = localStorage.getItem('market-report-timeframe');
            
            if (savedMarket) {
                const marketBtn = document.querySelector(`.market-btn[data-market="${savedMarket}"]`);
                if (marketBtn) {
                    marketBtn.classList.add('active');
                }
            }
            
            if (savedTimeframe) {
                const timeframeBtn = document.querySelector(`.timeframe-btn[data-timeframe="${savedTimeframe}"]`);
                if (timeframeBtn) {
                    timeframeBtn.classList.add('active');
                }
            }
        } catch (e) {
            console.warn('Failed to restore preferences:', e);
        }
    }
})();

