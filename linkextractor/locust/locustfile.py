from locust import HttpUser, task, between

# 10 páginas diferentes, servidas pelo contêiner "sites"
URLS = [f"sites/pagina-{n}.html" for n in range(1, 11)]


class LinkExtractorUser(HttpUser):
    wait_time = between(1, 2)  # pausa entre uma invocação e outra

    @task
    def extrair_links(self):
        # Sequência de 10 invocações ao serviço de extração, uma URL diferente a cada vez
        for url in URLS:
            with self.client.get("/api/" + url, name="/api/<url>", catch_response=True) as resp:
                if resp.status_code != 200:
                    resp.failure(f"status {resp.status_code}")
                elif not resp.json():
                    resp.failure("lista de links vazia")
            self.wait()
