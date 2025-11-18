# exporters_detailed.py
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os
from io import BytesIO
from utils.storage import json_safe

# -----------------------------
# EXPORT XLSX DÉTAILLÉ
# -----------------------------
def export_detailed_xlsx(routes, path="export_detailed.xlsx"):
    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        for r in routes:
            sheet_name = f"{r['origin']}-{r['destination']}"[:31]  # Excel limit 31 chars
            history = r.get("history", [])
            if history:
                df_hist = pd.DataFrame(history)
            else:
                df_hist = pd.DataFrame(columns=["date","price"])
            # Infos générales
            info_dict = {
                "ID": r.get("id"),
                "Origine": r.get("origin"),
                "Destination": r.get("destination"),
                "Classe": r.get("travel_class","Eco"),
                "Départ": r.get("departure"),
                "Retour": r.get("return"),
                "Flex départ ± jours": r.get("departure_flex_days",0),
                "Flex retour ± jours": r.get("return_flex_days",0),
                "Priorité durée séjour": r.get("priority_stay", False),
                "Séjour min": r.get("stay_min",1),
                "Séjour max": r.get("stay_max",1),
                "Prix cible": r.get("target_price",100.0),
                "Trackings/jour": r.get("tracking_per_day",1),
                "Notifications": r.get("notifications", False),
                "Email": r.get("email",""),
                "Min bagages": r.get("min_bags",0),
                "Vol direct": r.get("direct_only", False),
                "Max escales": r.get("max_stops","any"),
                "Compagnies à éviter": ",".join(r.get("avoid_airlines",[])),
                "Compagnies préférées": ",".join(r.get("preferred_airlines",[])),
            }
            df_info = pd.DataFrame(list(info_dict.items()), columns=["Paramètre","Valeur"])
            df_info.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0)
            df_hist.to_excel(writer, sheet_name=sheet_name, index=False, startrow=len(df_info)+2)
    return path

# -----------------------------
# EXPORT PDF DÉTAILLÉ
# -----------------------------
def export_detailed_pdf(routes, path="export_detailed.pdf"):
    pp = PdfPages(path)
    for r in routes:
        plt.figure(figsize=(8,6))
        plt.title(f"{r['origin']} → {r['destination']} ({r.get('travel_class','Eco')})")
        # Infos générales
        info_text = "\n".join([f"{k}: {json_safe(v)}" for k,v in {
            "ID": r.get("id"),
            "Classe": r.get("travel_class","Eco"),
            "Départ": r.get("departure"),
            "Retour": r.get("return"),
            "Flex départ ± jours": r.get("departure_flex_days",0),
            "Flex retour ± jours": r.get("return_flex_days",0),
            "Priorité durée séjour": r.get("priority_stay", False),
            "Séjour min/max": f"{r.get('stay_min',1)}/{r.get('stay_max',1)}",
            "Prix cible": r.get("target_price",100.0),
            "Trackings/jour": r.get("tracking_per_day",1),
            "Notifications": r.get("notifications", False),
            "Email": r.get("email",""),
            "Min bagages": r.get("min_bags",0),
            "Vol direct": r.get("direct_only", False),
            "Max escales": r.get("max_stops","any"),
            "Compagnies à éviter": ",".join(r.get("avoid_airlines",[])),
            "Compagnies préférées": ",".join(r.get("preferred_airlines",[])),
        }.items()])
        plt.text(0,1, info_text, fontsize=10, va='top', ha='left', wrap=True)
        
        # Graphique des prix
        history = r.get("history", [])
        if history:
            dates = [d['date'] for d in history]
            prices = [d['price'] for d in history]
            fig2, ax = plt.subplots(figsize=(8,3))
            ax.plot(dates, prices, marker='o')
            ax.set_title("Historique des prix")
            ax.set_xlabel("Date")
            ax.set_ylabel("Prix (€)")
            plt.xticks(rotation=45)
            plt.tight_layout()
            pp.savefig(fig2)
            plt.close(fig2)
        pp.savefig()
        plt.close()
    pp.close()
    return path
