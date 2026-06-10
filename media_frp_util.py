import os
import subprocess
import time
import requests
from uuid_config import UUIDConfig


def get_domain():
    uuid_config_instance = UUIDConfig()
    uuid_value = uuid_config_instance.get_uuid()
    return uuid_value + ".yunfrp.net"


def download_frp():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    frpc_path = os.path.join(current_directory, "frpc.exe")
    if os.path.exists(frpc_path):
        return True

    url = "https://source.poly-ai.chat/frp/frpc.exe"
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        with open(frpc_path, "wb") as f:
            f.write(r.content)
        return True
    except Exception:
        return False


def setup_frp_and_keep_alive(port=8000, frp_config=None, stop_event=None):
    """
    Setup FRP tunnel for remote access to the media server.
    Flask + SocketIO (HTTP + WebSocket signaling) both run on the same port,
    so only one FRP proxy entry is needed.

    Args:
        port (int): Local port where Flask media server is running
        frp_config (str): Path to FRP configuration file
        stop_event (threading.Event): Signal to stop the keep-alive loop
    """
    print(f"DEBUG: setup_frp called with local_port={port}, frp_config={frp_config}")

    if frp_config is None:
        frp_domain = get_domain()
        frp_config_content = f'''
            serverAddr = "129.213.174.213"
            serverPort = 7000

            webServer.addr = "127.0.0.1"
            webServer.port = 7400

            log.level = "debug"
            log.to = "./frpc.log"

            [transport]
            heartbeatInterval = 30
            heartbeatTimeout = 90
            tcpMux = true
            tcpMuxKeepaliveInterval = 30

            [[proxies]]
            name = "{frp_domain}"
            type = "https"
            customDomains = ["{frp_domain}"]

            [proxies.plugin]
            type = "https2http"
            localAddr = "127.0.0.1:{port}"
            crtPath = "./yunfrp_net.crt"
            keyPath = "./yunfrp_net.key"
            hostHeaderRewrite = "127.0.0.1"
        '''
        frp_config = "frpc.toml"
        with open(frp_config, 'w') as f:
            f.write(frp_config_content.strip())

        print(f"Started FRP tunnel using config: {frp_config_content}")

    frp_process = None
    try:
        current_directory = os.path.dirname(os.path.abspath(__file__))
        frpc_path = os.path.join(current_directory, "frpc.exe")
        frp_process = subprocess.Popen(
            [frpc_path, '-c', frp_config],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        while not (stop_event and stop_event.is_set()):
            poll_result = frp_process.poll()

            if poll_result is not None:
                if stop_event and stop_event.is_set():
                    break
                frp_process = subprocess.Popen(
                    [frpc_path, '-c', frp_config],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
                continue

            time.sleep(1)
    except Exception:
        print(f"Error: FRP client not found at {frpc_path}.")
        print("Please ensure frpc.exe is in the media-file-server directory")
    finally:
        if frp_process and frp_process.poll() is None:
            frp_process.terminate()
            try:
                frp_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                frp_process.kill()
            print("[FRP] frpc stopped.")


def setup_frp(port=8000, stop_event=None):
    """Download FRP client if needed, then start the FRP tunnel in a background thread."""
    if not download_frp():
        print("Error: Failed to download frpc.exe")
        return

    import threading
    frp_thread = threading.Thread(target=setup_frp_and_keep_alive, args=(port, None, stop_event), daemon=False)
    frp_thread.start()