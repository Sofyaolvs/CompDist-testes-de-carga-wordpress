"""Serviço de extração de links (versão Python): GET /api/<url> -> JSON com os links da página."""
import json
import os
from urllib.parse import urljoin

import redis
import requests
from bs4 import BeautifulSoup
from flask import Flask, Response

app = Flask(__name__)
app.url_map.merge_slashes = False  # preserva o "//" de http://

USAR_CACHE = os.environ.get("CACHE", "on") == "on"
cache = redis.Redis(host=os.environ.get("REDIS_HOST", "redis"), port=6379)


def normalizar(url):
    return url if url.startswith(("http://", "https://")) else "http://" + url


def extrair_links(url):
    html = requests.get(url, timeout=30).text
    soup = BeautifulSoup(html, "html.parser")
    return [urljoin(url, a["href"]) for a in soup.find_all("a", href=True)]


@app.route("/health")
def health():
    return "ok"


@app.route("/api/<path:url>")
def api(url):
    url = normalizar(url)
    corpo = cache.get(url) if USAR_CACHE else None
    if corpo is None:
        corpo = json.dumps(extrair_links(url))
        if USAR_CACHE:
            cache.set(url, corpo)
    return Response(corpo, mimetype="application/json")
