import http.server
import socketserver
import os

PORT = 8000

Handler = http.server.SimpleHTTPRequestHandler

httpd = socketserver.TCPServer(("", PORT), Handler)
os.chdir("website")

print("Serving at port", PORT)
httpd.serve_forever()
