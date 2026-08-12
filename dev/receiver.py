import queue
import socket
import threading
import time

import numpy as np
import sounddevice as sd

HOST = "127.0.0.1"
PORT = 5005
PREBUFFER_CHUNKS = 3


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        print(f"Connecting to WSL stream on {HOST}:{PORT}...")
        try:
            s.connect((HOST, PORT))
        except ConnectionRefusedError:
            print(
                "Connection refused. Ensure the WSL server is running and the port is tunneled."
            )
            return

        print("Connected. Awaiting audio stream...")

        sr_bytes = s.recv(4)
        sample_rate = int.from_bytes(sr_bytes, byteorder="big")

        audio_queue = queue.Queue()

        def playback_thread():
            while audio_queue.qsize() < PREBUFFER_CHUNKS:
                time.sleep(0.05)

            with sd.OutputStream(
                samplerate=sample_rate, channels=1, dtype="float32"
            ) as stream:
                while True:
                    chunk = audio_queue.get()
                    if chunk is None:  # Termination signal
                        break
                    stream.write(chunk)

        player = threading.Thread(target=playback_thread, daemon=True)
        player.start()

        while True:
            length_bytes = s.recv(4)
            if not length_bytes:
                break
            length = int.from_bytes(length_bytes, byteorder="big")

            data = b""
            while len(data) < length:
                packet = s.recv(length - len(data))
                if not packet:
                    break
                data += packet

            chunk = np.frombuffer(data, dtype=np.float32)
            audio_queue.put(chunk)


if __name__ == "__main__":
    main()
