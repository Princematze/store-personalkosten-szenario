import math
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Store-Personalkosten", page_icon="📊", layout="wide")
st.title("Store-Personalkosten – Szenariosteuerung")
st.caption("Theoretischer 12-Monats-Effekt aus wenigen zentralen Treibern")

def pct(x):
    return f"{x:.1%}".replace(".", ",")

def eur_m(x):
    return f"{x / 1_000_000:,.1f} Mio. €".replace(",", "X").replace(".", ",").replace("X", ".")

with st.sidebar:
    st.header("Ausgangsbasis")
    plan_revenue = st.number_input("Planumsatz 12 Monate (€)", 0.0, value=500_000_000.0, step=5_000_000.0)
    plan_pc = st.number_input("Plan-Personalkosten 12 Monate (€)", 0.0, value=100_000_000.0, step=1_000_000.0)
    cost_per_fte = st.number_input("Ø Vollkosten je FTE/Jahr (€)", 1.0, value=42_000.0, step=1_000.0)

    st.header("Kostenstruktur")
    fixed_share = st.slider("Fixer Kostenanteil", 0, 100, 70) / 100
    semi_share = st.slider("Semivariabler Kostenanteil", 0, 100, 20) / 100
    variable_share = 1 - fixed_share - semi_share

    if variable_share < 0:
        st.error("Fixer und semivariabler Anteil dürfen zusammen höchstens 100 % ergeben.")
        st.stop()

    st.metric("Variabler Kostenanteil", pct(variable_share))

    with st.expander("Erweiterte Modellparameter"):
        semi_elasticity = st.slider("Elastizität semivariable Kosten", 0.0, 1.5, 0.30, 0.05)
        variable_elasticity = st.slider("Elastizität variable Kosten", 0.0, 1.5, 0.80, 0.05)

st.subheader("Treiber")
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    revenue_change = st.slider("Planumsatz-Veränderung", -30, 30, -10) / 100
with c2:
    wage_change = st.slider("Lohn-/Gehaltsveränderung", -5, 15, 3) / 100
with c3:
    productivity_change = st.slider("Produktivitätsveränderung", -15, 20, 0) / 100
with c4:
    variable_hours_change = st.slider("Variable Stunden", -50, 30, -10) / 100
with c5:
    one_off = st.number_input("Sondereffekte (€)", value=0.0, step=250_000.0)

base_fixed = plan_pc * fixed_share
base_semi = plan_pc * semi_share
base_variable = plan_pc * variable_share

revenue_ratio = max(0.0, 1 + revenue_change)
productivity_ratio = max(0.01, 1 + productivity_change)
demand_ratio = revenue_ratio / productivity_ratio
variable_hours_factor = max(0.0, 1 + variable_hours_change)

after_revenue = (
    base_fixed
    + base_semi * revenue_ratio ** semi_elasticity
    + base_variable * revenue_ratio ** variable_elasticity
)
after_productivity = (
    base_fixed
    + base_semi * demand_ratio ** semi_elasticity
    + base_variable * demand_ratio ** variable_elasticity
)
after_variable_hours = (
    base_fixed
    + base_semi * demand_ratio ** semi_elasticity
    + base_variable * demand_ratio ** variable_elasticity * variable_hours_factor
)
after_wage = after_variable_hours * (1 + wage_change)

new_pc = after_wage + one_off
new_revenue = plan_revenue * revenue_ratio
pc_delta = new_pc - plan_pc
revenue_delta = new_revenue - plan_revenue

old_ratio = plan_pc / plan_revenue if plan_revenue else math.nan
new_ratio = new_pc / new_revenue if new_revenue else math.nan
fte_equivalent = abs(pc_delta) / cost_per_fte if cost_per_fte else math.nan

st.subheader("Theoretischer 12-Monats-Effekt")
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Neuer Umsatz", eur_m(new_revenue), eur_m(revenue_delta))
k2.metric("Neue Personalkosten", eur_m(new_pc), eur_m(pc_delta), delta_color="inverse")
k3.metric(
    "Personalkostenquote",
    pct(new_ratio) if not math.isnan(new_ratio) else "–",
    f"{(new_ratio-old_ratio)*100:+.1f} %-Pkt." if not math.isnan(new_ratio) else None,
    delta_color="inverse",
)
k4.metric("PK-Veränderung", pct(pc_delta / plan_pc) if plan_pc else "–")
k5.metric("FTE-Äquivalent", f"{fte_equivalent:,.0f}".replace(",", "."))

left, right = st.columns([1.4, 1])

with left:
    st.markdown("#### Wirkungsbrücke")
    fig = go.Figure(go.Waterfall(
        measure=["absolute", "relative", "relative", "relative", "relative", "relative", "total"],
        x=["Plan-PK", "Umsatz", "Produktivität", "Variable Stunden", "Lohn", "Sondereffekte", "Neue PK"],
        y=[
            plan_pc,
            after_revenue - plan_pc,
            after_productivity - after_revenue,
            after_variable_hours - after_productivity,
            after_wage - after_variable_hours,
            one_off,
            0,
        ],
        connector={"line": {"width": 1}},
    ))
    fig.update_layout(height=420, margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.markdown("#### Kostenstruktur")
    structure = pd.DataFrame({
        "Kostenblock": ["Fix", "Semivariabel", "Variabel"],
        "Plan": [base_fixed, base_semi, base_variable],
        "Szenario": [
            base_fixed * (1 + wage_change),
            base_semi * demand_ratio ** semi_elasticity * (1 + wage_change),
            base_variable * demand_ratio ** variable_elasticity * variable_hours_factor * (1 + wage_change),
        ],
    }).melt(id_vars="Kostenblock", var_name="Version", value_name="Personalkosten")
    st.bar_chart(structure, x="Kostenblock", y="Personalkosten", color="Version", height=420)

st.subheader("Management-Interpretation")
effect = "Einsparung" if pc_delta < 0 else "Mehrkosten"
st.write(
    f"Das Szenario führt theoretisch zu **{eur_m(abs(pc_delta))} {effect}**. "
    f"Die Personalkostenquote verändert sich von **{pct(old_ratio)}** auf **{pct(new_ratio)}**."
)
st.caption(
    "Theoretische Szenariorechnung. Die operative Umsetzbarkeit hängt vom tatsächlichen "
    "Fixkostenanteil, Vertragsbindungen und möglichen Personalmaßnahmen ab."
)
