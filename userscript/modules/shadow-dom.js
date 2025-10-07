(function() {

    function createControlPanel() {
    console.log("[Automation] 🎰 Creating control panel");

    // Create host container with solid background
    const host = document.createElement("div");
    host.id = "blackjack_automation_host";
    Object.assign(host.style, {
      position: "fixed",
      zIndex: "2147483647",
      bottom: "20px",
      right: "20px",
      width: "320px",
      background: "#1a1a1a",
      borderRadius: "8px",
      boxShadow: "0 4px 12px rgba(0, 0, 0, 0.5)",
      border: "1px solid rgba(255, 255, 255, 0.1)",
    });
    document.body.appendChild(host);

    // Create shadow root for style isolation
    const root = host.attachShadow({ mode: "open" });

    // Prevent event bubbling to page
    ["click", "mousedown", "mouseup"].forEach((evt) => {
      host.addEventListener(
        evt,
        (e) => {
          e.stopPropagation();
          e.stopImmediatePropagation();
        },
        false
      );
    });

    // Add styles directly to shadow DOM
    const style = document.createElement("style");
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
    const panel = document.createElement("div");
    panel.id = "automation-panel";
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
    $("toggle-run").addEventListener("click", toggleRun);
    $("strategy-select").addEventListener("change", (e) => {
      currentStrategy = e.target.value;
    });
    $("wager-input").addEventListener("change", (e) => {
      wagerAmount = parseInt(e.target.value);
    });
    $("hands-input").addEventListener("change", (e) => {
      targetHands = e.target.value ? parseInt(e.target.value) : 0;
    });

    // Store references
    window.automationElements = {
      root,
      toggleBtn: $("toggle-run"),
      statusEl: $("run-status"),
      handsEl: $("hands-count"),
      winRateEl: $("win-rate"),
    };

    console.log("[Automation] ✅ Control panel created");
    }

    return {
        createControlPanel: createControlPanel
    }
})();
