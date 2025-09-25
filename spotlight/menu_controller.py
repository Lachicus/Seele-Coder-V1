#!/usr/bin/env python3
import subprocess
import os
import signal
import threading
import time
import socket

class SeeleController:
    def __init__(self):
        self.basedir = os.path.dirname(os.path.abspath(__file__))
        self.flask_process = None
        self.log_path = os.path.join(self.basedir, "flask.log")
        

    def get_local_ip(self):
        """Return the local IP address of this machine."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # Doesn't need to be reachable
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
        

    def start_flask(self):
        if self.flask_process:
            print("Flask server already running.")
            return

        python_path = os.path.join(self.basedir, "myenv", "bin", "python3")
        app_path = os.path.join(self.basedir, "app.py")

        self.flask_process = subprocess.Popen(
            [python_path, app_path],
            preexec_fn=os.setsid,
            stdout=open(self.log_path, "a"),
            stderr=subprocess.STDOUT
        )

        print(f"[SeeleAI] Access SeeleAI : http://{self.get_local_ip()}:5001")
        print("[SeeleAI] Flask Server started.")

    def stop_flask(self):
        if self.flask_process:
            os.killpg(os.getpgid(self.flask_process.pid), signal.SIGTERM)
            subprocess.run(["pkill", "-f", "app.py"])
            self.flask_process = None
            print("[SeeleAI] Flask server stopped.")

    def tail_logs(self):
        """Continuously print new log lines to stdout."""
        with open(self.log_path, "r") as f:
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if line:
                    print(line.strip(), flush=True)
                else:
                    time.sleep(0.5)

def main():
    controller = SeeleController()
    controller.start_flask()


    log_thread = threading.Thread(target=controller.tail_logs, daemon=True)
    log_thread.start()


if __name__ == "__main__":
    main()
