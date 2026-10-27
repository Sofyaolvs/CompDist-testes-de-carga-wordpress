#!/usr/bin/env bash
# Publica os gráficos e a tabela-resumo na página /resultados/ do WordPress.
# Rode depois de ./scripts/run_tests.sh e de "docker compose run --rm graficos".
set -euo pipefail
export MSYS_NO_PATHCONV=1   # Git Bash no Windows não deve converter caminhos como /var/www/html
cd "$(dirname "$0")/.."

GRAFICOS=results/graficos
DESTINO=wordpress/wp-content/uploads/resultados
[ -f "$GRAFICOS/resumo.csv" ] || { echo "Sem $GRAFICOS/resumo.csv: gere os gráficos antes."; exit 1; }

mkdir -p "$DESTINO"
rm -f "$DESTINO"/*.png
cp "$GRAFICOS"/*.png "$DESTINO"/
URL=/wp-content/uploads/resultados

NOMES=("" "Blog post com imagem de 1mb" "Blog post com texto de 400kb" "Blog post com imagem de 300kb")
METRICAS=("tempo_medio:Tempo de resposta médio" "tempo_p95:Tempo de resposta (percentil 95)" "requisicoes_por_segundo:Requisições por segundo" "taxa_de_falhas:Taxa de falhas")

html="$DESTINO/pagina.html"
{
  echo '<p class="intro">Resultados dos testes de carga com o Locust: 3 cenários, com 1, 2 e 3 instâncias do WordPress e 10, 100 e 1000 usuários simultâneos (60 s por execução).</p>'
  echo '<nav class="subnav"><a href="#cenario-1">Cenário 1</a><a href="#cenario-2">Cenário 2</a><a href="#cenario-3">Cenário 3</a></nav>'
  for c in 1 2 3; do
    echo "<section class=\"res\" id=\"cenario-$c\">"
    echo "<h2>Cenário $c: ${NOMES[$c]}</h2>"
    echo '<div class="tabela"><table><thead><tr><th>Instâncias</th><th>Usuários</th><th>Tempo médio (s)</th><th>p95 (s)</th><th>Req/s</th><th>Requisições</th><th>Falhas</th></tr></thead><tbody>'
    awk -F, -v c="$c" 'NR>1 && $1==c {
      cls = ($8>0) ? " class=\"falha\"" : "";
      printf "<tr%s><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s (%s%%)</td></tr>\n", cls,$2,$3,$4,$5,$6,$7,$8,$9 }' "$GRAFICOS/resumo.csv"
    echo '</tbody></table></div>'
    for visao in usuarios instancias; do
      if [ "$visao" = usuarios ]; then echo '<h3>Por número de usuários</h3>'; else echo '<h3>Por número de instâncias</h3>'; fi
      echo '<div class="graficos">'
      for m in "${METRICAS[@]}"; do
        arq=${m%%:*}; nome=${m#*:}
        echo "<figure><img loading=\"lazy\" src=\"$URL/cenario${c}_${arq}_por_${visao}.png\" alt=\"$nome, cenário $c, por $visao\" /></figure>"
      done
      echo '</div>'
    done
    echo '</section>'
  done
} > "$html"

wp() { docker compose run --rm -T wpcli wp "$@"; }
conteudo=/var/www/html/wp-content/uploads/resultados/pagina.html
id=$(wp post list --post_type=page --name=resultados --post_status=any --format=ids)
if [ -n "$id" ]; then
  wp post update "$id" "$conteudo" --post_status=publish
else
  wp post create "$conteudo" --post_type=page --post_title="Resultados" --post_name=resultados --post_status=publish
fi
echo ">> Pronto: http://localhost/resultados/"
