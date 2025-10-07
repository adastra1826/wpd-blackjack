// ==UserScript==
// @name         Blackjack Automation
// @namespace    http://tampermonkey.net/
// @version      1.3
// @description  Automated blackjack playing with Flask backend
// @author       You
// @match        https://watchpeopledie.tv/casino/blackjack*
// @grant        GM_xmlhttpRequest
// @grant        unsafeWindow
// @connect      localhost
// @run-at       document-start
// ==/UserScript==

(function() {
    'use strict';

    // Configuration
    const FLASK_SERVER = 'https://localhost:8080';
    let isRunning = false;
    let handsPlayed = 0;
    let targetHands = 0;
    let currentStrategy = 'basic_strategy';
    let wagerAmount = 5;
    let actionDelay = 1500; // ms between actions

    console.log('[Automation] 🎰 v1.3 initializing (document-start)');

    // =================================================================
    // XHR INTERCEPTION - Must run FIRST, before page scripts load
    // =================================================================
    (function interceptXHR() {

        console.log('Overriding HXR implementation.');

        const XHR = unsafeWindow.XMLHttpRequest;
        const origOpen = XHR.prototype.open;
        const origSend = XHR.prototype.send;

        // Store original response getter
        const origResponseGetter = Object.getOwnPropertyDescriptor(XHR.prototype, 'response');
        const origResponseTextGetter = Object.getOwnPropertyDescriptor(XHR.prototype, 'responseText');

        XHR.prototype.open = function(method, url, ...args) {
            this._intercepted_url = url;
            this._intercepted_method = method;
            return origOpen.apply(this, [method, url, ...args]);
        };

        XHR.prototype.send = function(body) {
            const xhr = this;

            // Check if this is a blackjack request
            if (xhr._intercepted_url && xhr._intercepted_url.includes('/casino/blackjack/')) {
                console.log('[Automation] ✅ XHR intercepted:', xhr._intercepted_method, xhr._intercepted_url);

                // Store original onreadystatechange
                const origOnReadyStateChange = xhr.onreadystatechange;

                xhr.onreadystatechange = function(...args) {
                    // Call original handler first
                    if (origOnReadyStateChange) {
                        origOnReadyStateChange.apply(this, args);
                    }

                    // When request is complete
                    if (xhr.readyState === 4 && xhr.status === 200) {
                        try {
                            // Get response data
                            const responseText = origResponseTextGetter 
                                ? origResponseTextGetter.get.call(xhr)
                                : xhr.responseText;

                            console.log('[Automation] 📥 XHR complete, processing response...');
                            
                            // Handle the response asynchronously (don't block page)
                            setTimeout(() => {
                                try {
                                    handleGameResponse(responseText);
                                } catch (error) {
                                    console.error('[Automation] ❌ Error in handleGameResponse:', error);
                                }
                            }, 0);
                        } catch (error) {
                            console.error('[Automation] ❌ XHR interception error:', error);
                        }
                    }
                };

                // Also add load event listener as backup
                xhr.addEventListener('load', function() {
                    console.log('[Automation] 📥 XHR load event fired');
                });
            }

            return origSend.apply(this, arguments);
        };

        console.log('[Automation] ✅ XHR interception installed');
    })();

    // =================================================================
    // GAME RESPONSE HANDLER
    // =================================================================
    async function handleGameResponse(responseText) {
        try {
            const response = JSON.parse(responseText);
            
            if (response.success && response.state) {
                console.log('[Automation] 🎮 Game state:', response.state.status);
                
                // Always send state to server for logging
                await sendStateToServer(response);
                
                if (isRunning) {
                    const action = await getNextAction(response.state);
                    
                    if (action && action !== 'none') {
                        console.log('[Automation] 🎯 Next action:', action);
                        setTimeout(() => {
                            if (isRunning) {
                                executeAction(action);
                            }
                        }, actionDelay);
                    }
                    
                    // Check if hand is complete
                    if (response.state.actions && response.state.actions.includes('DEAL')) {
                        handsPlayed++;
                        if (window.automationElements) {
                            window.automationElements.handsEl.textContent = handsPlayed;
                        }
                        updateStats();
                        
                        if (targetHands > 0 && handsPlayed >= targetHands) {
                            console.log('[Automation] 🏁 Target reached');
                            toggleRun();
                        } else {
                            setTimeout(() => {
                                if (isRunning) {
                                    checkAndStartNewHand();
                                }
                            }, actionDelay * 2);
                        }
                    }
                }
            } else {
                console.log('[Automation] ℹ️ Response does not contain game state');
            }
        } catch (error) {
            console.error('[Automation] ❌ Error parsing response:', error);
        }
    }

    // =================================================================
    // FLASK SERVER COMMUNICATION
    // =================================================================
    
    // Get formkey from page
    function getFormkey() {
        const formkeyElement = document.getElementById('formkey');
        return formkeyElement ? formkeyElement.textContent.trim() : null;
    }

    // Send state to Flask server
    async function sendStateToServer(gameData) {
        return new Promise((resolve, reject) => {
            const formkey = getFormkey();
            
            GM_xmlhttpRequest({
                method: 'POST',
                url: `${FLASK_SERVER}/game_state`,
                headers: { 'Content-Type': 'application/json' },
                data: JSON.stringify({
                    state: gameData.state,
                    gambler: gameData.gambler,
                    timestamp: new Date().toISOString(),
                    strategy: currentStrategy,
                    formkey: formkey
                }),
                onload: function(response) {
                    if (response.status === 200) {
                        console.log('[Automation] ✅ State sent to Flask');
                        resolve(JSON.parse(response.responseText));
                    } else {
                        console.error('[Automation] ❌ Flask error:', response.status);
                        reject(new Error(`Server returned ${response.status}`));
                    }
                },
                onerror: function(error) {
                    console.error('[Automation] ❌ Flask request error:', error);
                    reject(error);
                }
            });
        });
    }

    // Get next action from server
    async function getNextAction(state) {
        try {
            const response = await sendStateToServer({ state });
            return response.action;
        } catch (error) {
            console.error('[Automation] ❌ Error getting action:', error);
            return 'none';
        }
    }

    // Update statistics
    async function updateStats() {
        try {
            const formkey = getFormkey();
            
            GM_xmlhttpRequest({
                method: 'GET',
                url: `${FLASK_SERVER}/stats?formkey=${formkey}`,
                onload: function(response) {
                    if (response.status === 200) {
                        const stats = JSON.parse(response.responseText);
                        if (stats.total_hands > 0 && window.automationElements) {
                            const winRate = ((stats.wins / stats.total_hands) * 100).toFixed(1);
                            window.automationElements.winRateEl.textContent = `${winRate}%`;
                        }
                    }
                },
                onerror: function(error) {
                    console.error('[Automation] ❌ Stats error:', error);
                }
            });
        } catch (error) {
            console.error('[Automation] ❌ Update stats error:', error);
        }
    }

    // Test connection to Flask server
    function testConnection() {
        GM_xmlhttpRequest({
            method: 'GET',
            url: `${FLASK_SERVER}/health`,
            onload: function(response) {
                if (response.status === 200) {
                    const data = JSON.parse(response.responseText);
                    console.log('[Automation] ✅ Connected to Flask:', data.message);
                } else {
                    console.error('[Automation] ❌ Flask returned:', response.status);
                }
            },
            onerror: function() {
                console.error('[Automation] ❌ Cannot connect to Flask at', FLASK_SERVER);
            }
        });
    }

    // =================================================================
    // GAME CONTROL FUNCTIONS
    // =================================================================

    // Execute game action by clicking buttons
    function executeAction(action) {
        console.log('[Automation] 🎮 Executing:', action);
        
        try {
            if (action === 'deal') {
                const wagerInput = document.querySelector('input[name="wager"]');
                if (wagerInput) {
                    wagerInput.value = wagerAmount;
                    wagerInput.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
            
            const buttonMap = {
                'hit': 'blackjack-HIT',
                'stay': 'blackjack-STAY',
                'double': 'blackjack-DOUBLE_DOWN',
                'split': 'blackjack-SPLIT',
                'hit_split': 'blackjack-HIT_SPLIT',
                'stay_split': 'blackjack-STAY_SPLIT',
                'insurance': 'blackjack-BUY_INSURANCE',
                'deal': 'blackjack-DEAL'
            };
            
            const buttonId = buttonMap[action];
            if (buttonId) {
                const button = document.getElementById(buttonId);
                if (button && button.style.display !== 'none') {
                    button.click();
                    console.log('[Automation] ✅ Clicked button:', buttonId);
                } else {
                    console.warn('[Automation] ⚠️ Button not available:', buttonId);
                }
            }
        } catch (error) {
            console.error('[Automation] ❌ Execute error:', error);
        }
    }

    // Check if we need to deal a new hand
    function checkAndStartNewHand() {
        if (!isRunning) {
            console.log('[Automation] ℹ️ checkAndStartNewHand called but not running');
            return;
        }
        
        console.log('[Automation] 🔍 Looking for deal button...');
        const dealButton = document.getElementById('blackjack-DEAL');
        console.log('[Automation] 🔍 Deal button found:', dealButton);
        
        if (dealButton) {
            const computedStyle = window.getComputedStyle(dealButton);
            console.log('[Automation] 🔍 Deal button display:', computedStyle.display);
            console.log('[Automation] 🔍 Deal button visibility:', computedStyle.visibility);
            console.log('[Automation] 🔍 Deal button disabled:', dealButton.disabled);
            
            if (dealButton.style.display !== 'none' && computedStyle.display !== 'none' && !dealButton.disabled) {
                console.log('[Automation] 🎴 Starting new hand');
                
                const wagerInput = document.querySelector('input[name="wager"]');
                if (wagerInput) {
                    console.log('[Automation] 🔍 Wager input found, setting to:', wagerAmount);
                    wagerInput.value = wagerAmount;
                } else {
                    console.warn('[Automation] ⚠️ Wager input not found');
                }
                
                setTimeout(() => {
                    if (isRunning) {
                        executeAction('deal');
                    }
                }, actionDelay);
            } else {
                console.log('[Automation] ⏳ Deal button not ready yet, checking again...');
                setTimeout(checkAndStartNewHand, 500);
            }
        } else {
            console.warn('[Automation] ⚠️ Deal button not found in DOM, checking again...');
            setTimeout(checkAndStartNewHand, 500);
        }
    }

    // Toggle run state
    function toggleRun() {
        if (!window.automationElements) return;
        
        const { toggleBtn, statusEl } = window.automationElements;
        
        if (isRunning) {
            isRunning = false;
            toggleBtn.textContent = 'Start Run';
            toggleBtn.className = 'btn-start';
            statusEl.textContent = 'Stopped';
            console.log('[Automation] ⏹️ Stopped');
        } else {
            isRunning = true;
            handsPlayed = 0;
            toggleBtn.textContent = 'Stop Run';
            toggleBtn.className = 'btn-stop';
            statusEl.textContent = 'Running';
            console.log('[Automation] ▶️ Started');
            checkAndStartNewHand();
        }
    }

    // =================================================================
    // UI PANEL CREATION - Runs after DOM is ready
    // =================================================================

    function createControlPanel() {
        // Create host container with solid background
        const host = document.createElement('div');
        host.id = 'blackjack_automation_host';
        Object.assign(host.style, { 
            position: 'fixed', 
            zIndex: '2147483647',
            bottom: '20px', 
            right: '20px',
            width: '320px',
            background: '#1a1a1a',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.5)',
            border: '1px solid rgba(255, 255, 255, 0.1)'
        });
        document.body.appendChild(host);

        // Create shadow root for style isolation
        const root = host.attachShadow({ mode: 'open' });

        // Prevent event bubbling to page
        ['click', 'mousedown', 'mouseup'].forEach((evt) => {
            host.addEventListener(evt, (e) => {
                e.stopPropagation();
                e.stopImmediatePropagation();
            }, false);
        });

        // Add styles directly to shadow DOM
        const style = document.createElement('style');
        style.textContent = `
            * { box-sizing: border-box; }
            :host {
                all: initial;
            }
            #automation-panel {
                background: #1a1a1a;
                color: #e0e0e0;
                padding: 24px;
                font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
                font-size: 13px;
            }
            h3 {
                margin: 0 0 15px 0;
                color: #4CAF50;
                font-size: 16px;
                font-weight: 600;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                padding-bottom: 10px;
            }
            .control-group {
                margin-bottom: 12px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            label {
                flex: 0 0 100px;
                font-size: 12px;
                color: #b0b0b0;
            }
            input, select {
                flex: 1;
                padding: 6px 10px;
                background: #2a2a2a;
                color: #e0e0e0;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                font-size: 12px;
            }
            input:focus, select:focus {
                outline: none;
                border-color: #4CAF50;
                background: #333;
            }
            button {
                width: 100%;
                padding: 10px;
                font-size: 14px;
                font-weight: 600;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                transition: all 0.3s ease;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            .btn-start {
                background: linear-gradient(135deg, #4CAF50, #45a049);
                color: white;
            }
            .btn-start:hover {
                background: linear-gradient(135deg, #45a049, #4CAF50);
                box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
            }
            .btn-stop {
                background: linear-gradient(135deg, #f44336, #da190b);
                color: white;
            }
            .btn-stop:hover {
                background: linear-gradient(135deg, #da190b, #f44336);
                box-shadow: 0 2px 8px rgba(244, 67, 54, 0.3);
            }
            .status-group {
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }
            .status-group div {
                display: flex;
                justify-content: space-between;
                margin-bottom: 6px;
                font-size: 12px;
            }
            .status-group span {
                font-weight: 600;
                color: #4CAF50;
            }
            .status-label {
                color: #909090;
            }
        `;
        root.appendChild(style);

        // Create panel HTML
        const panel = document.createElement('div');
        panel.id = 'automation-panel';
        panel.innerHTML = `
            <h3>🎰 Blackjack Automation</h3>
            <div class="control-group">
                <label>Strategy:</label>
                <select id="strategy-select">
                    <option value="basic_strategy">Basic Strategy</option>
                </select>
            </div>
            <div class="control-group">
                <label>Wager Amount:</label>
                <input type="number" id="wager-input" value="5" min="1">
            </div>
            <div class="control-group">
                <label>Hands to Play:</label>
                <input type="number" id="hands-input" placeholder="Infinite" min="1">
            </div>
            <div class="control-group">
                <button id="toggle-run" class="btn-start">Start Run</button>
            </div>
            <div class="status-group">
                <div><span class="status-label">Status:</span> <span id="run-status">Idle</span></div>
                <div><span class="status-label">Hands Played:</span> <span id="hands-count">0</span></div>
                <div><span class="status-label">Win Rate:</span> <span id="win-rate">0%</span></div>
            </div>
        `;
        root.appendChild(panel);

        // Get elements using shadow DOM
        const $ = (id) => root.getElementById(id);

        // Event listeners
        $('toggle-run').addEventListener('click', toggleRun);
        $('strategy-select').addEventListener('change', (e) => {
            currentStrategy = e.target.value;
        });
        $('wager-input').addEventListener('change', (e) => {
            wagerAmount = parseInt(e.target.value);
        });
        $('hands-input').addEventListener('change', (e) => {
            targetHands = e.target.value ? parseInt(e.target.value) : 0;
        });

        // Store references
        window.automationElements = {
            root,
            toggleBtn: $('toggle-run'),
            statusEl: $('run-status'),
            handsEl: $('hands-count'),
            winRateEl: $('win-rate')
        };

        console.log('[Automation] ✅ Control panel created');
    }

    // =================================================================
    // INITIALIZATION - Wait for DOM
    // =================================================================

    function initialize() {
        console.log('[Automation] 🎰 v1.3 fully loaded');
        createControlPanel();
        
        const formkey = getFormkey();
        if (formkey) {
            console.log('[Automation] ✅ Formkey found:', formkey.substring(0, 8) + '...');
        } else {
            console.warn('[Automation] ⚠️ Formkey not found');
        }
        
        testConnection();
    }

    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }

})();