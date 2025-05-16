import os
import signal
import subprocess
import time
import psutil

def kill_process_on_port(port):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.connections():
                if conn.laddr.port == port:
                    os.kill(proc.pid, signal.SIGTERM)
                    time.sleep(1)  # Give the process time to terminate
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def restart_server():
    # Kill any process running on port 5000
    kill_process_on_port(5000)
    
    # Start the Flask server
    subprocess.Popen(['python', 'run.py'])

if __name__ == '__main__':
    restart_server() 