from bottle import request, post, get, default_app

MIL_NUMBER = "+46123456789"       # test value
FALLBACK_NUMBER = "+46111111111"  # test value

@get("/")
def health():
    return "ok"

@post("/calls")
def calls():
    from_number = (request.forms.get("from") or "").replace(" ", "")
    if from_number == MIL_NUMBER:
        return {"play": "https://mtup.xyz"}  # placeholder URL
    return {"connect": FALLBACK_NUMBER}

app = default_app()
