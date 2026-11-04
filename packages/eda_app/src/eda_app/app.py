"""Dashboard Streamlit del proyecto (US9) — el CEO filtra y explora solo.

Ejecutar: task dashboard  (streamlit run packages/eda_app/src/eda_app/app.py)
Lee el dataset ENRIQUECIDO del pipeline (sin recomputar el EDA); la lógica
de negocio vive en eda_core — aquí solo carga, filtros y visualización.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

RUTA_DATOS = Path("data/processed/oposicions_enriquit.csv")
RUTA_FALLBACK = Path("../") / RUTA_DATOS  # si se lanza desde otro directorio


@st.cache_data
def cargar_datos(ruta_csv: str | Path) -> pd.DataFrame:
    df = pd.read_csv(ruta_csv, dtype=str).fillna("")
    df["durada_mesos"] = pd.to_numeric(df["durada_mesos"], errors="coerce")
    df["plazas_n"] = pd.to_numeric(df["plazas"], errors="coerce")
    df["poblacion_n"] = pd.to_numeric(df["poblacio_municipi"], errors="coerce")
    df["places_per_mil_hab_n"] = pd.to_numeric(df["places_per_mil_hab"], errors="coerce")
    df["fecha"] = pd.to_datetime(df["fecha_convocatoria"], errors="coerce")
    return df


def calcular_kpis(
    df: pd.DataFrame, *, municipio: str, grupo: str, estado: str,
    rango_anios: tuple[int, int] | None = None,
) -> pd.DataFrame:
    if municipio != "Todos":
        df = df[df["institucio"] == municipio]
    if grupo != "Todos":
        df = df[df["grupo"] == grupo]
    if estado != "Todos":
        df = df[df["estado"] == estado]
    if rango_anios is not None:
        anios = df["fecha"].dt.year
        df = df[anios.isna() | ((anios >= rango_anios[0]) & (anios <= rango_anios[1]))]
        if rango_anios[0] > int(df["fecha"].dt.year.min() or 0):
            df = df[df["fecha"].dt.year.between(rango_anios[0], rango_anios[1])]
    return df


def main() -> None:
    import plotly.express as px

    st.set_page_config(page_title="Oposiciones IT — CIDO", page_icon="🎓", layout="wide")
    st.title("🎓 Procesos selectivos IT en la administración local")
    st.caption("Área de Vic (45 km) · materia Informàtica · fuente CIDO DIBA · "
               "datos enriquecidos y limpios vía pipeline TDD")

    if not (RUTA_DATOS.exists() or RUTA_FALLBACK.exists()):
        st.error("No existe el dataset enriquecido. Ejecuta antes: `task download` → "
                 "`uv run eda-pipeline --step clean` → `--step enrich`")
        return
    ruta = RUTA_DATOS if RUTA_DATOS.exists() else RUTA_FALLBACK
    df = cargar_datos(ruta)

    st.sidebar.header("Filtros")
    municipios = ["Todos"] + sorted(df["institucio"].unique())
    municipio = st.sidebar.selectbox("Institución convocante", municipios)
    grupo = st.sidebar.selectbox("Grupo de titulación",
                                 ["Todos"] + sorted(g for g in df["grupo"].unique() if g))
    estado = st.sidebar.selectbox("Estado", ["Todos"] + sorted(e for e in df["estado"].unique() if e))
    anios_validos = df["fecha"].dt.year.dropna().astype(int)
    rango_anios = None
    if not anios_validos.empty:
        min_a, max_a = int(anios_validos.min()), int(anios_validos.max())
        rango_anios = st.sidebar.slider("Año de convocatoria", min_a, max_a, (min_a, max_a))

    filtrado = calcular_kpis(df, municipio=municipio, grupo=grupo, estado=estado,
                             rango_anios=rango_anios)
    unicos = filtrado.drop_duplicates(subset="proceso_id")

    # ── KPIs ──
    procesos = len(unicos)
    resueltas = unicos.dropna(subset=["durada_mesos"])
    con_pob = unicos.dropna(subset=["places_per_mil_hab_n"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Procesos", f"{procesos:,}")
    c2.metric("Hitos documentados", f"{len(filtrado):,}")
    c3.metric("Plazas convocadas", f"{unicos['plazas_n'].sum():.0f}")
    c4.metric("Duración mediana (resueltas)",
              f"{resueltas['durada_mesos'].median():.1f} meses" if len(resueltas) else "—")

    # ── Visualizaciones interactivas (P1, P2, P3) ──
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        if not resueltas.empty:
            fig_p1 = px.box(
                resueltas, x="grupo", y="durada_mesos", color="urbanitzacio",
                hover_name="institucio",
                labels={"durada_mesos": "Meses hasta resolución", "grupo": "Grupo"},
                title="P1 — Duración por grupo de titulación y tamaño municipal",
            )
            st.plotly_chart(fig_p1, use_container_width=True)
    with col_g2:
        if not con_pob.empty:
            fig_p2 = px.scatter(
                con_pob[con_pob["poblacion_n"] > 0], x="poblacion_n", y="places_per_mil_hab_n",
                color="urbanitzacio", hover_name="institucio", log_x=True,
                labels={"poblacion_n": "Población municipal (log)",
                        "places_per_mil_hab_n": "Plazas por 1.000 hab"},
                title="P2 — Plazas IT per cápita por municipio",
            )
            st.plotly_chart(fig_p2, use_container_width=True)

    con_fecha = unicos.dropna(subset=["fecha"]).set_index("fecha")
    if not con_fecha.empty:
        mensual = con_fecha.resample("ME").size()
        evol_df = pd.DataFrame({
            "Fecha": mensual.index,
            "Convocatorias": mensual.values,
            "Media móvil 12m": mensual.rolling(12, min_periods=1).mean().values,
        })
        fig_p3 = px.line(
            evol_df, x="Fecha", y=["Convocatorias", "Media móvil 12m"],
            labels={"value": "Procesos convocados", "variable": "Serie"},
            title="P3 — Calendario mensual de convocatorias IT (con media móvil 12m)",
        )
        st.plotly_chart(fig_p3, use_container_width=True)

    # ── Tabla del proceso ──
    st.subheader("Procesos")
    st.dataframe(
        unicos[
            ["proceso_id", "fecha_convocatoria", "institucio", "sistema",
             "grupo", "plazas", "estado", "municipi", "urbanitzacio",
             "places_per_mil_hab", "durada_mesos"]
        ].sort_values("fecha_convocatoria", ascending=False),
        use_container_width=True, hide_index=True,
    )

    st.caption("Dataset: release silver + actualizaciones diarias del pipeline · "
               "código y decisiones: ver PRD y ADRs en el repositorio")


if __name__ == "__main__":
    main()
