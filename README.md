# Trabalho 2 – WordPress com Múltiplas Instâncias usando Nginx e Docker Compose

## Arquitetura

```
              Máquina hospedeira (porta 80)
                          │
                    ┌─────▼─────┐
                    │   nginx   │  nginx:1.19.0 (balanceador)
                    └─────┬─────┘
        rede frontend     │
      ┌───────────────────┼───────────────────┐
┌─────▼──────┐     ┌──────▼─────┐     ┌───────▼────┐
│ wordpress1 │     │ wordpress2 │     │ wordpress3 │  wordpress:5.4.2-php7.2-apache
└─────┬──────┘     └──────┬─────┘     └───────┬────┘
      └───────────────────┼───────────────────┘
        rede backend      │
                    ┌─────▼─────┐
                    │    db     │  mysql:5.7
                    └───────────┘
```

## Arquivos

- `docker-compose.yml` – define os cinco contêineres, as redes e os volumes.
- `nginx.conf` – configuração do Nginx como balanceador de carga (montado em `/etc/nginx/nginx.conf`).
- `wordpress/` – pasta criada automaticamente na primeira execução; é o `/var/www/html` compartilhado.

## Como os requisitos foram atendidos

| Requisito | Solução |
|---|---|
| Imagens `mysql:5.7`, `wordpress:5.4.2-php7.2-apache`, `nginx:1.19.0` | Definidas em `image:` de cada serviço |
| Nginx balanceia entre wordpress1, 2 e 3 | Bloco `upstream wordpress` no `nginx.conf` |
| Todos os WordPress usam o mesmo MySQL | Mesmas variáveis `WORDPRESS_DB_*` apontando para `db` |
| WordPress não acessível pela máquina hospedeira | Serviços sem `ports:`; só o Nginx publica a porta 80 |
| MySQL acessível só pelos WordPress | Sem `ports:` e apenas na rede `backend`, onde o Nginx não está |
| WordPress compartilha `/var/www/html` com o host | Volume `./wordpress:/var/www/html` |
| Nginx mapeia essa pasta em `/usr/share/nginx/html` | Volume `./wordpress:/usr/share/nginx/html` |

## Como executar

```bash
docker compose up -d
docker compose ps
```

Acesse `http://localhost/` e conclua a instalação do WordPress.

## Como testar

Execute várias vezes:

```bash
curl -I http://localhost/
```

O cabeçalho `X-Upstream` alterna entre três IPs (ex.: `172.18.0.3:80`, `172.18.0.4:80`, `172.18.0.5:80`), que são os IPs dos contêineres WordPress. Para conferir os IPs:

```bash
docker inspect -f "{{.Name}} {{range .NetworkSettings.Networks}}{{.IPAddress}} {{end}}" wordpress1 wordpress2 wordpress3
```

No navegador: F12 → aba **Rede** → clique na requisição da página → cabeçalhos de resposta → `X-Upstream`.

## Encerrar

```bash
docker compose down        # mantém os dados
docker compose down -v     # apaga também o banco
```

---

# Trabalho 3 – Testes de Carga com o Locust

O Locust foi adicionado ao `docker-compose.yml` (serviço `locust`, imagem `locustio/locust:2.32.0`, rede `frontend`, alvo `http://nginx`). Os serviços do trabalho 3 usam `profiles`, então `docker compose up` continua subindo só a arquitetura do trabalho 2.

## Arquivos

- `locust/locustfile.py` – usuário que faz GET no post do cenário (`/<slug>/`) e, nos cenários com imagem, também baixa a imagem referenciada.
- `nginx-1.conf`, `nginx-2.conf`, `nginx.conf` – upstream com 1, 2 e 3 instâncias (escolhido pela variável `NGINX_CONF`).
- `scripts/setup.sh` – gera a mídia, sobe o ambiente, instala o WordPress (via WP-CLI), ativa o tema e cria os 3 posts.
- `tema/` – tema próprio "SD Moderno" (visual com cards e gradiente; só fontes do sistema, sem JS nem imagens, para não interferir nas medições).
- `scripts/run_tests.sh` – executa a matriz cenários × instâncias × usuários.
- `scripts/gerar_graficos.py` – gera os gráficos a partir dos CSVs do Locust.
- `conteudo/` – imagem de ~1 MB (JPG), imagem de ~300 KB (JPG) e texto de ~400 KB usados nos posts.
- `wordpress-conf/mpm_prefork.conf` – limita os processos do Apache (cabe nos 512 MB de cada instância).

## Cenários

| # | Post | Slug |
|---|---|---|
| 1 | imagem de ~1mb | `cenario-1-imagem-1mb` |
| 2 | texto de ~400kb | `cenario-2-texto-400kb` |
| 3 | imagem de ~300kb | `cenario-3-imagem-300kb` |

## Como executar

Em um terminal bash (Git Bash/WSL), com o Docker em execução:

```bash
./scripts/setup.sh                 # uma vez: instala o WordPress e cria os posts (admin/admin)
./scripts/run_tests.sh             # 3 cenários x 1,2,3 instâncias x 10,100,1000 usuários (60s cada)
docker compose run --rm graficos   # gráficos em results/graficos/
```

Parâmetros opcionais do `run_tests.sh`: `RUN_TIME=30s INSTANCIAS="1 2" USUARIOS="10 100" CENARIOS="1"`.

## Resultados

- `results/c<cenário>_i<instâncias>_u<usuários>_stats.csv` – estatísticas brutas do Locust.
- `results/graficos/cenario<N>_<métrica>_por_usuarios.png` – nº de usuários no eixo X, barras por nº de instâncias.
- `results/graficos/cenario<N>_<métrica>_por_instancias.png` – nº de instâncias no eixo X, barras por nº de usuários.
- Métricas: tempo médio, p95, requisições por segundo e taxa de falhas (24 gráficos no total).
- `results/graficos/resumo.csv` – tabela com tempo médio, p95, RPS, requisições e falhas.

## Decisões para um teste justo

- Mantive as imagens do Trabalho 2 (`mysql:5.7`, `wordpress:5.4.2-php7.2-apache`, `nginx:1.19.0`).
- Cada instância do WordPress tem limite de 1 CPU / 512 MB e Apache com no máximo 10 workers; sem isso, adicionar instâncias não adicionaria capacidade, pois todas dividiriam a mesma máquina.
- O Nginx aceita até 8192 conexões por worker e reutiliza conexões com o upstream (`keepalive`), para que ele não seja o gargalo com 1000 usuários.
- MySQL com `max-connections=1000` e `healthcheck`; os WordPress só sobem quando o banco está saudável.
- Antes de cada execução as instâncias e o Nginx são reiniciados e há uma pausa de 10 s, para que uma rodada não influencie a seguinte.
- Com 1000 usuários, o próprio Locust, o MySQL ou o Docker podem virar gargalo, pois tudo roda na mesma máquina; se isso aparecer nos gráficos, comente na análise.
- O enunciado usa `grubykarol/locust` e a API antiga (`HttpLocust`/`TaskSet`); foi usada a imagem oficial `locustio/locust` com `HttpUser`, com o mesmo comportamento.
