import mido
import os

def get_bpm(file_path):
    try:
        mid = mido.MidiFile(file_path)
        # The first tempo change usually defines the initial BPM
        for track in mid.tracks:
            for msg in track:
                if msg.type == 'set_tempo':
                    return mido.tempo2bpm(msg.tempo)
        return "Unknown"
    except Exception as e:
        return f"Error: {e}"

mid_dirs = [
    "/run/media/fabio/Dados/Fabio/kof98_port_snes/music",
    "/run/media/fabio/Dados/Fabio/kof98_port_snes/assets/survival_ending"
]

for d in mid_dirs:
    if os.path.exists(d):
        for f in os.listdir(d):
            if f.endswith(".mid"):
                path = os.path.join(d, f)
                bpm = get_bpm(path)
                print(f"{f} | {bpm}")
