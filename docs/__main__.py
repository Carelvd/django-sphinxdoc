import http.server
import socketserver
import functools

HOST = ""
PORT = 8000
DOCS = ".build/html"
        
Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DOCS)

with socketserver.TCPServer((HOST, PORT), Handler) as httpd:
    print(f"Serving {DOCS} through port {PORT}")
    httpd.serve_forever()
