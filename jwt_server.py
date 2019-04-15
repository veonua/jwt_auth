import http.server
import socketserver
import jwt
import urllib.request
import json
import sys
import os
from argparse import ArgumentParser
from jwt.exceptions import InvalidTokenError



parser = ArgumentParser()
parser.add_argument('-p', '--port', type=int, default=int(os.getenv('JWT_SERVER_PORT', 8000)), help='Used Port. Defaults to environment variable JWT_SERVER_PORT or 8000')
parser.add_argument('-a', '--audience', default=os.getenv('JWT_AUDIANCE'), help='JWT Audiance. Defaults to environment variable JWT_AUDIANCE. Mandatory')
parser.add_argument('-i', '--issuer', default=os.getenv('JWT_ISSUER'), help='JWT Issuer. Defaults to enviroment variable JWT_ISSUER. Mandatory')
parser.add_argument('-j', '--jwks', default=os.getenv('JWT_KEY_URL'), help='JWT URL to fetch public keys. Defaults to enviroment variable JWT_KEY_URL. Mandatory')
parser.add_argument('--scopeparam', default=os.getenv('JWT_SCOPE_PARAM', 'scope'), help='JWT Scope parameter. Default to environment variable JWT_SCOPE_PARAM or "scope"')
parser.add_argument('-s', '--scope', default=os.getenv('JWT_SCOPE'), help='Whitespace seperated list of allowed scopes. Default to environment variable JWT_SCOPES')

args = parser.parse_args()

response = urllib.request.urlopen(args.jwks)
text = response.read().decode('utf-8')
j = json.loads(text)
public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(j['keys'][0]))

class JwtHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path=="/healthz":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            return

        try:
            authorization = self.headers.get("authorization")
            auth_header = authorization.split()

            if auth_header[0].lower() != 'bearer' or len(auth_header) == 1:
                self.end_headers()
                return

            token = auth_header[1]

            decoded = jwt.decode(token, public_key, audience=args.audience, issuer=args.issuer, algorithms=['RS256']) #, options={'verify_exp': False})
            if args.scopeparam in decoded:
                scope_claims = decoded[args.scopeparam]
                if args.scope:
                    if not any(val in scope_claims for val in args.scope.split(' ')):
                        raise InvalidTokenError('Invalid scope '+str(scope_claims)+' not in '+str(args.scope))

            self.send_response(200)
            self.send_header("Content-type", "text/plain")

            for key, value in decoded.items():
                self.send_header("X-JWT-"+key, str(value))

            self.end_headers()

            self.wfile.write(bytes(str(decoded), "utf8"))
        except Exception as e:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(bytes(str(e), "utf8"))
        return

with socketserver.TCPServer(("", args.port), JwtHandler) as httpd:
    try:
        print("serving at port", args.port)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down")
        httpd.shutdown()
