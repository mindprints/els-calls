from bottle import request, post, get, default_app

MIL_NUMBER = "+46123456789"       # test: pretend this is your mother-in-law
FALLBACK_NUMBER = "+46733466657"  # your real mobile for now

@get("/")
def health():
    return "ok"

@post("/calls")
def calls():
    from_number = (request.forms.get("from") or "").replace(" ", "")

    if from_number == MIL_NUMBER:
        return {
            "play": "https://mtup.xyz"  # placeholder until your MP3 is ready
        }

    return {
        "connect": FALLBACK_NUMBER
    }

app = default_app()

