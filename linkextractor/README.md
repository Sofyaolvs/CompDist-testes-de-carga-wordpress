# Trabalho 4 – Testes de Desempenho com o Link Extractor

Compara o serviço de extração de links em **Python** (Flask + Gunicorn) e **Ruby** (Sinatra + Puma), **com e sem cache** (Redis), variando o número de usuários virtuais. A ferramenta de carga é o Locust.

## Arquitetura

```
 Locust ──► api-python  (ou api-ruby) ──► sites (páginas de teste)
                 │
                 └──► redis (usado só nos testes "com cache")
```

O front-end PHP não participa: o enunciado pede testes do serviço de extração, então o Locust chama a API diretamente (`GET /api/<url>`).

## Arquivos

- `api-python/`, `api-ruby/` – as duas versões do serviço. Mesma lógica: com cache, consulta o Redis e, se não achar, extrai da página e grava; sem cache (`CACHE=off`), sempre extrai da página.
- `sites/server.py` – serve `pagina-1.html` … `pagina-10.html` (40 links cada) com latência simulada de 300 ms (`SITE_DELAY_MS`). Páginas locais tornam o teste reproduzível e independente da internet.
- `locust/locustfile.py` – usuário virtual: sequência de 10 invocações a `/api/sites/pagina-N.html`, uma URL diferente em cada, com pausa de 1–2 s entre elas; repete a sequência até o fim do teste.
- `scripts/run_tests.sh` – executa a matriz versão × cache × usuários.
- `scripts/gerar_graficos.py` – gera os gráficos e o `resumo.csv` a partir dos CSVs do Locust.

## Cenários

| Variável | Valores |
|---|---|
| Versão do serviço | Python, Ruby |
| Cache | com (Redis), sem |
| Usuários virtuais | 10, 50, 100, 500 (60 s cada) |

São 16 execuções (~25 min). A cada execução o Redis é limpo e a API é recriada. As duas APIs têm o mesmo limite (1 CPU / 512 MB) e 4 processos × 4 threads (Gunicorn `gthread` e Puma `-t 4:4`, ambos com keep-alive ≥ 20 s).

## Como executar

Em um terminal bash (Git Bash/WSL), com o Docker em execução, dentro de `linkextractor/`:

```bash
./scripts/run_tests.sh
docker compose --profile tools run --rm graficos
```

Parâmetros opcionais: `RUN_TIME=30s VERSOES="python" CACHES="on" USUARIOS="10 100"`.

## Resultados

- `results/<versão>_cache-<on|off>_u<usuários>_stats.csv` – estatísticas brutas do Locust (média, mediana, percentis).
- `results/graficos/<métrica>_por_usuarios.png` – tempo médio, mediana, p95, requisições/s e taxa de falhas; barras por versão × cache.
- `results/graficos/resumo.csv` – tabela-resumo.
