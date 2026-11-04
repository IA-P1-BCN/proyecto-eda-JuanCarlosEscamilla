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
    df = pd.read_csv(ruta_csv, dtype={"proceso_id": str}).fillna("")
    df["durada_mesos"] = pd.to_numeric(df["durada_mesos"], errors="coerce")
    df["plazas_n"] = pd.to_numeric(df["plazas"], errors="coerce")
    df["poblacion_n"] = pd.to_numeric(df["poblacio_municipi"], errors="coerce")
    df["fecha"] = pd.to_datetime(df["fecha_convocatoria"], errors="coerce")
    return df


def calcular_kpis(df: pd.DataFrame, *, municipio: str, grupo: str, estado: str) -> pd.DataFrame:
    if municipio != "Todos":
        df = df[df["institucio"] == municipio]
    if grupo != "Todos":
        df = df[df["grupo"] == grupo]
    if estado != "Todos":
        df = df[df["estado"] == estado]
    return df


def main() -> None:
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

    filtrado = calcular_kpis(df, municipio=municipio, grupo=grupo, estado=estado)

    # ── KPIs ──
    procesos = filtrado["proceso_id"].nunique()
    resueltas = filtrado.dropna(subset=["durada_mesos"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Procesos", f"{procesos:,}")
    c2.metric("Hitos documentados", f"{len(filtrado):,}")
    c3.metric("Plazas convocadas", f"{filtrado['plazas_n'].sum():.0f}")
    c4.metric("Duración mediana (resueltas)",
              f"{resueltas['durada_mesos'].median():.1f} meses" if len(resueltas) else "—")

    # ── Tabla del proceso ──
    st.subheader("Procesos")
    st.dataframe(
        filtrado.drop_duplicates(subset="proceso_id")[
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
