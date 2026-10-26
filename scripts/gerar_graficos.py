"""Lê results/c<cenário>_i<instâncias>_u<usuários>_stats.csv e gera os gráficos de barras.

Por cenário:
  - 4 métricas (tempo médio, p95, requisições/s, % de falhas), cada uma em 2 visões:
  - nº de usuários no eixo X, uma série por nº de instâncias
  - nº de instâncias no eixo X, uma série por nº de usuários
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

NOMES = {"1": "Blog post com imagem de 1mb",
         "2": "Blog post com texto de 400kb",
         "3": "Blog post com imagem de 300kb"}


def carregar(pasta):
    dados = {}  # (cenário, instâncias, usuários) -> métricas da linha "Aggregated"
    for arq in glob.glob(os.path.join(pasta, "c*_i*_u*_stats.csv")):
        c, i, u = re.search(r"c(\d+)_i(\d+)_u(\d+)_stats", arq).groups()
        with open(arq, newline="") as f:
            for linha in csv.DictReader(f):
                if linha["Name"] == "Aggregated":
                    dados[(c, int(i), int(u))] = {
                        "tempo_medio_s": float(linha["Average Response Time"]) / 1000,
                        "p95_s": float(linha["95%"]) / 1000,
                        "rps": float(linha["Requests/s"]),
                        "requisicoes": int(linha["Request Count"]),
                        "falhas": int(linha["Failure Count"]),
                        "falhas_pct": 100 * int(linha["Failure Count"]) / max(1, int(linha["Request Count"])),
                    }
    return dados


def barras(titulo, xlabel, ylabel, eixo_x, series, valor, rotulo_serie, saida):
    """eixo_x: valores no eixo X; series: valores que geram as barras de cada grupo."""
    fig, ax = plt.subplots(figsize=(8, 5))
    largura = 0.8 / len(series)
    for k, s in enumerate(series):
        ys = [valor(x, s) for x in eixo_x]
        pos = [j + k * largura for j in range(len(eixo_x))]
        ax.bar(pos, ys, largura, label=rotulo_serie(s), edgecolor="black")
    ax.set_xticks([j + largura * (len(series) - 1) / 2 for j in range(len(eixo_x))])
    ax.set_xticklabels(eixo_x)
    ax.set_title(titulo)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    fig.tight_layout()
    fig.savefig(saida, dpi=150)
    plt.close(fig)


METRICAS = [  # (chave, arquivo, rótulo do eixo Y)
    ("tempo_medio_s", "tempo_medio", "Tempo de resposta médio (s)"),
    ("p95_s", "tempo_p95", "Tempo de resposta – percentil 95 (s)"),
    ("rps", "requisicoes_por_segundo", "Requisições por segundo"),
    ("falhas_pct", "taxa_de_falhas", "Requisições com falha (%)"),
]


def main(pasta):
    dados = carregar(pasta)
    if not dados:
        sys.exit("Nenhum CSV encontrado em " + pasta)
    saida = os.path.join(pasta, "graficos")
    os.makedirs(saida, exist_ok=True)

    with open(os.path.join(saida, "resumo.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cenario", "instancias", "usuarios", "tempo_medio_s", "p95_s", "rps",
                    "requisicoes", "falhas", "falhas_pct"])
        for (c, i, u), m in sorted(dados.items()):
            w.writerow([c, i, u, round(m["tempo_medio_s"], 3), round(m["p95_s"], 3),
                        round(m["rps"], 2), m["requisicoes"], m["falhas"], round(m["falhas_pct"], 2)])

    for c in sorted({k[0] for k in dados}):
        insts = sorted({k[1] for k in dados if k[0] == c})
        users = sorted({k[2] for k in dados if k[0] == c})
        for chave, arq, rotulo in METRICAS:
            get = lambda i, u: dados.get((c, i, u), {}).get(chave, 0)
            titulo = f"Cenário {c}: {NOMES[c]}"
            barras(titulo, "Número de usuários", rotulo, users, insts,
                   lambda u, i: get(i, u), lambda i: f"{i} instância(s)",
                   os.path.join(saida, f"cenario{c}_{arq}_por_usuarios.png"))
            barras(titulo, "Número de instâncias", rotulo, insts, users,
                   lambda i, u: get(i, u), lambda u: f"{u} usuários",
                   os.path.join(saida, f"cenario{c}_{arq}_por_instancias.png"))
    print("Gráficos em", saida)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results")
