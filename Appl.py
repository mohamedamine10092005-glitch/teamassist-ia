import streamlit as st
from datetime import datetime
import pandas as pd

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(
    page_title="TeamAssist IA — Management augmenté",
    page_icon="🤖",
    layout="wide",
)

# -----------------------------
# STATE (historique en mémoire)
# -----------------------------
if "history" not in st.session_state:
    st.session_state.history = []  # liste de dict

# -----------------------------
# HELPERS
# -----------------------------
def compute_scores(mood: int, workload: str, sleep: int, focus: int, conflicts: str, comment: str):
    """
    Scores simples (démonstrateur) : stress / motivation / risque.
    Objectif : montrer une logique IA + transparence (explicabilité).
    """
    workload_map = {"Faible": 1, "Moyenne": 3, "Élevée": 5}
    conflict_map = {"Non": 1, "Oui (léger)": 3, "Oui (important)": 5}

    w = workload_map[workload]
    c = conflict_map[conflicts]

    # Stress (0-100)
    stress = (w * 12) + ((6 - mood) * 10) + ((8 - sleep) * 6) + (c * 6) + ((6 - focus) * 8)
    stress = max(0, min(100, stress))

    # Motivation (0-100)
    motivation = (mood * 14) + (focus * 10) + (sleep * 6) - (w * 8) - (c * 6)
    motivation = max(0, min(100, motivation))

    # Risque global (0-100)
    risk = round((stress * 0.6) + ((100 - motivation) * 0.4))
    risk = max(0, min(100, risk))

    # Mini “NLP” très simple (démonstrateur) : détection de mots-clés
    text = (comment or "").lower()
    red_flags = ["burnout", "épuis", "angoiss", "panic", "déprim", "harcel", "insom", "mal", "pression", "overload"]
    keyword_hit = any(k in text for k in red_flags)

    if keyword_hit:
        risk = min(100, risk + 10)

    return int(stress), int(motivation), int(risk), keyword_hit


def generate_recommendations(stress: int, motivation: int, risk: int, keyword_hit: bool):
    """
    Recommandations structurées (IA conseillère), avec actions manager + actions collaborateur.
    """
    level = "Faible"
    if risk >= 70:
        level = "Élevé"
    elif risk >= 40:
        level = "Modéré"

    # Conseils de base
    manager_actions = []
    team_actions = []
    human_note = "⚖️ Décision finale laissée au manager humain (IA = aide à la décision)."

    if level == "Élevé":
        manager_actions += [
            "Planifier un échange 1:1 sous 48h (écoute active, sans jugement).",
            "Réduire temporairement la charge / re-prioriser les tâches.",
            "Clarifier les attentes, délais, et points de blocage.",
            "Proposer un soutien (mentorat, binômage, pause planifiée).",
        ]
        team_actions += [
            "Définir 1–2 priorités maximum pour la prochaine période.",
            "Bloquer une pause et une plage sans interruptions.",
            "Demander de l’aide sur une tâche précise (pair-programming / relecture / support).",
        ]
        if keyword_hit:
            manager_actions.append("⚠️ Mots-clés sensibles détectés : renforcer l’attention humaine, proposer un accompagnement adapté.")
    elif level == "Modéré":
        manager_actions += [
            "Faire un check-in rapide (10 min) cette semaine.",
            "Ajuster l’organisation : répartition, planning, micro-deadlines.",
            "Encourager la communication sur les obstacles.",
        ]
        team_actions += [
            "Lister les blocages et proposer une solution / besoin.",
            "Mettre en place une routine courte de suivi (5 min/jour).",
        ]
    else:
        manager_actions += [
            "Maintenir le cadre actuel et valoriser les efforts.",
            "Préserver un bon équilibre : charge stable, feedback régulier.",
        ]
        team_actions += [
            "Continuer les bonnes pratiques (organisation, pauses, communication)."
        ]

    # Message synthèse
    summary = f"Niveau de risque : **{level}** (score {risk}/100)."

    return summary, manager_actions, team_actions, human_note


def comment_suggestions():
    """
    Suggestions de commentaires prêtes à cliquer
    (pour rendre la saisie rapide et plus “guidée”).
    """
    return {
        "Charge & délais": [
            "Je me sens sous pression à cause des délais cette semaine.",
            "J’ai trop de tâches en parallèle, je n’arrive pas à prioriser.",
            "Je suis bloqué(e) sur une partie et j’ai besoin d’aide.",
        ],
        "Énergie & sommeil": [
            "Je dors mal en ce moment, je manque d’énergie.",
            "Je suis fatigué(e) et j’ai du mal à rester concentré(e).",
            "J’ai besoin d’un rythme plus stable pour être efficace.",
        ],
        "Motivation": [
            "Je me sens moins motivé(e) depuis quelques jours.",
            "Je suis motivé(e) mais j’ai besoin d’objectifs plus clairs.",
            "Je me sens bien, j’avance correctement sur mes priorités.",
        ],
        "Relationnel & communication": [
            "Il y a des tensions légères dans l’équipe, ça me pèse un peu.",
            "Je préfère clarifier la communication sur qui fait quoi.",
            "Je me sens bien soutenu(e) par l’équipe en ce moment.",
        ],
    }

