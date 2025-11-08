from bottle import request, post, get, static_file, default_app

MIL_NUMBER = "+46705152223"        # mother-in-law real SIM in E.164
FALLBACK_NUMBER = "+46733466657   # your / your wife's mobile

@get("/")
def health():
    return "ok"

@get("/audio/<filename>")
def audio(filename):
    # Serves files from ./audio inside the container
    return static_file(filename, root="./audio", mimetype="audio/mpeg")

@post("/calls")
def calls():
    from_number = (request.forms.get("from") or "").replace(" ", "")

    if from_number == MIL_NUMBER:
        return {
            "play": "https://calls.mtup.xyz/audio/Aha-remix.mp3"
            # no "next" → call ends after playback
        }

    return {
        "connect": FALLBACK_NUMBER
    }

app = default_app()
