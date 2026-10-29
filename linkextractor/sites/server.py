"""Servidor de páginas de teste: /pagina-1.html ... /pagina-10.html, cada uma com 40 links.

SITE_DELAY_MS simula a latência de uma página da web real (o que o cache do Link Extractor evita).
Usar páginas locais deixa o teste determinístico, sem depender da internet.
"""
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DELAY = int(os.environ.get("SITE_DELAY_MS", "300")) / 1000
PAGINAS = 10
LINKS = 40


def pagina(n):
    links = "\n".join(
        f'<li><a href="http://exemplo{(n + k) % 7}.org/pagina-{n}/item-{k}">Link {k}</a></li>'
        for k in range(LINKS - 1))
    links += f'\n<li><a href="/pagina-{n % PAGINAS + 1}.html">Próxima página</a></li>'
    return f"<html><head><title>Página {n}</title></head><body><h1>Página {n}</h1><ul>\n{links}\n</ul></body></html>"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        n = self.path.removeprefix("/pagina-").removesuffix(".html")
        if not (self.path.startswith("/pagina-") and n.isdigit() and 1 <= int(n) <= PAGINAS):
            self.send_error(404)
            return
        time.sleep(DELAY)
        corpo = pagina(int(n)).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 80), Handler).serve_forever()
