import socket
import numpy as np
import sounddevice as sd
import queue
import threading
import time

HOST = "127.0.0.1"
PORT = 5005
# Increase this value if you still hear stuttering; decrease it to lower latency
PREBUFFER_CHUNKS = 3


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Disable Nagle's algorithm
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

        # Thread-safe queue to pass audio data between the network and audio hardware
        audio_queue = queue.Queue()

        def playback_thread():
            # Wait until the initial buffer is filled before starting the stream
            while audio_queue.qsize() < PREBUFFER_CHUNKS:
                time.sleep(0.05)

            # OutputStream handles the underlying C-level ring buffer automatically
            with sd.OutputStream(
                samplerate=sample_rate, channels=1, dtype="float32"
            ) as stream:
                while True:
                    chunk = audio_queue.get()
                    if chunk is None:  # Termination signal
                        break
                    # .write() blocks if the hardware buffer is full, ensuring perfect timing
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

            # Add new chunks to the queue for the playback thread
            audio_queue.put(chunk)


if __name__ == "__main__":
    main()
