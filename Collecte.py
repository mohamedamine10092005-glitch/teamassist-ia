import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(
    page_title="RH — Consultation",
    page_icon="📊",
    layout="wide",
)

# -----------------------------
# GOOGLE SHEETS
# -----------------------------
def gs_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    return gspread.authorize(creds)

def load_data():
    client = gs_client()
    sh = client.open_by_key(st.secrets["sheet_id"])
    ws = sh.worksheet("data")
    values = ws.get_all_values()

    cols = [
        "timestamp", "organization", "user_role",
        "mood", "workload", "sleep_hours", "focus",
        "conflicts", "comment"
    ]
    if not values or len(values) < 2:
        return pd.DataFrame(columns=cols)

    header = values[0]
    rows = values[1:]
    df = pd.DataFrame(rows, columns=header)

    # Types
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    for c in ["mood", "sleep_hours", "focus"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Colonnes manquantes éventuelles
    for c in cols:
        if c not in df.columns:
            df[c] = None
    df = df[cols]
    return df

# -----------------------------
# UI — HEADER
# -----------------------------
left, right = st.columns([3, 2], vertical_alignment="center")
with left:
    st.title("📊 Consultation RH")
    st.caption("Consulter, filtrer et exporter les données collectées.")
with right:
    st.info("🔎 Utilisez les filtres à gauche pour cibler une équipe, un rôle ou une période.")

st.divider()

# -----------------------------
# LOAD
# -----------------------------
try:
    df = load_data()
except Exception as e:
    st.error("❌ Impossible de charger les données. Vérifiez Secrets + accès Google Sheet.")
    st.code(str(e))
    st.stop()

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
with st.sidebar:
    st.header("🔎 Filtres")
    orgs = sorted([x for x in df["organization"].dropna().unique().tolist() if str(x).strip() != ""])
    roles = sorted([x for x in df["user_role"].dropna().unique().tolist() if str(x).strip() != ""])

    org_filter = st.multiselect("Organisation / Équipe", orgs, default=orgs[:1] if orgs else [])
    role_filter = st.multiselect("Rôle", roles, default=roles if roles else [])

    st.divider()
    st.write("📅 Période")
    if df["timestamp"].notna().any():
        dmin = df["timestamp"].min().date()
        dmax = df["timestamp"].max().date()
        date_range = st.date_input("Du / au", value=(dmin, dmax))
    else:
        date_range = None

    st.divider()
    export_name = st.text_input("Nom du fichier CSV", value="export_rh.csv")

# -----------------------------
# APPLY FILTERS
# -----------------------------
filtered = df.copy()

if org_filter:
    filtered = filtered[filtered["organization"].isin(org_filter)]
if role_filter:
    filtered = filtered[filtered["user_role"].isin(role_filter)]

if date_range and isinstance(date_range, tuple) and len(date_range) == 2 and filtered["timestamp"].notna().any():
    start, end = date_range
    filtered = filtered[
        (filtered["timestamp"].dt.date >= start) &
        (filtered["timestamp"].dt.date <= end)
    ]

# -----------------------------
# KPI ROW
# -----------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Entrées", int(len(filtered)))
c2.metric("Humeur moyenne", f"{filtered['mood'].mean():.2f}" if len(filtered) else "—")
c3.metric("Sommeil moyen", f"{filtered['sleep_hours'].mean():.2f}" if len(filtered) else "—")
c4.metric("Concentration moyenne", f"{filtered['focus'].mean():.2f}" if len(filtered) else "—")

st.divider()

# -----------------------------
# MAIN VIEW
# -----------------------------
left, right = st.columns([2, 1], gap="large")

with left:
    st.subheader("🗂️ Données")
    st.dataframe(
        filtered.sort_values("timestamp", ascending=False),
        use_container_width=True,
        hide_index=True
    )

    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Télécharger CSV",
        data=csv_bytes,
        file_name=export_name,
        mime="text/csv",
        use_container_width=True
    )

with right:
    st.subheader("📌 Synthèse rapide")

    if len(filtered) == 0:
        st.info("Aucune donnée pour les filtres sélectionnés.")
    else:
        with st.container(border=True):
            st.markdown("### Répartition charge")
            st.dataframe(filtered["workload"].value_counts(dropna=False).rename("count"), use_container_width=True)

        with st.container(border=True):
            st.markdown("### Tensions / conflits")
            st.dataframe(filtered["conflicts"].value_counts(dropna=False).rename("count"), use_container_width=True)

        with st.container(border=True):
            st.markdown("### Derniers commentaires")
            last_comments = (
                filtered.sort_values("timestamp", ascending=False)["comment"]
                .fillna("")
                .head(10)
                .tolist()
            )
            for i, c in enumerate(last_comments, start=1):
                st.write(f"{i}. {c}" if str(c).strip() else f"{i}. —")

st.divider()
st.caption("TeamAssist IA — Consultation RH")
