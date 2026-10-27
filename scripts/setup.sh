#!/usr/bin/env bash
# Sobe o ambiente, instala o WordPress e cria os 3 posts dos cenários de teste.
# Execute na raiz do projeto: ./scripts/setup.sh
set -euo pipefail
export MSYS_NO_PATHCONV=1   # Git Bash no Windows não deve converter caminhos como /conteudo
cd "$(dirname "$0")/.."


echo ">> Subindo db, wordpress1 e nginx"
docker compose up -d --no-deps db wordpress1
docker compose up -d --no-deps nginx wordpress2 wordpress3

wp() { docker compose run --rm -T wpcli wp "$@"; }

echo ">> Aguardando o banco e o wp-config.php"
until wp db check >/dev/null 2>&1; do sleep 5; done

if ! wp core is-installed >/dev/null 2>&1; then
  echo ">> Instalando o WordPress"
  wp core install --url=http://nginx --title="Sistemas Distribuidos" \
    --admin_user=admin --admin_password=admin --admin_email=admin@example.com --skip-email
fi

criar_post() {  # criar_post <slug> <título> <arquivo de conteúdo>
  if [ -n "$(wp post list --name="$1" --post_status=publish --format=ids)" ]; then
    echo "   $1 já existe"; return
  fi
  wp post create "$3" --post_title="$2" --post_name="$1" --post_status=publish --porcelain
}

criar_post_imagem() {  # criar_post_imagem <slug> <título> <imagem em /media>
  if [ -n "$(wp post list --name="$1" --post_status=publish --format=ids)" ]; then
    echo "   $1 já existe"; return
  fi
  local id url
  id=$(wp media import "$3" --porcelain)
  url=$(wp post get "$id" --field=guid)
  wp post create --post_content="<img src=\"$url\" alt=\"$2\" />" --post_title="$2" --post_name="$1" --post_status=publish --porcelain
}

echo ">> Permalinks amigáveis (/<slug>/), sem redirecionamento"
wp rewrite structure "/%postname%/" --hard

echo ">> Ativando o tema SD Moderno"
docker compose run --rm -T wpcli sh -c "rm -rf wp-content/themes/sd-moderno && cp -r /tema wp-content/themes/sd-moderno"
wp theme activate sd-moderno

echo ">> Criando posts"
criar_post_imagem cenario-1-imagem-1mb "Cenario 1 - imagem 1mb" /conteudo/datacenter_aereo_1mb.jpg
criar_post        cenario-2-texto-400kb "Cenario 2 - texto 400kb" /conteudo/texto_400kb.html
criar_post_imagem cenario-3-imagem-300kb "Cenario 3 - imagem 300kb" /conteudo/mapa_datacenters_300kb.jpg

echo ">> Pronto. Teste: curl -s 'http://localhost/cenario-2-texto-400kb/' | wc -c"
