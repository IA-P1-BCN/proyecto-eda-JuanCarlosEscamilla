"""Gráficos del informe y del dashboard (US7·T2/T3).

Cada gráfico lleva en su título la PREGUNTA de negocio que responde
(convención del PRD). Los estáticos alimentan el informe Quarto (US8);
los interactivos (plotly, self-contained) el dashboard en Render (US9).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .viz import PALETA, aplicar_estilo, guardar


def _cargar(ruta_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(ruta_csv, dtype={"proceso_id": str}).fillna("")
    df["durada_mesos_n"] = pd.to_numeric(df["durada_mesos"], errors="coerce")
    df["plazas_n"] = pd.to_numeric(df["plazas"], errors="coerce")
    df["poblacion_n"] = pd.to_numeric(df["poblacio_municipi"], errors="coerce")
    return df


def generar_estaticos(ruta_csv: Path, directorio: Path | str = "reports/charts") -> list[Path]:
    """Los 6 estáticos estrella (matplotlib/seaborn) → reports/charts/*.png."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    df = _cargar(Path(ruta_csv))
    rutas: list[Path] = []
    d = df.dropna(subset=["durada_mesos_n"])

    # P1 — duración por grupo
    fig, ax = plt.subplots(figsize=(10, 6))
    top = d["grupo"].value_counts().head(5).index
    sns.boxplot(data=d[d["grupo"].isin(top)], x="grupo", y="durada_mesos_n",
                hue="grupo", legend=False, palette=PALETA, ax=ax)
    aplicar_estilo(ax, "P1 — ¿Cuánto tarda en resolverse un proceso IT por grupo?",
                   xlabel="Grupo de titulación", ylabel="Meses convocatoria→resolución")
    rutas.append(guardar(fig, "p1_duracion_por_grupo", directorio)); plt.close(fig)

    # P1 — histograma con mediana vs media
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(d["durada_mesos_n"], bins=40, color=PALETA[0], edgecolor="white")
    ax.axvline(d["durada_mesos_n"].median(), color=PALETA[1], linestyle="--",
               label=f"mediana = {d['durada_mesos_n'].median():.1f}")
    ax.axvline(d["durada_mesos_n"].mean(), color="#111827", linestyle=":",
               label=f"media = {d['durada_mesos_n'].mean():.1f}")
    aplicar_estilo(ax, "P1 — Duración: la media la arrastra la cola de atascos",
                   xlabel="Meses", ylabel="Procesos", leyenda=True)
    rutas.append(guardar(fig, "p1_duracion_hist", directorio)); plt.close(fig)

    # P2 — per cápita top municipios
    munis = (df[df["poblacion_n"] >= 1000]
             .drop_duplicates(subset="proceso_id")
             .groupby(["municipi", "urbanitzacio"])["proceso_id"].nunique()
             .rename("procesos").reset_index())
    munis = munis.merge(df.drop_duplicates("municipi")[["municipi", "poblacion_n"]], on="municipi")
    munis["por_1k"] = (munis["procesos"] / (munis["poblacion_n"] / 1000)).round(2)
    top = munis.nlargest(10, "por_1k")
    fig, ax = plt.subplots(figsize=(10, 6))
    colores = [PALETA[2] if u == "rural" else PALETA[3] if u == "intermedi" else PALETA[0]
               for u in top["urbanitzacio"]]
    ax.barh(top["municipi"], top["por_1k"], color=colores)
    ax.invert_yaxis()
    aplicar_estilo(ax, "P2 — ¿Dónde están los puestos IT per cápita? (top 10)",
                   xlabel="Procesos por 1.000 habitantes", ylabel=None)
    rutas.append(guardar(fig, "p2_per_capita_top", directorio)); plt.close(fig)

    # P2 — urbano/intermedio/rural
    fig, ax = plt.subplots(figsize=(10, 6))
    orden = ["rural", "intermedi", "urbano"]
    sns.boxplot(data=df.dropna(subset=["durada_mesos_n"]), x="urbanitzacio",
                y="durada_mesos_n", hue="urbanitzacio", legend=False, order=orden,
                palette=["#16a34a", "#f59e0b", "#2563eb"], ax=ax)
    aplicar_estilo(ax, "P2 — Duración según tamaño del municipio",
                   xlabel="rural <5k · intermedi 5-20k · urbano ≥20k hab",
                   ylabel="Meses hasta resolución")
    rutas.append(guardar(fig, "p2_urbano_rural", directorio)); plt.close(fig)

    # P3 — perfiles demandados
    fig, ax = plt.subplots(figsize=(10, 6))
    df.drop_duplicates(subset="proceso_id")["grupo"].value_counts().head(6).plot(
        kind="barh", ax=ax, color=PALETA[0])
    ax.invert_yaxis()
    aplicar_estilo(ax, "P3 — ¿Qué perfil IT piden los ayuntamientos?",
                   xlabel="Procesos convocados", ylabel="Grupo de titulación")
    rutas.append(guardar(fig, "p3_perfiles", directorio)); plt.close(fig)

    # P3 — estacionalidad
    fig, ax = plt.subplots(figsize=(10, 6))
    meses = df.drop_duplicates(subset="proceso_id")["fecha_convocatoria"].str[5:7]
    orden_meses = meses.value_counts().sort_index()
    ax.bar(range(1, 13), [orden_meses.get(f"{m:02d}", 0) for m in range(1, 13)], color=PALETA[3])
    ax.set_xticks(range(1, 13),
                  ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"])
    aplicar_estilo(ax, "P3 — ¿Cuándo se convoca? (estacionalidad mensual)",
                   xlabel="Mes de la convocatoria", ylabel="Procesos")
    rutas.append(guardar(fig, "p3_estacionalidad", directorio)); plt.close(fig)

    return rutas


def generar_interactivos(ruta_csv: Path, directorio: Path | str = "reports/charts") -> list[Path]:
    """3 plotly self-contained (hover/zoom sin servidor) para el dashboard."""
    import plotly.express as px

    df = _cargar(Path(ruta_csv))
    df = df.drop_duplicates(subset="proceso_id")
    df = df[df["poblacion_n"] > 0]
    rutas: list[Path] = []
    directorio = Path(directorio)
    directorio.mkdir(parents=True, exist_ok=True)

    fig = px.scatter(df, x="poblacion_n", y="places_per_mil_hab", color="urbanitzacio",
                     hover_name="institucio", log_x=True,
                     labels={"poblacion_n": "Población del municipio (log)",
                             "places_per_mil_hab": "Plazas por 1.000 hab"},
                     title="P2 — Plazas IT per cápita por municipio (interactivo)",
                     color_discrete_sequence=PALETA)
    ruta = directorio / "p2_per_capita_scatter.html"
    fig.write_html(ruta, include_plotlyjs=True)
    rutas.append(ruta)

    fig = px.box(df.dropna(subset=["durada_mesos_n"]), x="grupo", y="durada_mesos_n",
                 color="urbanitzacio", hover_name="institucio",
                 labels={"durada_mesos_n": "Meses hasta resolución", "grupo": "Grupo"},
                 title="P1 — Duración por grupo y tamaño de municipio (interactivo)",
                 color_discrete_sequence=PALETA)
    ruta = directorio / "p1_duracion_interactivo.html"
    fig.write_html(ruta, include_plotlyjs=True)
    rutas.append(ruta)

    mensual = (df.assign(fecha=pd.to_datetime(df["fecha_convocatoria"], errors="coerce"))
                 .dropna(subset=["fecha"]).set_index("fecha").resample("ME").size())
    fig = px.line(x=mensual.index, y=mensual.values,
                  labels={"x": "Fecha", "y": "Procesos convocados"},
                  title="P3 — Evolución mensual de convocatorias IT (interactivo)")
    fig.update_traces(line_color=PALETA[0])
    ruta = directorio / "p3_evolucion.html"
    fig.write_html(ruta, include_plotlyjs=True)
    rutas.append(ruta)

    return rutas
