#!/usr/bin/env python3
"""
Medion Keyboard RGB UI
Web-based interface for per-key RGB control
"""

import os
import sys
import json
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import webbrowser
import threading
import time

LED_BASE_PATH = "/sys/class/leds"
PROFILE_DIR = Path.home() / ".config" / "medion-rgb-profiles"
NUM_KEYS = 126

class MedionRGBHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

    def _set_headers(self, content_type='text/html'):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def get_led_path(self, key_num):
        """Get the sysfs path for a specific key LED"""
        if key_num == "base":
            return Path(LED_BASE_PATH) / "rgb:kbd_backlight"
        return Path(LED_BASE_PATH) / f"rgb:kbd_backlight_{key_num}"

    def read_key_color(self, key_num):
        """Read RGB values for a specific key"""
        led_path = self.get_led_path(key_num)
        try:
            multi_intensity = (led_path / "multi_intensity").read_text().strip()
            r, g, b = map(int, multi_intensity.split())
            return {"r": r, "g": g, "b": b}
        except:
            return {"r": 0, "g": 0, "b": 0}

    def set_key_color(self, key_num, r, g, b):
        """Set RGB values for a specific key"""
        led_path = self.get_led_path(key_num)
        try:
            multi_intensity_path = led_path / "multi_intensity"
            os.system(f'echo "{r} {g} {b}" | sudo tee {multi_intensity_path} > /dev/null 2>&1')
            return True
        except:
            return False

    def do_GET(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/':
            self._set_headers('text/html')
            self.wfile.write(self.get_html().encode())

        elif parsed_path.path == '/api/keys':
            self._set_headers('application/json')
            keys = {}

            # Read special base key
            if self.get_led_path("base").exists():
                keys["base"] = self.read_key_color("base")

            # Read numbered keys
            for i in range(NUM_KEYS):
                if self.get_led_path(i).exists():
                    keys[str(i)] = self.read_key_color(i)

            self.wfile.write(json.dumps(keys).encode())

        elif parsed_path.path == '/api/profiles':
            self._set_headers('application/json')
            PROFILE_DIR.mkdir(parents=True, exist_ok=True)
            profiles = [p.stem for p in PROFILE_DIR.glob("*.json")]
            self.wfile.write(json.dumps(profiles).encode())

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        parsed_path = urlparse(self.path)

        if parsed_path.path == '/api/set-key':
            data = json.loads(post_data.decode())
            key_num = data['key']
            if key_num != "base":
                key_num = int(key_num)

            success = self.set_key_color(key_num, data['r'], data['g'], data['b'])

            self._set_headers('application/json')
            self.wfile.write(json.dumps({"success": success}).encode())

        elif parsed_path.path == '/api/save-profile':
            data = json.loads(post_data.decode())
            profile_name = data['name']

            PROFILE_DIR.mkdir(parents=True, exist_ok=True)
            profile_path = PROFILE_DIR / f"{profile_name}.json"

            profile_data = {"version": 1, "keys": {}}

            # Save special base key
            if self.get_led_path("base").exists():
                color = self.read_key_color("base")
                profile_data["keys"]["base"] = {
                    "rgb": [color["r"], color["g"], color["b"]],
                    "brightness": 50
                }

            # Save numbered keys
            for i in range(NUM_KEYS):
                if self.get_led_path(i).exists():
                    color = self.read_key_color(i)
                    profile_data["keys"][str(i)] = {
                        "rgb": [color["r"], color["g"], color["b"]],
                        "brightness": 50
                    }

            with open(profile_path, 'w') as f:
                json.dump(profile_data, f, indent=2)

            self._set_headers('application/json')
            self.wfile.write(json.dumps({"success": True}).encode())

        elif parsed_path.path == '/api/load-profile':
            data = json.loads(post_data.decode())
            profile_name = data['name']
            profile_path = PROFILE_DIR / f"{profile_name}.json"

            if not profile_path.exists():
                self._set_headers('application/json')
                self.wfile.write(json.dumps({"success": False}).encode())
                return

            with open(profile_path, 'r') as f:
                profile_data = json.load(f)

            keys = profile_data.get("keys", {})
            for key_num_str, data in keys.items():
                key_num = key_num_str if key_num_str == "base" else int(key_num_str)
                rgb = data.get("rgb", [0, 0, 0])
                self.set_key_color(key_num, rgb[0], rgb[1], rgb[2])

            self._set_headers('application/json')
            self.wfile.write(json.dumps({"success": True}).encode())

    def get_html(self):
        return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Medion Keyboard RGB Controller</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
            color: #fff;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2em;
            text-shadow: 0 0 20px rgba(0,150,255,0.5);
        }
        .controls {
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            align-items: center;
        }
        .control-group {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        label { font-weight: bold; }
        input[type="color"] {
            width: 60px;
            height: 40px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        input[type="text"], select {
            padding: 10px;
            border-radius: 5px;
            border: 1px solid rgba(255,255,255,0.2);
            background: rgba(255,255,255,0.1);
            color: #fff;
            font-size: 14px;
        }
        button {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: scale(1.05);
        }
        button:active {
            transform: scale(0.95);
        }
        .keyboard {
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 50px rgba(0,0,0,0.5);
        }
        .key-row {
            display: flex;
            gap: 5px;
            margin-bottom: 5px;
            justify-content: center;
        }
        .key {
            flex: 1;
            height: 50px;
            min-width: 0;
            border-radius: 5px;
            border: 2px solid rgba(255,255,255,0.2);
            cursor: pointer;
            transition: all 0.2s;
            position: relative;
            font-size: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            text-shadow: 0 0 5px rgba(0,0,0,0.8);
        }
        .key:hover {
            transform: scale(1.1);
            border-color: #fff;
            box-shadow: 0 0 20px rgba(255,255,255,0.3);
        }
        .key.selected {
            border: 3px solid #fff;
            box-shadow: 0 0 30px rgba(255,255,255,0.6);
        }
        .key.w150 { flex: 1.5; }
        .key.w200 { flex: 2; }
        .key.w250 { flex: 2.5; }
        .key.w600 { flex: 6; }
        .status {
            text-align: center;
            margin-top: 20px;
            font-size: 14px;
            color: #888;
        }
        .preset-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .preset-btn {
            padding: 8px 15px;
            background: rgba(255,255,255,0.1);
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎹 Medion Keyboard RGB Controller</h1>

        <div class="controls">
            <div class="control-group">
                <label>Color:</label>
                <input type="color" id="colorPicker" value="#ff0000">
            </div>

            <div class="control-group">
                <label>Profile Name:</label>
                <input type="text" id="profileName" placeholder="my-profile">
                <button onclick="saveProfile()">💾 Save</button>
            </div>

            <div class="control-group">
                <label>Load:</label>
                <select id="profileList">
                    <option value="">-- Select Profile --</option>
                </select>
                <button onclick="loadProfile()">📂 Load</button>
            </div>

            <button onclick="loadCurrentColors()">🔄 Refresh</button>
        </div>

        <div class="controls">
            <div class="preset-buttons">
                <button class="preset-btn" onclick="applyPreset('red')">🔴 Red</button>
                <button class="preset-btn" onclick="applyPreset('green')">🟢 Green</button>
                <button class="preset-btn" onclick="applyPreset('blue')">🔵 Blue</button>
                <button class="preset-btn" onclick="applyPreset('purple')">🟣 Purple</button>
                <button class="preset-btn" onclick="applyPreset('cyan')">🩵 Cyan</button>
                <button class="preset-btn" onclick="applyPreset('yellow')">🟡 Yellow</button>
                <button class="preset-btn" onclick="applyPreset('white')">⚪ White</button>
                <button class="preset-btn" onclick="applyPreset('rainbow')">🌈 Rainbow</button>
                <button class="preset-btn" onclick="applyPreset('off')">⚫ Off</button>
            </div>
        </div>

        <div class="keyboard" id="keyboard"></div>

        <div class="status" id="status">Click any key to change its color • Use Ctrl+Click to apply color to multiple keys</div>
    </div>

    <script>
        let selectedKeys = new Set();
        let keyColors = {};

        const keyLayout = [
            [{k: 105, l: 'Esc'}, {k: 106, l: 'F1'}, {k: 107, l: 'F2'}, {k: 108, l: 'F3'}, {k: 109, l: 'F4'}, {k: 110, l: 'F5'}, {k: 111, l: 'F6'}, {k: 112, l: 'F7'}, {k: 113, l: 'F8'}, {k: 114, l: 'F9'}, {k: 115, l: 'F10'}, {k: 116, l: 'F11'}, {k: 117, l: 'F12'}, {k: 118, l: 'Prt'}, {k: 119, l: 'Pau'}, {k: 120, l: 'Del'}, {k: 102, l: 'End'}, {k: 103, l: '+'}, {k: 104, l: '-'}],
            [{k: 84, l: '`'}, {k: 85, l: '1'}, {k: 86, l: '2'}, {k: 87, l: '3'}, {k: 88, l: '4'}, {k: 89, l: '5'}, {k: 90, l: '6'}, {k: 91, l: '7'}, {k: 92, l: '8'}, {k: 93, l: '9'}, {k: 94, l: '0'}, {k: 95, l: '-'}, {k: 96, l: '='}, {k: 98, l: '⌫', w: 'w200'}, {k: 99, l: 'Num'}, {k: 100, l: '/'}, {k: 101, l: '*'}, {k: 122, l: '+'}],
            [{k: 63, l: 'Tab', w: 'w150'}, {k: 65, l: 'Q'}, {k: 66, l: 'W'}, {k: 67, l: 'E'}, {k: 68, l: 'R'}, {k: 69, l: 'T'}, {k: 70, l: 'Y'}, {k: 71, l: 'U'}, {k: 72, l: 'I'}, {k: 73, l: 'O'}, {k: 74, l: 'P'}, {k: 75, l: '['}, {k: 76, l: ']'}, {k: 77, l: '⏎', w: 'w150'}, {k: 78, l: '7'}, {k: 79, l: '8'}, {k: 80, l: '9'}],
            [{k: 42, l: 'Caps', w: 'w200'}, {k: 44, l: 'A'}, {k: 45, l: 'S'}, {k: 46, l: 'D'}, {k: 47, l: 'F'}, {k: 48, l: 'G'}, {k: 49, l: 'H'}, {k: 50, l: 'J'}, {k: 51, l: 'K'}, {k: 52, l: 'L'}, {k: 53, l: ';'}, {k: 54, l: '\\''}, {k: 55, l: '#'}, {k: 77, l: '⏎', w: 'w200'}, {k: 57, l: '4'}, {k: 58, l: '5'}, {k: 59, l: '6'}],
            [{k: 21, l: 'Shift', w: 'w150'}, {k: 23, l: '\\\\'}, {k: 24, l: 'Z'}, {k: 25, l: 'X'}, {k: 26, l: 'C'}, {k: 27, l: 'V'}, {k: 28, l: 'B'}, {k: 29, l: 'N'}, {k: 30, l: 'M'}, {k: 31, l: ','}, {k: 32, l: '.'}, {k: 33, l: '/'}, {k: 34, l: 'Shift', w: 'w250'}, {k: 35, l: '↑'}, {k: 36, l: '1'}, {k: 37, l: '2'}, {k: 38, l: '3'}],
            [{k: 'base', l: 'Ctrl'}, {k: 2, l: 'Fn'}, {k: 3, l: 'Win'}, {k: 4, l: 'Alt'}, {k: 7, l: 'Space', w: 'w600'}, {k: 10, l: 'AltGr'}, {k: 11, l: '☰'}, {k: 12, l: 'Ctrl'}, {k: 13, l: '←'}, {k: 14, l: '↓'}, {k: 15, l: '→'}, {k: 16, l: '0', w: 'w200'}, {k: 17, l: '.'}]
        ];

        function createKeyboard() {
            const keyboard = document.getElementById('keyboard');
            keyboard.innerHTML = '';

            keyLayout.forEach(row => {
                const rowDiv = document.createElement('div');
                rowDiv.className = 'key-row';

                row.forEach(keyInfo => {
                    if (keyInfo.s) {
                        const spacer = document.createElement('div');
                        spacer.className = 'spacer';
                        rowDiv.appendChild(spacer);
                    } else {
                        const key = document.createElement('div');
                        key.className = 'key';
                        if (keyInfo.w) key.classList.add(keyInfo.w);
                        key.dataset.key = keyInfo.k;
                        key.textContent = keyInfo.l;
                        key.onclick = (e) => handleKeyClick(keyInfo.k, e);
                        rowDiv.appendChild(key);
                    }
                });

                keyboard.appendChild(rowDiv);
            });
        }

        function handleKeyClick(keyNum, event) {
            const color = document.getElementById('colorPicker').value;
            const rgb = hexToRgb(color);

            if (event.ctrlKey) {
                const keyEl = event.target;
                if (selectedKeys.has(keyNum)) {
                    selectedKeys.delete(keyNum);
                    keyEl.classList.remove('selected');
                } else {
                    selectedKeys.add(keyNum);
                    keyEl.classList.add('selected');
                }
            } else {
                setKeyColor(keyNum, rgb.r, rgb.g, rgb.b);
            }
        }

        function hexToRgb(hex) {
            const result = /^#?([a-f\\d]{2})([a-f\\d]{2})([a-f\\d]{2})$/i.exec(hex);
            return result ? {
                r: parseInt(result[1], 16),
                g: parseInt(result[2], 16),
                b: parseInt(result[3], 16)
            } : {r: 0, g: 0, b: 0};
        }

        function rgbToHex(r, g, b) {
            return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
        }

        async function setKeyColor(keyNum, r, g, b) {
            const response = await fetch('/api/set-key', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({key: keyNum, r, g, b})
            });

            if (response.ok) {
                updateKeyDisplay(keyNum, r, g, b);
                keyColors[keyNum] = {r, g, b};
            }
        }

        function updateKeyDisplay(keyNum, r, g, b) {
            const keyEl = document.querySelector(`[data-key="${keyNum}"]`);
            if (keyEl) {
                keyEl.style.backgroundColor = `rgb(${r}, ${g}, ${b})`;
            }
        }

        async function loadCurrentColors() {
            setStatus('Loading current colors...');
            const response = await fetch('/api/keys');
            keyColors = await response.json();

            for (const [keyNum, color] of Object.entries(keyColors)) {
                updateKeyDisplay(keyNum, color.r, color.g, color.b);
            }
            setStatus('Colors loaded');
        }

        async function saveProfile() {
            const name = document.getElementById('profileName').value;
            if (!name) {
                alert('Please enter a profile name');
                return;
            }

            setStatus('Saving profile...');
            const response = await fetch('/api/save-profile', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name})
            });

            if (response.ok) {
                setStatus(`Profile "${name}" saved!`);
                loadProfiles();
            }
        }

        async function loadProfile() {
            const name = document.getElementById('profileList').value;
            if (!name) {
                alert('Please select a profile');
                return;
            }

            setStatus('Loading profile...');
            const response = await fetch('/api/load-profile', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name})
            });

            if (response.ok) {
                setStatus(`Profile "${name}" loaded!`);
                await loadCurrentColors();
            }
        }

        async function loadProfiles() {
            const response = await fetch('/api/profiles');
            const profiles = await response.json();

            const select = document.getElementById('profileList');
            select.innerHTML = '<option value="">-- Select Profile --</option>';
            profiles.forEach(profile => {
                const option = document.createElement('option');
                option.value = profile;
                option.textContent = profile;
                select.appendChild(option);
            });
        }

        async function applyPreset(preset) {
            setStatus(`Applying ${preset} preset...`);

            const presets = {
                red: [255, 0, 0],
                green: [0, 255, 0],
                blue: [0, 0, 255],
                purple: [128, 0, 128],
                cyan: [0, 255, 255],
                yellow: [255, 255, 0],
                white: [255, 255, 255],
                off: [0, 0, 0]
            };

            if (preset === 'rainbow') {
                const keys = Object.keys(keyColors);
                for (let i = 0; i < keys.length; i++) {
                    const hue = (i / keys.length) * 360;
                    const rgb = hslToRgb(hue / 360, 1, 0.5);
                    await setKeyColor(keys[i], rgb.r, rgb.g, rgb.b);
                }
            } else {
                const [r, g, b] = presets[preset];
                for (const keyNum of Object.keys(keyColors)) {
                    await setKeyColor(keyNum, r, g, b);
                }
            }

            setStatus(`${preset} preset applied!`);
        }

        function hslToRgb(h, s, l) {
            let r, g, b;
            if (s === 0) {
                r = g = b = l;
            } else {
                const hue2rgb = (p, q, t) => {
                    if (t < 0) t += 1;
                    if (t > 1) t -= 1;
                    if (t < 1/6) return p + (q - p) * 6 * t;
                    if (t < 1/2) return q;
                    if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
                    return p;
                };
                const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
                const p = 2 * l - q;
                r = hue2rgb(p, q, h + 1/3);
                g = hue2rgb(p, q, h);
                b = hue2rgb(p, q, h - 1/3);
            }
            return {
                r: Math.round(r * 255),
                g: Math.round(g * 255),
                b: Math.round(b * 255)
            };
        }

        function setStatus(msg) {
            document.getElementById('status').textContent = msg;
        }

        // Apply color to selected keys
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && selectedKeys.size > 0) {
                const color = document.getElementById('colorPicker').value;
                const rgb = hexToRgb(color);

                selectedKeys.forEach(keyNum => {
                    setKeyColor(keyNum, rgb.r, rgb.g, rgb.b);
                });

                // Clear selection
                document.querySelectorAll('.key.selected').forEach(el => {
                    el.classList.remove('selected');
                });
                selectedKeys.clear();
            }
        });

        // Initialize
        createKeyboard();
        loadCurrentColors();
        loadProfiles();
    </script>
</body>
</html>'''

def main():
    port = 8080
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    server = HTTPServer(('localhost', port), MedionRGBHandler)

    print(f"🎹 Medion RGB Controller starting...")
    print(f"🌐 Open your browser to: http://localhost:{port}")
    print(f"📁 Profiles stored in: {PROFILE_DIR}")
    print(f"⚠️  Make sure you have sudo access for LED control")
    print(f"🛑 Press Ctrl+C to stop\n")

    # Open browser after short delay
    def open_browser():
        time.sleep(1)
        webbrowser.open(f'http://localhost:{port}')

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        server.shutdown()

if __name__ == "__main__":
    main()
