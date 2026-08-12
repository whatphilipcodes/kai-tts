import socket
from pathlib import Path

from voxcpm import VoxCPM

HOST = "127.0.0.1"
PORT = 5005

ref = Path(__file__).resolve().parent.parent / "resources" / "source-ilja.wav"

ref_text_ilja = "Das Scheinwerferlicht bricht sich in der Stille des großen Hauses, während der Vorhang langsam beiseite gleitet. In diesem flüchtigen Moment zwischen Realität und Illusion verschmelzen die Worte des Dramas mit der Präsenz des Schauspielers, um das Publikum in eine Welt voll dramatischer Tiefe und ungeahnter Leidenschaft zu entführen."
ref_text_philip = "Ich muss mal ausprobieren wie meine Stimme jetzt durch dieses System klingt weil das habe ich nämlich actually noch gar nicht gemacht und das sind ja jetzt doch ein paar Neuerungen dazu gekommen insofern hat es ja vielleicht 'nen überraschenden Effekt."

ref_text_rt = "Wir wohnten der Generalprobe unserer eigenen Beerdigung bei - Unglücklicherweise erlebt dieses Abenteuer das allen gemeinsam ist jeder allein."
ref_text_kinski = "Nein, er hat nicht gesagt halt die Schnauze. Er hat eine Peitsche genommen und hat ihm in die Fresse gehauen!"


def main():
    print("Initializing VoxCPM2 model on WSL...")
    model = VoxCPM.from_pretrained(
        "openbmb/VoxCPM2",
        load_denoiser=True,
    )
    sample_rate = model.tts_model.sample_rate

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Listening on port {PORT}. Awaiting Mac client connection...")

        conn, addr = s.accept()
        with conn:
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            print(f"Client connected from {addr}")

            conn.sendall(int(sample_rate).to_bytes(4, byteorder="big"))

            while True:
                try:
                    user_input = input("\nInput: ")
                except KeyboardInterrupt, EOFError:
                    break

                if user_input.strip().lower() == "exit":
                    break
                if not user_input.strip():
                    continue

                for chunk in model.generate_streaming(
                    text=user_input,
                    prompt_wav_path=ref,
                    prompt_text=ref_text_ilja,
                    reference_wav_path=ref,
                ):
                    data = chunk.tobytes()
                    conn.sendall(len(data).to_bytes(4, byteorder="big"))
                    conn.sendall(data)


if __name__ == "__main__":
    main()
