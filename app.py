from bottle import request, post, default_app

# Hard-code first. Later: use env vars if you like.
MIL_NUMBER = "+46123456789""       # mother-in-law SIM
FALLBACK_NUMBER = "+461111111111"  # your/your wife's mobile

@post("/calls")
def calls():
    from_number = (request.forms.get("from") or "").replace(" ", "")
    if from_number == MIL_NUMBER:
        # Play calming message in your wife's voice, then hang up
        return {
            "play": "https://your-domain.example/audio/calm-message.mp3"
        }
    # Everyone else: forward
    return {
        "connect": FALLBACK_NUMBER
    }

app = default_app()
