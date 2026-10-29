"""Lê results/<versão>_cache-<on|off>_u<usuários>_stats.csv e gera os gráficos de barras.

Para cada métrica (tempo médio, mediana, p95, requisições/s, % de falhas): nº de usuários no eixo X,
uma barra por combinação versão x cache. Também gera results/graficos/resumo.csv.
Uso: python gerar_graficos.py <diretório de resultados>
"""
import csv
import glob
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

METRICAS = [  # (chave, arquivo, rótulo do eixo Y)
    ("tempo_medio_s", "tempo_medio", "Tempo de resposta médio (s)"),
    ("mediana_s", "tempo_mediana", "Tempo de resposta – mediana (s)"),
    ("p95_s", "tempo_p95", "Tempo de resposta – percentil 95 (s)"),
    ("rps", "requisicoes_por_segundo", "Requisições por segundo"),
    ("falhas_pct", "taxa_de_falhas", "Requisições com falha (%)"),
]


def carregar(pasta):
    dados = {}  # (versão, cache, usuários) -> métricas da linha "Aggregated"
    for arq in glob.glob(os.path.join(pasta, "*_cache-*_u*_stats.csv")):
        v, c, u = re.search(r"(\w+?)_cache-(\w+)_u(\d+)_stats", os.path.basename(arq)).groups()
        with open(arq, newline="") as f:
            for linha in csv.DictReader(f):
                if linha["Name"] == "Aggregated":
                    n = int(linha["Request Count"])
                    dados[(v, c, int(u))] = {
                        "tempo_medio_s": float(linha["Average Response Time"]) / 1000,
                        "mediana_s": float(linha["Median Response Time"]) / 1000,
                        "p95_s": float(linha["95%"]) / 1000,
                        "rps": float(linha["Requests/s"]),
                        "requisicoes": n,
                        "falhas": int(linha["Failure Count"]),
                        "falhas_pct": 100 * int(linha["Failure Count"]) / max(1, n),
                    }
    return dados


def barras(titulo, ylabel, users, combos, valor, saida):
    fig, ax = plt.subplots(figsize=(9, 5))
    largura = 0.8 / len(combos)
    for k, (v, c) in enumerate(combos):
        ys = [valor(v, c, u) for u in users]
        pos = [j + k * largura for j in range(len(users))]
        ax.bar(pos, ys, largura, label=f"{v.capitalize()} {'com' if c == 'on' else 'sem'} cache", edgecolor="black")
    ax.set_xticks([j + largura * (len(combos) - 1) / 2 for j in range(len(users))])
    ax.set_xticklabels(users)
    ax.set_title(titulo)
    ax.set_xlabel("Número de usuários")
    ax.set_ylabel(ylabel)
    ax.legend()
    fig.tight_layout()
    fig.savefig(saida, dpi=150)
    plt.close(fig)


def main(pasta):
    dados = carregar(pasta)
    if not dados:
        sys.exit("Nenhum CSV encontrado em " + pasta)
    saida = os.path.join(pasta, "graficos")
    os.makedirs(saida, exist_ok=True)

    with open(os.path.join(saida, "resumo.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["versao", "cache", "usuarios", "tempo_medio_s", "mediana_s", "p95_s", "rps",
                    "requisicoes", "falhas", "falhas_pct"])
        for (v, c, u), m in sorted(dados.items()):
            w.writerow([v, c, u, round(m["tempo_medio_s"], 3), round(m["mediana_s"], 3), round(m["p95_s"], 3),
                        round(m["rps"], 2), m["requisicoes"], m["falhas"], round(m["falhas_pct"], 2)])

    users = sorted({k[2] for k in dados})
    combos = sorted({(k[0], k[1]) for k in dados}, key=lambda t: (t[0], t[1] != "on"))
    for chave, arq, rotulo in METRICAS:
        barras("Link Extractor: " + rotulo.split(" (")[0], rotulo, users, combos,
               lambda v, c, u: dados.get((v, c, u), {}).get(chave, 0),
               os.path.join(saida, f"{arq}_por_usuarios.png"))
    print("Gráficos em", saida)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results")
