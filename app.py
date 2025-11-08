from bottle import Bottle, request, static_file

app = Bottle()

MIL_NUMBER = "+46705152223"        # your wife's number for this test
FALLBACK_NUMBER = "+46733466657"   # fallback mobile

@app.get("/")
def health():
    return "ok"

@app.get("/audio/<filename>")
def serve_audio(filename: str):
    return static_file(filename, root="/app/audio", mimetype="audio/mpeg")

@app.post("/calls")
def calls():
    from_number = (request.forms.get("from") or "").replace(" ", "")
    # Optional: debug log
    print(f"from={from_number} mil={MIL_NUMBER}")

    if from_number == MIL_NUMBER:
        return {
            "play": "https://calls.mtup.xyz/audio/Aha-remix.mp3"
        }

    return {
        "connect": FALLBACK_NUMBER
    }
