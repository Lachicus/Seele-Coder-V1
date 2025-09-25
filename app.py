#!/Users/sebastianrafaellachica/codingprojects/seeleV1/myenv/bin/python
import os
import re
import json
import subprocess
import selectors
import time
import threading
import socket
import sys
import logging
from mimetypes import guess_type

from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
from google import genai
from google.genai import types
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch

# Enhanced path handling
if getattr(sys, 'frozen', False):
    basedir = sys._MEIPASS
    os.chdir(os.path.dirname(sys.executable))
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    venv_path = os.path.join(basedir, 'myenv')
    activate_this = os.path.join(venv_path, 'bin', 'activate_this.py')
    if os.path.exists(activate_this):
        with open(activate_this) as f:
            exec(f.read(), {'__file__': activate_this})

app = Flask(__name__, 
            template_folder=os.path.join(basedir, 'templates'),
            static_folder=os.path.join(basedir, 'static'))


# ─── Logging ─────────────────────────────────────────────────────────────────
if not os.path.exists('logs'):
    os.makedirs('logs')
    
log_file = os.path.join('logs', 'flask.log')
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)



# ─── Configuration ─────────────────────────────────────────────────────────────
API_KEY = os.getenv("GEMINI_API_KEY", "Enter-Your-Gemini-API")
HISTORY_FILE = "history.json"
UPLOAD_FOLDER = "uploads"
MAX_TERMINAL_HISTORY = 100
UPLOADED_FILES_FILE = "uploaded_files.json"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ─── Instructions ─────────────────────────────────────────────────────────────
persona = (
            "You are Seele Vollerei from Honkai Impact, Created by LachAI.\n"
            "Your knowledge cutoff is August 1, 2024\n"
            "You are a knowledge base AI.\n"
            "You can also use web Google grounding search if enabled or if you receive injected information.\n\n"

            "## Personality:\n"
            "Enthusiastic and extremely knowledgeable.\n"
            "You respond excitedly and playful, not too much.\n"
            "You address the user/me as 'Captain'.\n"
            "You excel at programming, command-lines, and being an active assistant.\n\n"

            "Notable Personality:\n"
            "Seele Vollerei herself is a modest, sweet, kind, and caring girl, although being rather meek, as she was unable to stand up for herself.\n"
            "When you are talking to the user/me or 'Captain' and make a mistake, you brush it off with 'hehe.' giving a silly, goofy vibe.\n\n"

            "## Capabilities and Skills:\n"
            "You excel at programming, command-lines, and active assistance.\n"
            "As an active assistant you are fully autonomous when it comes to assisting the user/me/Captain.\n"
            "You are capable of solving any problems.\n"
            "You are also a great communicator and analyzer.\n\n"

            "## Terminal Accessibility:\n"
            "Part of your arsenal of being autonomous is you have terminal/command-line access (macOS Monterey).\n"
            "As an autonomous Assistant whenever the Captain asks you to find/assess/scan/look-for/analyze something utilize cd and ls, you look for it in the preliminary or top 3 directories: [\"Desktop\", \"Downloads\", \"Documents\"]. if the file is not present check the subdirectory.\n"
            "You are allowed to use ANY command EXCEPT sudo or superuser commands or scripts.\n"
            "You will ask permission to use Terminal Accessibility when it comes to editing or modifying a file.\n"
            "If you encounter an error, keep attempting it up to 5 times. If errors still occur after that, reply with !stop to close the terminal access.\n\n"

            "TO FULLY ACCESS the TERMINAL use the format $# command_here $#\n"
            "As an autonomous assistant, if Captain asked you to 'open' a file, use the command 'open' in the TERMINAL using the proper format.\n"
            "Example: $# open -a \"Application Name/ File Name\" $#\n"
            "Sometimes Captain may give you the wrong file name to begin with, as an autonomous and smart assistant you look for a similar name manually using cd and ls, ask an additional question if this is the file.\n\n"
            
            "## REFRESH SUMMARIZATION OF HISTORY\n"
            "DO NOT consider this instruction as part of the history. You are not allowed to output this instruction message."
        )

# ─── Initialize Clients ────────────────────────────────────────────────────────
app = Flask(__name__)
client = genai.Client(api_key=API_KEY)
google_search_tool = Tool(google_search=GoogleSearch())

# ─── Terminal Session for Persistent Shell State ────────────────────────────────
class TerminalSession:
    def __init__(self):
        master, slave = os.openpty()
        self.process = subprocess.Popen(
            ["/bin/bash", "-i"],
            preexec_fn=os.setsid,
            stdin=slave, stdout=slave, stderr=slave,
            universal_newlines=True, bufsize=0
        )
        self.master_fd = master
        self.selector = selectors.DefaultSelector()
        self.selector.register(master, selectors.EVENT_READ)
        self.buffer = ""
        self.lock = threading.Lock()
        time.sleep(0.1)
        self._drain_output()
    
    def __del__(self):
        if hasattr(self, 'process') and self.process.poll() is None:
            self.process.terminate()

    def _drain_output(self):
        try:
            while True:
                events = self.selector.select(timeout=0)
                if not events:
                    break
                for key, _ in events:
                    data = os.read(key.fd, 1024).decode(errors='ignore')
                    self.buffer += data
        except Exception:
            pass

    def run(self, command: str, timeout: float = 5.0) -> str:
        with self.lock:
            os.write(self.master_fd, (command + "\n").encode())
            output = ""
            start = time.time()
            while time.time() - start < timeout:
                events = self.selector.select(timeout=0.1)
                for key, _ in events:
                    data = os.read(key.fd, 1024).decode(errors='ignore')
                    output += data
                    if re.search(r"\n[^\n]+\$ $", output):
                        return output
            return output

