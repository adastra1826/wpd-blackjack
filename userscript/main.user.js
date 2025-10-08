// ==UserScript==
// @name         WPD Blackjack Automation
// @namespace    https://github.com/adastra1826
// @updateURL    https://raw.githubusercontent.com/adastra1826/wpd-blackjack/refs/heads/main/userscript/main.user.js
// @downloadURL  https://raw.githubusercontent.com/adastra1826/wpd-blackjack/refs/heads/main/userscript/main.user.js
// @version      1.0.16
// @description  Automated blackjack playing with Flask backend
// @author       Nicholas Doherty
// @match        https://watchpeopledie.tv/casino/blackjack*
// @grant        GM_xmlhttpRequest
// @grant        unsafeWindow
// @connect      localhost
// @connect      cdn.jsdelivr.net
// @connect      raw.githubusercontent.com
// @run-at       document-start
// ==/UserScript==

(function() {
    'use strict';
    
    console.log('[AUTOMATION] WPD Blackjack Automation script beginning loading');

    // Configuration
    // Pick the branch and CDN to use
    const branch = 'main';
    const useGithub = true;

    const ghUrl = `https://raw.githubusercontent.com/adastra1826/wpd-blackjack/refs/heads/${branch}/userscript/modules/`;
    const jsDelivrUrl = `https://cdn.jsdelivr.net/gh/adastra1826/wpd-blackjack@refs/heads/${branch}/userscript/modules/`;
    const cdnUrl = useGithub ? ghUrl : jsDelivrUrl;
    
    const modules = [
        'shadow-dom.js'
    ];

    const loadedModules = {};

    async function loadModules(name) {
        console.log('[AUTOMATION] Loading module:', name);
        const { createControlPanel } = await import(`${cdnUrl}shadow-dom.js`);
        loadedModules[name] = createControlPanel();
        console.log('[AUTOMATION] Loaded module:', name);
    }

    loadModules('shadow-dom.js').then(() => {
        console.log('[AUTOMATION] Loaded modules:', loadedModules);
        if (loadedModules['shadow-dom']) {
            loadedModules['shadow-dom'].createControlPanel();
        } else {
            console.error('[AUTOMATION] Failed to load shadow-dom module');
        }
    });

    /*

    async function loadModules(name) {
        return new Promise((resolve, reject) => {
            GM_xmlhttpRequest({
                url: `${cdnUrl}${name}`,
                method: 'GET',
                onload: (response) => {
                    if (response.status === 200) {
                        try {
                            const wrapped = new Function(response.responseText);
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
                loadedModules[name] = await loadModules(module);
            } catch (error) {
                console.error(`Failed to load module: ${module}`, error);
            }
        }
    }

    loadAllModules().then(() => {
        console.log('[AUTOMATION] Loaded modules:', loadedModules);
        if (loadedModules['shadow-dom']) {
            loadedModules['shadow-dom'].createControlPanel();
        } else {
            console.error('[AUTOMATION] Failed to load shadow-dom module');
        }
        console.log('[AUTOMATION] WPD Blackjack Automation script loaded');
    });

    */

})();