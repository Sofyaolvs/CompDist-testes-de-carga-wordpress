# Relatório – Testes de Desempenho com o Link Extractor

## 1. Objetivo

Comparar o serviço de extração de links do Link Extractor em duas implementações (**Python** e **Ruby**), com e sem cache (**Redis**), sob carga crescente de usuários virtuais.

## 2. Ferramenta de carga: Locust

O Locust descreve o usuário virtual em Python (`locust/locustfile.py`). Cada usuário executa, em loop, uma sequência de **10 invocações** a `GET /api/sites/pagina-N.html` (N = 1…10, uma URL diferente a cada chamada), com pausa de 1–2 s entre elas.

```python
URLS = [f"sites/pagina-{n}.html" for n in range(1, 11)]

class LinkExtractorUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def extrair_links(self):
        for url in URLS:
            with self.client.get("/api/" + url, name="/api/<url>", catch_response=True) as resp:
                if resp.status_code != 200:
                    resp.failure(f"status {resp.status_code}")
                elif not resp.json():
                    resp.failure("lista de links vazia")
            self.wait()
```

Execução headless (`--headless`), 60 s por teste, entrada de usuários a 50/s (ou menos, se houver menos de 50), métricas gravadas em CSV (`--csv`).

## 3. Ambiente e cenários

- Serviço `sites`: 10 páginas HTML locais, 40 links cada, com **300 ms** de latência simulada (substitui a web real e torna o teste reprodutível).
- As duas APIs: mesmo limite (1 CPU / 512 MB) e mesma concorrência, 4 processos × 4 threads (Gunicorn `gthread` / Puma `-t 4:4`).
- Python: Flask + requests + BeautifulSoup. Ruby: Sinatra + Net::HTTP + Nokogiri.
- Com cache: consulta o Redis e, se não achar, extrai e grava. Sem cache (`CACHE=off`): sempre extrai da página.
- Antes de cada execução, Redis limpo e API recriada.

Matriz: 2 versões × 2 modos de cache × 4 cargas (10, 50, 100, 500 usuários) = **16 execuções**. O front-end PHP não foi usado; o Locust chama a API diretamente.

## 4. Resultados

Fonte: `results/graficos/resumo.csv` (tempos em segundos; todas as 16 execuções tiveram 0 falhas).

| Versão | Cache | Usuários | Média | Mediana | p95 | Req/s | Requisições |
|---|---|---:|---:|---:|---:|---:|---:|
| Python | sem | 10 | 0,325 | 0,320 | 0,35 | 5,2 | 304 |
| Python | sem | 50 | 0,718 | 0,670 | 1,3 | 21,3 | 1255 |
| Python | sem | 100 | 0,720 | 0,700 | 1,3 | 42,6 | 2507 |
| Python | sem | 500 | 7,214 | 7,800 | 9,6 | 49,4 | 2916 |
| Python | com | 10 | 0,044 | 0,006 | 0,32 | 6,2 | 362 |
| Python | com | 50 | 0,008 | 0,006 | 0,014 | 30,9 | 1817 |
| Python | com | 100 | 0,007 | 0,005 | 0,012 | 61,8 | 3636 |
| Python | com | 500 | 0,011 | 0,004 | 0,054 | 283,3 | 16701 |
| Ruby | sem | 10 | 0,318 | 0,310 | 0,33 | 5,3 | 308 |
| Ruby | sem | 50 | 0,392 | 0,320 | 0,65 | 25,1 | 1476 |
| Ruby | sem | 100 | 1,566 | 1,200 | 2,1 | 31,0 | 1827 |
| Ruby | sem | 500 | 1,597 | 1,200 | 2,0 | 31,1 | 1824 |
| Ruby | com | 10 | 0,041 | 0,006 | 0,32 | 6,1 | 358 |
| Ruby | com | 50 | 0,016 | 0,006 | 0,046 | 31,0 | 1825 |
| Ruby | com | 100 | 0,048 | 0,010 | 0,17 | 60,2 | 3545 |
| Ruby | com | 500 | 0,760 | 0,620 | 1,0 | 77,9 | 4594 |

Gráficos (em `results/graficos/`): `tempo_medio_por_usuarios.png`, `tempo_mediana_por_usuarios.png`, `tempo_p95_por_usuarios.png`, `requisicoes_por_segundo_por_usuarios.png`, `taxa_de_falhas_por_usuarios.png`.

## 5. Análise

1. **O cache é o fator dominante.** Sem cache, toda chamada paga os ~300 ms da página de origem; com cache a mediana cai para 4–10 ms (até 100 usuários). Com 500 usuários, o Python passa de 7,2 s para 11 ms de média.
2. **Sem cache, as duas versões saturam por I/O.** Com 16 threads e 300 ms por extração, o teto teórico é ~53 req/s. O Python chegou a 49 req/s com 500 usuários (tempo médio de 7,2 s, pela fila). O Ruby estabilizou em ~31 req/s, ou seja, gasta mais tempo por extração (Net::HTTP + Nokogiri).
3. **Com cache, o Python escala melhor.** Em 500 usuários, o Python serviu 283 req/s com p95 de 54 ms; o Ruby saturou em ~78 req/s, com média de 0,76 s. Até 100 usuários a vazão das duas é praticamente igual (~60 req/s), embora o Ruby já tenha p95 maior (0,17 s contra 0,012 s).
4. **Com 10 usuários** as diferenças são pequenas: a média com cache (~40 ms) é puxada pelas primeiras chamadas, que são cache miss (a mediana é 6 ms).
5. **Nenhuma execução teve falhas.**

## 6. Limitações e observações

- Locust, APIs, Redis e páginas de teste rodam na mesma máquina, então os valores absolutos dependem do hardware; vale a comparação relativa.
- Cada configuração foi executada **uma vez** (sem repetições), então não há intervalo de confiança.
- No Ruby sem cache, o tempo médio não cresce entre 100 e 500 usuários (1,57 s e 1,60 s) enquanto o Python cresce. Não investiguei a causa; pode estar ligada ao modo como o Puma enfileira conexões keep-alive. O número de requisições concluídas é praticamente idêntico, então o teto de vazão é o que vale comparar.
- **Correção durante o trabalho:** uma primeira rodada com Puma de 1 thread e Gunicorn de workers síncronos foi descartada. O Puma ficava preso a conexões keep-alive (respostas de até 20 s), o que fazia o Ruby parecer mais lento por motivo alheio ao cache. Também foi preciso aumentar o keep-alive do Gunicorn para 30 s para evitar conexões fechadas (status 0). A rodada final usa a configuração igual para as duas versões.
- Parâmetros de comparação (4 × 4 threads, 1 CPU, 300 ms de latência da página) são escolhas do trabalho, não propriedades das linguagens.
