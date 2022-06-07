import http.server
import socketserver
import jwt
import urllib.request
import json
import sys
import datetime
from jwt.exceptions import InvalidTokenError

PORT = 8000

url = sys.argv[1]
valid_scopes = sys.argv[2:]
response = urllib.request.urlopen(url + '/.well-known/openid-configuration')
config = json.load(response)
response = urllib.request.urlopen(config['jwks_uri'])
text = response.read().decode('utf-8')
j = json.loads(text)
public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(j['keys'][0]))


class JwtHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/healthz":
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

            decoded = jwt.decode(token, public_key, audience=url + '/resources', issuer=url,
                                 algorithms=['RS256'])  # , options={'verify_exp': False})

            scope_claims = decoded['scope']
            if valid_scopes:
                if not any(val in scope_claims for val in valid_scopes):
                    raise InvalidTokenError('Invalid scope ' + str(scope_claims) + ' not in ' + str(valid_scopes))

            self.send_response(200)
            self.send_header("Content-type", "text/plain")

            for key, value in decoded.items():
                self.send_header("X-JWT-" + key, str(value))

            self.end_headers()

            self.wfile.write(bytes(str(decoded), "utf8"))
        except Exception as e:
            st = datetime.datetime.utcnow()
            print(str(st) + " e: " + repr(e))
            self.send_response(401)
            self.end_headers()
            self.wfile.write(bytes(str(e), "utf8"))
        return


with socketserver.TCPServer(("", PORT), JwtHandler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()
