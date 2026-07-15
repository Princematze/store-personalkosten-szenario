
import math
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Store-Personalkosten – Szenario", page_icon="📊", layout="wide")

def eur_m(v):
    return f"{v/1_000_000:,.1f} Mio. €".replace(",", "X").replace(".", ",").replace("X", ".")

def pct(v):
    return f"{v:.1%}".replace(".", ",")

def delta_eur(v):
    s = "+" if v > 0 else ""
    return (s + f"{v/1_000_000:,.1f} Mio. €").replace(",", "X").replace(".", ",").replace("X", ".")

def delta_pp(v):
    s = "+" if v > 0 else ""
    return (s + f"{v*100:.1f} %-Pkt.").replace(".", ",")

st.title("Store-Personalkosten – Szenario")
st.caption("Theoretischer 12-Monats-Effekt")

left, middle, right = st.columns([1.05, 1, 1.25], gap="large")

with left:
    st.subheader("Treiber")
    revenue_change = st.slider("Planumsatz-Veränderung", -30, 30, -10, 1, "%d %%") / 100
    wage_change = st.slider("Lohn-/Gehaltsveränderung", -5, 15, 0, 1, "%d %%") / 100
    productivity_change = st.slider("Produktivität", -15, 20, 2, 1, "%d %%") / 100
    variable_hours_change = st.slider("Variable Stunden", -50, 30, -15, 1, "%d %%") / 100
    one_off = st.number_input("Sondereffekte (€)", value=0.0, step=250_000.0, format="%.0f")

with middle:
    st.subheader("Ausgangsbasis")
    plan_revenue = st.number_input("Planumsatz 12 Monate (€)", min_value=0.0, value=500_000_000.0, step=5_000_000.0, format="%.0f")
    plan_pc = st.number_input("Plan-Personalkosten 12 Monate (€)", min_value=0.0, value=100_000_000.0, step=1_000_000.0, format="%.0f")
    fixed_share = st.number_input("Fixer Kostenanteil (%)", min_value=0.0, max_value=100.0, value=70.0, step=1.0) / 100
    semi_share = st.number_input("Semivariabler Anteil (%)", min_value=0.0, max_value=100.0, value=20.0, step=1.0) / 100
    variable_share = 1 - fixed_share - semi_share
    if variable_share < 0:
        st.error("Fixer und semivariabler Anteil dürfen zusammen höchstens 100 % ergeben.")
        st.stop()
    st.text_input("Variabler Anteil", value=pct(variable_share), disabled=True)

semi_elasticity = 0.30
variable_elasticity = 0.80

base_fixed = plan_pc * fixed_share
base_semi = plan_pc * semi_share
base_variable = plan_pc * variable_share

rev_ratio = max(0.0, 1 + revenue_change)
prod_ratio = max(0.01, 1 + productivity_change)
demand_ratio = rev_ratio / prod_ratio
hours_factor = max(0.0, 1 + variable_hours_change)

new_revenue = plan_revenue * rev_ratio
new_fixed = base_fixed
new_semi = base_semi * demand_ratio ** semi_elasticity
new_variable = base_variable * demand_ratio ** variable_elasticity * hours_factor
new_pc = (new_fixed + new_semi + new_variable) * (1 + wage_change) + one_off

base_ratio = plan_pc / plan_revenue if plan_revenue else math.nan
new_ratio = new_pc / new_revenue if new_revenue else math.nan

with right:
    st.subheader("Management Case")
    df = pd.DataFrame([
        ["Umsatz", eur_m(plan_revenue), eur_m(new_revenue), delta_eur(new_revenue - plan_revenue)],
        ["Personalkosten", eur_m(plan_pc), eur_m(new_pc), delta_eur(new_pc - plan_pc)],
        ["Personalkostenquote", pct(base_ratio), pct(new_ratio), delta_pp(new_ratio - base_ratio)],
        ["Fixe Personalkosten", eur_m(base_fixed), eur_m(new_fixed * (1 + wage_change)), delta_eur(new_fixed * (1 + wage_change) - base_fixed)],
        ["Semivariable Personalkosten", eur_m(base_semi), eur_m(new_semi * (1 + wage_change)), delta_eur(new_semi * (1 + wage_change) - base_semi)],
        ["Variable Personalkosten", eur_m(base_variable), eur_m(new_variable * (1 + wage_change)), delta_eur(new_variable * (1 + wage_change) - base_variable)],
        ["Sondereffekte", "0,0 Mio. €", eur_m(one_off), delta_eur(one_off)],
    ], columns=["Kennzahl", "Ausgangsbasis", "Management Case", "Veränderung"])

    st.dataframe(df, hide_index=True, use_container_width=True)
