import os
import re
from urllib.parse import urlparse

from locust import HttpUser, task, between

# Cada cenário é um post criado por scripts/setup.sh (identificado pelo slug).
# O cenário é escolhido pela variável de ambiente SCENARIO.
SCENARIOS = {
    "1": {"slug": "cenario-1-imagem-1mb", "imagem": True},
    "2": {"slug": "cenario-2-texto-400kb", "imagem": False},
    "3": {"slug": "cenario-3-imagem-300kb", "imagem": True},
}

SCENARIO = SCENARIOS[os.environ.get("SCENARIO", "1")]
IMG_SRC = re.compile(r'<img[^>]+src="([^"]*/wp-content/uploads/[^"]+)"')


class WebsiteUser(HttpUser):
    wait_time = between(1, 3)  # tempo de "leitura" entre uma página e outra

    @task
    def ler_post(self):
        # GET <HOST_DO_WORDPRESS>/<slug>/
        with self.client.get("/" + SCENARIO["slug"] + "/", name="post",
                             catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"status {resp.status_code}")
                return
            imagens = IMG_SRC.findall(resp.text) if SCENARIO["imagem"] else []
            if SCENARIO["imagem"] and not imagens:
                resp.failure("imagem não encontrada no post")
                return
        # Como um navegador, baixa as imagens referenciadas pelo post
        for src in imagens:
            self.client.get(urlparse(src).path, name="imagem")
