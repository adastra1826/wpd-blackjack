// ==UserScript==
// @name         WPD Blackjack Automation
// @namespace    https://github.com/adastra1826
// @updateURL    https://raw.githubusercontent.com/adastra1826/wpd-blackjack/refs/heads/main/userscript/main.user.js
// @downloadURL  https://raw.githubusercontent.com/adastra1826/wpd-blackjack/refs/heads/main/userscript/main.user.js
// @version      1.0.1
// @description  Automated blackjack playing with Flask backend
// @author       Nicholas Doherty
// @match        https://watchpeopledie.tv/casino/blackjack*
// @grant        GM_xmlhttpRequest
// @grant        unsafeWindow
// @connect      localhost
// @connect      cdn.jsdelivr.net
// @run-at       document-start
// ==/UserScript==

(function() {
    'use strict';
    
    console.log('[AUTOMATION] WPD Blackjack Automation script beginning loading');

    const cdnUrl = 'https://cdn.jsdelivr.net/gh/adastra1826/wpd-blackjack@refs/heads/main/userscript/modules/';
    
    const modules = [
        'shadow-dom.js'
    ];

    async function loadModules(name) {
        return new Promise((resolve, reject) => {
            GM_xmlhttpRequest({
                url: `${cdnUrl}${name}`,
                method: 'GET',
                onload: (response) => {
                    if (response.status === 200) {
                        try {
                            const wrapped = new Function('return ' + response.responseText);
                            const module = wrapped();
                            resolve(module);
                        } catch (error) {
                            reject(new Error(`Failed to load module ${name}: ${error}`));
                        }
                    } else {
                        reject(new Error(`Failed to load module ${name}: HTTP ${response.status}`));
                    }
                },
                onerror: (error) => {
                    reject(new Error(`Failed to load module ${name}: ${error}`));
                }
            });
        });
    }

    const loadedModules = {};

    async function loadAllModules() {
        for (const module of modules) {
            try {
                const name = module.replace('.js', '');
                loadedModules[name] = await loadModules(name);
            } catch (error) {
                console.error(`Failed to load module: ${module}`, error);
            }
        }
    }

    loadAllModules();

    loadedModules.shadowDom.createControlPanel();

    console.log('[AUTOMATION] WPD Blackjack Automation script loaded');

})();