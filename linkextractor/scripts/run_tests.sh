#!/usr/bin/env bash
# Executa a matriz de testes: versão do serviço (python/ruby) x cache (on/off) x usuários.
# Resultados em results/<versão>_cache-<on|off>_u<usuários>_stats.csv
# Uso: ./scripts/run_tests.sh   (variáveis opcionais: RUN_TIME=60s VERSOES="python ruby" CACHES="on off" USUARIOS="10 50 100 500")
set -euo pipefail
export MSYS_NO_PATHCONV=1
cd "$(dirname "$0")/.."

VERSOES=${VERSOES:-"python ruby"}
CACHES=${CACHES:-"on off"}
USUARIOS=${USUARIOS:-"10 50 100 500"}
export RUN_TIME=${RUN_TIME:-60s}
mkdir -p results
chmod 777 results   # o contêiner do Locust escreve aqui com outro usuário

for versao in $VERSOES; do
  export API_HOST="api-$versao"
  for cache in $CACHES; do
    export CACHE=$cache
    for users in $USUARIOS; do
      echo "--- $versao | cache $cache | $users usuários ---"
      # estado limpo a cada execução: Redis vazio e API recriada (com a variável CACHE escolhida)
      docker compose --profile "$versao" up -d --wait --force-recreate redis sites
      docker compose --profile "$versao" up -d --build --wait --force-recreate --no-deps "api-$versao"
      export USERS=$users SPAWN_RATE=$(( users < 50 ? users : 50 ))
      export CSV_PREFIX="${versao}_cache-${cache}_u${users}"
      docker compose --profile test run --rm locust
      sleep "${PAUSA:-5}"
    done
  done
  docker compose --profile "$versao" down
done

echo ">> Concluído. Gere os gráficos com: docker compose run --rm graficos"
