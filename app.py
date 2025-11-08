from bottle import Bottle, request, static_file

app = Bottle()

# TODO: set these to real numbers in E.164 format
MIL_NUMBER = "+46705152223"        # mother-in-law test number
FALLBACK_NUMBER = "+46733466657"   # your mobile

@app.get("/")
def health():
    return "ok"

@app.get("/audio/<filename>")
def serve_audio(filename: str):
    # WORKDIR in Dockerfile is /app, so this is correct
    return static_file(filename, root="/app/audio", mimetype="audio/mpeg")

@app.post("/calls")
def calls():
    from_number = (request.forms.get("from") or "").replace(" ", "")

    if from_number == MIL_NUMBER:
        # exact filename, case-sensitive
        return {
            "play": "https://calls.mtup.xyz/audio/Aha-remix.mp3"
        }

    return {
        "connect": FALLBACK_NUMBER
    }
