from firebase_admin import initialize_app, firestore, auth
from firebase_functions import https_fn
from firebase_functions.options import set_global_options

import https_method_handlers

set_global_options(max_instances=2)
initialize_app()
db = firestore.client()

@https_fn.on_request()
def on_request(req: https_fn.Request) -> https_fn.Response:
    if not is_authenticated(req):
        return https_fn.Response(status=401)

    match req.method:
        case "GET":
            return https_method_handlers.get(req, db)
        case "POST":
            return https_method_handlers.post(req, db)
        case "PUT":
            return https_method_handlers.put(req, db)
        case "DELETE":
            return https_method_handlers.delete(req, db)

    return https_fn.Response(status=405)

def is_authenticated(req: https_fn.Request) -> bool:
    authorization = req.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return False
    token = authorization.split("Bearer ")[1]

    try:
        auth.verify_id_token(token)
        return True
    except (
        ValueError,
        auth.InvalidIdTokenError,
        auth.ExpiredIdTokenError,
        auth.RevokedIdTokenError,
        auth.CertificateFetchError,
        auth.UserDisabledError,
    ):
        return False