# utils/layout.py
import streamlit as st
from datetime import datetime
from utils.plotting import plot_price_history
from utils.actions import send_test_email_for_route
from utils.data import count_updates_last_24h

# CSS for theme A (light / Google-like)
THEME_CSS = """
<style>
body { background-color: #f7f9fc; }
.card {
  background: white;
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(20,30,50,0.06);
  margin-bottom: 12px;
}
.header-row { display:flex; gap:12px; align-items:center; }
.small-muted { color: #6b7280; font-size:13px; }
.action-btn { margin-right:6px; }
</style>
"""

def render_header(count:int, theme="light"):
    st.markdown(THEME_CSS, unsafe_allow_html=True)
    st.markdown(f"## ✈️ Flight Price Tracker  —  <span style='color:#2563eb'>{count} suivis</span>", unsafe_allow_html=True)
    st.markdown("Suivi des prix — thème clair moderne (A)")

def render_top_actions():
    cols = st.columns([1,1,1])
    with cols[0]:
        if st.button("➕ Ajouter un suivi (onglet)"):
            st.info("Utilise l'onglet Ajouter un suivi.")
    with cols[1]:
        if st.button("🔄 Mettre à jour tous (simu)"):
            st.session_state["bulk_update"] = True
    with cols[2]:
        if st.button("✉️ Envoyer test email global"):
            st.session_state["test_global"] = True

def render_dashboard_table(routes, email_cfg):
    import pandas as pd
    rows = []
    for r in routes:
        last = r.get("history")[-1]["price"] if r.get("history") else None
        minp = min((h["price"] for h in r.get("history",[])), default=None)
        rows.append({
            "id": r.get("id")[:8],
            "route": f"{r.get('origin')} → {r.get('destination')}",
            "departure": r.get("departure"),
            "last_price": last,
            "min_price": minp,
            "target": r.get("target_price"),
            "notif": "ON" if r.get("notifications") else "OFF",
            "email": r.get("email") or email_cfg.get("email","")
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

def render_route_card(r:dict, idx:int, email_cfg:dict):
    """Render one route block. Returns True if any change to route (so caller saves)."""
    changed = False
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        c1, c2 = st.columns([3,1])
        with c1:
            st.markdown(f"**{r.get('origin')} → {r.get('destination')}**  •  {r.get('departure')}")
            st.markdown(f"<span class='small-muted'>Séjour {r.get('stay_min')}–{r.get('stay_max')} j • Retour: {r.get('return') or '—'}</span>", unsafe_allow_html=True)
            last = r.get("history")[-1]["price"] if r.get("history") else None
            st.markdown(f"**Prix actuel :** {last if last else '—'} €  •  **Seuil :** {r.get('target_price')}€")
        with c2:
            if st.button("🔄", key=f"update_{idx}"):
                price = int(100 + (hash(f"{r['id']}{datetime.now()}")%900))
                r.setdefault("history", []).append({"date": datetime.now().isoformat(), "price": price})
                r["last_tracked"] = datetime.now().isoformat()
                changed = True
            if r.get("notifications"):
                if st.button("🔕", key=f"notif_off_{idx}"):
                    r["notifications"] = False
                    changed = True
            else:
                if st.button("🔔", key=f"notif_on_{idx}"):
                    r["notifications"] = True
                    changed = True
            if st.button("🗑", key=f"del_{idx}"):
                # signal delete by set flag (parent should remove)
                r["_delete"] = True
                changed = True

        st.markdown("---")
        # small history & actions
        last_prices = [h["price"] for h in (r.get("history")[-3:] if r.get("history") else [])]
        st.markdown("Derniers prix : " + (" → ".join(str(p) for p in last_prices) if last_prices else "Aucun"))
        if r.get("history"):
            fig = plot_price_history(r["history"])
            st.pyplot(fig, clear_figure=False)

        # test mail button
        rcpt = r.get("email") or email_cfg.get("email","")
        if st.button("Envoyer test mail", key=f"testmail_{idx}"):
            ok, status = send_test_email_for_route(r)
            if ok:
                st.success("Test mail envoyé ✔")
            else:
                st.error(f"Erreur envoi — {status}")

        st.markdown("</div>", unsafe_allow_html=True)
    # handle deletion (parent code will check _delete)
    return changed