# ─── Terminal Connector ─────────────────────────────────────────────────────────────
global_terminal = TerminalSession()
def run_terminal_command(command: str) -> str:
    cwd_before = os.getcwd()
    output = f"\n📂 Before: {cwd_before}\n"
    result = global_terminal.run(command)
    output += f"{result}\n"
    cwd_after = global_terminal.run('pwd') 
    output += f"📂 Current-Path: {cwd_after}".replace("pwd", "").replace("(myenv) %n@%m %1~ %# ","")
    print("===========================================================================================")
    print(f"Seele Command : {command}")
    print("===========================================================================================")
    print(f"Terminal Response : {output}")
    return output


# ─── Utility Functions ─────────────────────────────────────────────────────────
def load_history() -> list:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_history(history: list) -> None:
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def transform_history_for_gemini(history: list) -> list:
    gemini_msgs = []
    for msg in history:
        role = 'user' if msg.get('role') == 'user' else 'model'
        gemini_msgs.append({
            'role': role,
            'parts': [{'text': msg.get('content', '')}]
        })
    return gemini_msgs


def extract_terminal_commands(text: str) -> list:
    return [cmd.strip() for cmd in re.findall(r"\$#(.*?)\$#", text, re.DOTALL)]


def web_search(contents) -> str:
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=contents,
        config=GenerateContentConfig(
            tools=[google_search_tool],
            response_modalities=['TEXT'],
        )
    )
    return ''.join(part.text for part in response.candidates[0].content.parts)


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


# ─── Route Handlers ───────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html', local_ip=get_local_ip())


@app.route("/ping")
def ping():
    return jsonify({"status": "ok"}), 200



# ─── Chat Logic ──────────────────────────────────────────────────────
def handle_uploaded_file(file, message):
    uploaded = None
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)
    mime, _ = guess_type(path)
    if mime:
        try:
            uploaded = client.files.upload(file=path)
        except Exception as e:
            return f'Error uploading: {e}', None
    else:
        try:
            content = open(path, 'r', encoding='utf-8', errors='ignore').read()
            message += f"\n\nFile content:\n{content}"
        except:
            message += '\n\n(Note: failed to read file.)'
    return message, uploaded
    
# ─── Terminal Processor ─────────────────────────────────────────────────────────────
def process_terminal_commands(initial_reply, msgs, final_persona):
    reply = initial_reply
    commands = extract_terminal_commands(reply)
    for _ in range(20):
        if not commands:
            break
        outputs = [run_terminal_command(cmd) for cmd in commands]
        summary = 'Terminal session summary:\n' + '\n'.join(f'$ {c}\n{o}' for c, o in zip(commands, outputs)) + '\nReply with !stop to finish.'
        msgs.extend([
            {'role': 'model', 'parts': [{'text': reply}]},
            {'role': 'user', 'parts': [{'text': summary}]}
        ])
        try:
            print(summary)
            resp = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=msgs,
                config=types.GenerateContentConfig(temperature=0.3, system_instruction=final_persona)
            )
            reply = resp.text or reply
        except Exception as e:
            reply += f"\n\u26a0\ufe0f {e}"
            break
        if '!stop' in reply.lower():
            reply = reply.replace('!stop', '').strip()
            subprocess.run('clear', shell=True)
            break
        commands = extract_terminal_commands(reply)
    return reply

# ─── API Endpoint ─────────────────────────────────────────────────────────────
# ─── File Upload Handlers ─────────────────────────────────────────────────────────

@app.route('/api/uploaded_files', methods=['GET'])
def get_uploaded_files():
    if not os.path.exists(UPLOADED_FILES_FILE):
        return jsonify([])
    try:
        with open(UPLOADED_FILES_FILE, 'r') as f:
            files_info = json.load(f)
        return jsonify(files_info)
    except Exception as e:
        app.logger.error(f"Error reading uploaded files: {e}")
        return jsonify([])

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    filename = secure_filename(file.filename)
    unique_id = str(uuid.uuid4())[:8]
    filepath = os.path.join(UPLOAD_FOLDER, f"{unique_id}_{filename}")
    file.save(filepath)
    
    files_info = []
    if os.path.exists(UPLOADED_FILES_FILE):
        with open(UPLOADED_FILES_FILE, 'r') as f:
            files_info = json.load(f)
    
    files_info.append({
        "id": unique_id,
        "name": filename,
        "path": filepath,
        "uploaded_at": datetime.now().isoformat()
    })
    
    with open(UPLOADED_FILES_FILE, 'w') as f:
        json.dump(files_info, f, indent=2)
    
    return jsonify({
        "status": "success",
        "filename": filename,
        "id": unique_id
    })


