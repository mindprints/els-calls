from bottle import Bottle, request, static_file

app = Bottle()

MIL_NUMBER = "+46123456789"        # test MIL
FALLBACK_NUMBER = "+46733466657"   # your mobile

@app.get("/")
def health():
    return "ok"

@app.get("/debug-audio")
def debug_audio():
    import os
    out = []
    for root, dirs, files in os.walk("/app"):
        if "audio" in root:
            for f in files:
                out.append(f"{root}/{f}")
    return "\n".join(out) or "no audio files found"

@app.get("/audio/<filename>")
def serve_audio(filename: str):
    # Workdir is /app, MP3 is in /app/audio
    return static_file(filename, root="/app/audio", mimetype="audio/mpeg")

@app.post("/calls")
def calls():
    from_number = (request.forms.get("from") or "").replace(" ", "")

    if from_number == MIL_NUMBER:
        return {
            "play": "https://calls.mtup.xyz/audio/Aha-remix.mp3"
        }

    return {
        "connect": FALLBACK_NUMBER
    }