# -----------------------------
# UI — HEADER
# -----------------------------
left, right = st.columns([3, 2], vertical_alignment="center")
with left:
    st.title("🤖 TeamAssist IA")
    st.caption("Assistant de bien-être & aide à la décision — **Management augmenté par l’IA**")
with right:
    st.info("✅ Prototype démonstrateur : IA conseille, l’humain décide.\n\n📌 Données minimales, approche éthique.")

st.divider()

# -----------------------------
# SIDEBAR (paramètres)
# -----------------------------
with st.sidebar:
    st.header("⚙️ Paramètres")
    st.write("Personnalise l’évaluation et la démo.")
    org = st.text_input("Organisation / Équipe", value="Équipe projet")
    role = st.selectbox("Rôle de l’utilisateur", ["Collaborateur", "Manager", "RH"])
    anonym = st.checkbox("Mode anonymisé (recommandé)", value=True)
    st.caption("RGPD : minimisation, consentement, transparence.")

# -----------------------------
# MAIN LAYOUT
# -----------------------------
col_form, col_dash = st.columns([2, 3], gap="large")

# -----------------------------
# FORM — saisie collaborateur
# -----------------------------
with col_form:
    st.subheader("📝 Check-in du jour (Collaborateur)")

    with st.container(border=True):
        st.markdown("### Indicateurs")
        mood = st.slider("Humeur (1 = très mauvaise, 5 = excellente)", 1, 5, 3)
        workload = st.radio("Charge de travail", ["Faible", "Moyenne", "Élevée"], horizontal=True)
        sleep = st.slider("Sommeil (heures / nuit)", 0, 10, 7)
        focus = st.slider("Concentration (1 = faible, 5 = excellente)", 1, 5, 3)
        conflicts = st.selectbox("Tensions / conflits ressentis", ["Non", "Oui (léger)", "Oui (important)"])

    st.markdown("### 💬 Commentaire (optionnel)")

    sugg = comment_suggestions()
    cat = st.selectbox("Suggestions de commentaires", list(sugg.keys()))
    pick = st.selectbox("Choisir une phrase (facultatif)", ["—"] + sugg[cat])

    comment_default = "" if pick == "—" else pick
    comment = st.text_area("Exprime ton ressenti (tu peux modifier la phrase)", value=comment_default, height=130)

    st.markdown("### ✅ Consentement")
    consent = st.checkbox("Je consens à l’utilisation de ces données pour un suivi interne (prototype pédagogique).", value=True)

    submitted = st.button("🔎 Analyser avec l’IA", use_container_width=True, type="primary")

# -----------------------------
# DASHBOARD — résultats
# -----------------------------
with col_dash:
    st.subheader("📊 Tableau de bord (Manager / RH)")

    if submitted:
        if not consent:
            st.error("Le consentement est requis pour lancer l’analyse (démonstration RGPD).")
        else:
            stress, motivation, risk, keyword_hit = compute_scores(mood, workload, sleep, focus, conflicts, comment)
            summary, manager_actions, team_actions, human_note = generate_recommendations(stress, motivation, risk, keyword_hit)

            # Enregistrer dans l'historique (en mémoire)
            st.session_state.history.append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "org": org,
                "role": role,
                "mood": mood,
                "workload": workload,
                "sleep": sleep,
                "focus": focus,
                "conflicts": conflicts,
                "stress": stress,
                "motivation": motivation,
                "risk": risk,
                "flag_keywords": keyword_hit,
                "comment": "" if anonym else (comment or ""),
            })

            # KPIs
            k1, k2, k3 = st.columns(3)
            k1.metric("Stress", f"{stress}/100")
            k2.metric("Motivation", f"{motivation}/100")
            k3.metric("Risque global", f"{risk}/100")

            with st.container(border=True):
                st.markdown("### 🧠 Synthèse IA")
                st.markdown(summary)
                if keyword_hit:
                    st.warning("Mots-clés sensibles détectés dans le commentaire (démonstrateur). Prioriser un échange humain.")

                st.markdown("### ✅ Plan d’action — Manager")
                for a in manager_actions:
                    st.write("•", a)

                st.markdown("### 🤝 Conseils — Collaborateur")
                for a in team_actions:
                    st.write("•", a)

                st.caption(human_note)

            with st.expander("🔎 Explicabilité (comment l’IA a conclu ?)"):
                st.write(
                    "- Le score de risque est calculé à partir de : charge, humeur, sommeil, concentration et tensions.\n"
                    "- Les mots-clés sensibles augmentent légèrement le risque pour renforcer la vigilance humaine.\n"
                    "- Ce modèle est un **démonstrateur pédagogique** : transparent et améliorable."
                )

    # Historique
    st.markdown("### 🗂️ Historique des check-ins (session)")
    if len(st.session_state.history) == 0:
        st.caption("Aucun check-in pour le moment. Lance une analyse à gauche.")
    else:
        df = pd.DataFrame(st.session_state.history)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.download_button(
            "⬇️ Télécharger l’historique (CSV)",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="teamassist_history.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Encadré éthique (toujours visible)
    st.divider()
    with st.container(border=True):
        st.markdown("### 🛡️ Éthique & RGPD (à montrer au prof)")
        st.write("• Minimisation des données (pas de données sensibles obligatoires).")
        st.write("• Consentement explicite avant analyse.")
        st.write("• Anonymisation optionnelle.")
        st.write("• L’IA **ne décide pas**, elle **propose** : responsabilité humaine maintenue.")
