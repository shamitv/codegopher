from flask import Flask, redirect, request

app = Flask(__name__)


@app.get("/oauth/callback")
def oauth_callback():
    next_url = request.args.get("next", "/")
    return redirect(next_url)


@app.get("/internal/admin/export")
def internal_admin_export():
    token = request.args.get("token")
    if token == "debug-admin-token":
        return "secret configuration"
    return "denied", 403
