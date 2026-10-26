#!/usr/bin/env bash
# Executa a matriz de testes: cenários x instâncias do WordPress x usuários.
# Resultados em results/c<cenário>_i<instâncias>_u<usuários>_stats.csv
# Uso: ./scripts/run_tests.sh   (variáveis opcionais: RUN_TIME=60s INSTANCIAS="1 2 3" USUARIOS="10 100 1000" CENARIOS="1 2 3")
set -euo pipefail
export MSYS_NO_PATHCONV=1   # Git Bash no Windows não deve converter caminhos como /conteudo
cd "$(dirname "$0")/.."

INSTANCIAS=${INSTANCIAS:-"1 2 3"}
USUARIOS=${USUARIOS:-"10 100 1000"}
CENARIOS=${CENARIOS:-"1 2 3"}
export RUN_TIME=${RUN_TIME:-60s}
mkdir -p results
chmod 777 results   # o contêiner do Locust escreve aqui com outro usuário

for inst in $INSTANCIAS; do
  echo "=== $inst instância(s) do WordPress ==="
  export NGINX_CONF="nginx-$inst.conf"; [ "$inst" = 3 ] && NGINX_CONF=nginx.conf   # 3 instâncias = nginx.conf (Trabalho 2)
  servicos=""; para_parar=""
  for i in 1 2 3; do
    if [ "$i" -le "$inst" ]; then servicos="$servicos wordpress$i"; else para_parar="$para_parar wordpress$i"; fi
  done
  docker compose up -d --no-deps db $servicos
  [ -n "$para_parar" ] && docker compose stop $para_parar
  # recria o nginx para ler o upstream da configuração escolhida
  docker compose up -d --no-deps --force-recreate nginx

  # aquecimento: espera o site responder e inicializa o opcache de cada instância
  until docker compose exec -T nginx curl -fs -o /dev/null "http://localhost/cenario-2-texto-400kb/"; do sleep 3; done
  for _ in $(seq $((inst * 3))); do
    docker compose exec -T nginx curl -s -o /dev/null "http://localhost/cenario-2-texto-400kb/"
  done

  for cenario in $CENARIOS; do
    for users in $USUARIOS; do
      export SCENARIO=$cenario USERS=$users
      export SPAWN_RATE=$(( users < 50 ? users : 50 ))
      export CSV_PREFIX="c${cenario}_i${inst}_u${users}"
      docker compose restart $servicos nginx >/dev/null 2>&1   # estado limpo a cada execução
      until docker compose exec -T nginx curl -fs -o /dev/null "http://localhost/cenario-2-texto-400kb/"; do sleep 3; done
      echo "--- cenário $cenario | $inst instância(s) | $users usuários ---"
      docker compose run --rm locust
      sleep ${PAUSA:-10}   # descanso entre execuções
    done
  done
done

echo ">> Concluído. Gere os gráficos com: docker compose run --rm graficos"
