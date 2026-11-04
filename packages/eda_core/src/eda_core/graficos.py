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
    df = pd.read_csv(ruta_csv, dtype=str).fillna("")
    df["durada_mesos_n"] = pd.to_numeric(df["durada_mesos"], errors="coerce")
    df["plazas_n"] = pd.to_numeric(df["plazas"], errors="coerce")
    df["poblacion_n"] = pd.to_numeric(df["poblacio_municipi"], errors="coerce")
    return df


def resumen_outliers_iqr(serie: pd.Series) -> dict:
    """Detecta valores atípicos superiores por rango intercuartílico (Q3 + 1.5·IQR)."""
    s = pd.to_numeric(serie, errors="coerce").dropna()
    if s.empty:
        return {"q1": 0.0, "q3": 0.0, "iqr": 0.0, "limite_superior": 0.0,
                "n_outliers": 0, "pct_outliers": 0.0, "max_outlier": 0.0}
    q1, q3 = float(s.quantile(0.25)), float(s.quantile(0.75))
    iqr = q3 - q1
    limite = q3 + 1.5 * iqr
    atipicos = s[s > limite]
    return {
        "q1": round(q1, 1),
        "q3": round(q3, 1),
        "iqr": round(iqr, 1),
        "limite_superior": round(limite, 1),
        "n_outliers": int(len(atipicos)),
        "pct_outliers": round(len(atipicos) / len(s) * 100, 1),
        "max_outlier": round(float(atipicos.max()), 1) if len(atipicos) else 0.0,
    }


def ranking_per_capita(df: pd.DataFrame, *, min_poblacion: int = 1000, top_n: int = 10) -> pd.DataFrame:
    """Ranking municipal de procesos y plazas IT por cada 1.000 habitantes."""
    d = df.copy()
    d["poblacion_n"] = pd.to_numeric(d["poblacio_municipi"], errors="coerce")
    d["plazas_n"] = pd.to_numeric(d["plazas"], errors="coerce").fillna(0.0)
    d = d[d["poblacion_n"] >= min_poblacion].drop_duplicates(subset="proceso_id")
    if d.empty:
        return pd.DataFrame(columns=["municipi", "urbanitzacio", "poblacion_n",
                                     "procesos", "plazas_totales", "por_1k", "plazas_por_1k"])
    munis = (d.groupby(["municipi", "urbanitzacio", "poblacion_n"], as_index=False)
              .agg(procesos=("proceso_id", "nunique"),
                   plazas_totales=("plazas_n", "sum")))
    munis["por_1k"] = (munis["procesos"] / (munis["poblacion_n"] / 1000)).round(2)
    munis["plazas_por_1k"] = (munis["plazas_totales"] / (munis["poblacion_n"] / 1000)).round(2)
    return munis.nlargest(top_n, "por_1k").reset_index(drop=True)


def generar_estaticos(ruta_csv: Path, directorio: Path | str = "reports/charts") -> list[Path]:
    """Los 6 estáticos estrella (matplotlib/seaborn) → reports/charts/*.png."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    df = _cargar(Path(ruta_csv))
    rutas: list[Path] = []
    d = df.dropna(subset=["durada_mesos_n"])

    # P1 — duración por grupo
    fig, ax = plt.subplots(figsize=(10, 6))
    top_grupos = list(d["grupo"].value_counts().head(5).index)
    sns.boxplot(data=d[d["grupo"].isin(top_grupos)], x="grupo", y="durada_mesos_n",
                hue="grupo", legend=False, palette=PALETA[:len(top_grupos)], ax=ax)
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
    top = ranking_per_capita(df, min_poblacion=1000, top_n=10)
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
    d_urb = df.dropna(subset=["durada_mesos_n"])
    d_urb = d_urb[d_urb["urbanitzacio"].isin(orden)]
    sns.boxplot(data=d_urb, x="urbanitzacio",
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
    evol_df = pd.DataFrame({
        "Fecha": mensual.index,
        "Mensual": mensual.values,
        "Media móvil 12m": mensual.rolling(12, min_periods=1).mean().values,
    })
    fig = px.line(evol_df, x="Fecha", y=["Mensual", "Media móvil 12m"],
                  labels={"value": "Procesos convocados", "variable": "Serie"},
                  title="P3 — Evolución mensual de convocatorias IT con media móvil 12m (interactivo)",
                  color_discrete_sequence=[PALETA[0], PALETA[1]])
    ruta = directorio / "p3_evolucion.html"
    fig.write_html(ruta, include_plotlyjs=True)
    rutas.append(ruta)

    return rutas