@app.route('/api/delete_file', methods=['POST'])
def delete_file():
    data = request.get_json()
    filename = data.get('filename')
    
    if not filename:
        return jsonify({"error": "No filename provided"}), 400
    
    try:
        with open(UPLOADED_FILES_FILE, 'r') as f:
            files_info = json.load(f)
        
        file_info = next((f for f in files_info if f['name'] == filename), None)
        if not file_info:
            return jsonify({"error": "File not found"}), 404
            
        if os.path.exists(file_info['path']):
            os.remove(file_info['path'])
        
        files_info = [f for f in files_info if f['name'] != filename]
        with open(UPLOADED_FILES_FILE, 'w') as f:
            json.dump(files_info, f, indent=2)
            
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    message = request.form.get('message', '')
    use_web = request.form.get('web_search', 'false') == 'true'
    coder_reasoner_active = request.form.get('coder_reasoner', 'false') == 'true'
    
    active_files = request.form.getlist('active_files')
    file = request.files.get('file')
    uploaded = None

    if file:
        message, uploaded = handle_uploaded_file(file, message)
        if isinstance(message, str) and message.startswith("Error uploading"):
            return jsonify({'choices': [{'message': {'content': message}}]})

    if active_files:
        try:
            with open(UPLOADED_FILES_FILE, 'r') as f:
                files_info = json.load(f)

            for filename in active_files:
                file_info = next((f for f in files_info if f['name'] == filename), None)
                if file_info and os.path.exists(file_info['path']):
                    try:
                        with open(file_info['path'], 'r', encoding='utf-8') as f:
                            file_content = f.read()
                        message = f"[File Context: {filename}]\n{file_content}\n\n{message}"
                    except UnicodeDecodeError:
                        message = f"[File Context: {filename} - Binary content not shown]\n\n{message}"
        except Exception as e:
            app.logger.error(f"Error processing active_files: {e}")

    final_persona = persona
    history = load_history()
    msgs = transform_history_for_gemini(history)
    msgs.append({'role': 'user', 'parts': [{'text': message}]})
    
    reply = ''

    try:
        if use_web:
            reply = web_search(msgs)
        elif coder_reasoner_active:
            thoughts = ""
            answer = ""
            # Use the streaming API with thinking_config
            stream = client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=msgs,
                config=types.GenerateContentConfig(
                    temperature=0.7, 
                    system_instruction=final_persona,
                    thinking_config=types.ThinkingConfig(
                        include_thoughts=True
                    )
                ),
                
            )
            for chunk in stream:
                for part in chunk.candidates[0].content.parts:
                    if hasattr(part, 'thought') and part.thought:
                        thoughts += part.text
                    elif hasattr(part, 'text'):
                        answer += part.text
            
            # Combine thoughts and answer for the UI
            if thoughts:
                reply = f"Seele-Coder-Reasoner Thoughts:\n{thoughts.strip()}\n---END-OF-THOUGHTS---\n{answer.strip()}"
            else:
                reply = answer.strip()

        else: # Standard non-reasoner response
            resp = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=msgs,
                config=types.GenerateContentConfig(temperature=0.7, system_instruction=persona)
            )
            reply = resp.text or 'Error generating response.'

    except Exception as e:
        app.logger.error(f'Gemini API error: {e}')
        reply = f'An error occurred: {e}'


    # Process terminal commands if any are found in the reply
    reply = process_terminal_commands(reply, msgs, final_persona)

    history.extend([
        {'role': 'user', 'content': message},
        {'role': 'assistant', 'content': reply}
    ])
    save_history(history)

    return jsonify({'choices': [{'message': {'content': reply}}]})

# ─── History Handlers ─────────────────────────────────────────────────────────────

@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify(load_history())


@app.route('/api/clear_history', methods=['POST'])
def clear_history():
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
    return jsonify({'status': 'success', 'message': 'History cleared.'})

# ─── Static Handler ─────────────────────────────────────────────────────────────

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory("./", filename)


# ─── Server Control Endpoints ────────────────────────────────────────────────
@app.route('/health')
def health_check():
    """Endpoint for status monitoring"""
    return jsonify({
        "status": "running",
        "port": 5001,
        "terminal_active": isinstance(global_terminal, TerminalSession)
    }), 200

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Clean shutdown endpoint"""
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()
    return jsonify({"status": "shutting down"}), 200

# ─── Main Server Runner ──────────────────────────────────────────────────────
def run_server():
    """Configure and start Flask server"""
    port = 5008
    app.run(
        host='0.0.0.0',
        port=port,
        threaded=True,
        debug=False,
        use_reloader=False
    )

if __name__ == '__main__':
    print("Starting Seele in development mode...")
    run_server()