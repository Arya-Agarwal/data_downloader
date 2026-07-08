import os
import webbrowser
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer

from kiteconnect import (
    KiteConnect,
    KiteTicker
)

from dotenv import load_dotenv

from core.logger import log


load_dotenv()


class TokenHandler(BaseHTTPRequestHandler):

    request_token = None

    def do_GET(self):

        query = parse_qs(
            urlparse(
                self.path
            ).query
        )

        if "request_token" in query:

            TokenHandler.request_token = (
                query["request_token"][0]
            )

            self.send_response(200)
            self.end_headers()

            self.wfile.write(
                b"Login successful. You can close this window."
            )

            log.info(
                "Captured request token."
            )

        else:

            self.send_response(400)
            self.end_headers()

            self.wfile.write(
                b"Request token not found."
            )


def read_env():

    return {

        "api_key":
            os.getenv(
                "KITE_API_KEY"
            ),

        "api_secret":
            os.getenv(
                "KITE_API_SECRET"
            ),

        "access_token":
            os.getenv(
                "KITE_ACCESS_TOKEN"
            ),

        "redirect_url":
            os.getenv(
                "KITE_REDIRECT_URL"
            )

    }


def update_access_token(
    new_token
):

    env_path = ".env"

    with open(
        env_path,
        "r"
    ) as file:

        lines = file.readlines()

    with open(
        env_path,
        "w"
    ) as file:

        for line in lines:

            if line.startswith(
                "KITE_ACCESS_TOKEN="
            ):

                file.write(
                    f"KITE_ACCESS_TOKEN={new_token}\n"
                )

            else:

                file.write(
                    line
                )

    load_dotenv(
        override=True
    )

    log.info(
        "Updated access token in .env"
    )


def validate_token():

    creds = read_env()

    if not creds["access_token"]:

        return False

    try:

        kite = KiteConnect(
            api_key=creds["api_key"]
        )

        kite.set_access_token(
            creds["access_token"]
        )

        kite.profile()

        log.info(
            "Access token valid."
        )

        return True

    except Exception as e:

        log.warning(
            f"Token invalid: {e}"
        )

        return False


def login_and_generate_token():

    TokenHandler.request_token = None

    creds = read_env()

    kite = KiteConnect(
        api_key=creds["api_key"]
    )

    login_url = kite.login_url()

    log.info(
        "Opening Zerodha login page..."
    )

    server = HTTPServer(
        (
            "localhost",
            8000
        ),
        TokenHandler
    )

    webbrowser.open(
        login_url
    )

    try:

        while TokenHandler.request_token is None:

            server.handle_request()

    finally:

        server.server_close()

    request_token = (
        TokenHandler.request_token
    )

    session = kite.generate_session(

        request_token=request_token,

        api_secret=creds[
            "api_secret"
        ]

    )

    access_token = session[
        "access_token"
    ]

    update_access_token(
        access_token
    )

    kite.set_access_token(
        access_token
    )

    log.info(
        "Login successful."
    )

    return kite


def get_kite():

    if validate_token():

        creds = read_env()

        kite = KiteConnect(
            api_key=creds["api_key"]
        )

        kite.set_access_token(
            creds["access_token"]
        )

        return kite

    log.info(
        "Access token expired. Starting login..."
    )

    return login_and_generate_token()


def get_kite_ticker():
    """
    Returns an authenticated
    KiteTicker instance.
    """

    kite = get_kite()

    creds = read_env()

    return KiteTicker(

        api_key=creds[
            "api_key"
        ],

        access_token=kite.access_token

    )