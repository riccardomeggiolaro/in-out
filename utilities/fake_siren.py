from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse
import json

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse.urlparse(self.path)
        path = parsed.path
        query = urlparse.parse_qs(parsed.query)

        if path == "/rpc/Switch.Set":
            switch_id = query.get("id", ["?"])[0]
            on_status = query.get("on", ["?"])[0]

            response = {
                "status": "ok",
                "id": switch_id,
                "on": on_status
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

print("Server in ascolto su 0.0.0.0:8000")
server = HTTPServer(("0.0.0.0", 8000), RequestHandler)
server.serve_forever()