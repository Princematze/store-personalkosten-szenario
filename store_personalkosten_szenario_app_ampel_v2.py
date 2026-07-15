import math
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Store-Personalkosten – Szenario",
    page_icon="📊",
    layout="wide",
)

def eur_m(v: float) -> str:
    return f"{v / 1_000_000:,.1f} Mio. €".replace(",", "X").replace(".", ",").replace("X", ".")

def pct(v: float) -> str:
    return f"{v:.1%}".replace(".", ",")

def delta_eur(v: float) -> str:
    sign = "+" if v > 0 else ""
    return (sign + f"{v / 1_000_000:,.1f} Mio. €").replace(",", "X").replace(".", ",").replace("X", ".")

def delta_pp(v: float) -> str:
    sign = "+" if v > 0 else ""
    return (sign + f"{v * 100:.1f} %-Pkt.").replace(".", ",")

st.title("Store-Personalkosten – Szenario")
st.caption("Theoretischer 12-Monats-Effekt")

left, middle, right = st.columns([1.05, 1, 1.25], gap="large")

# -----------------------------
# Treiber
# -----------------------------
with left:
    st.subheader("Treiber")

    revenue_change = st.slider(
        "Planumsatz-Veränderung",
        min_value=-30,
        max_value=30,
        value=-10,
        step=1,
        format="%d %%",
    ) / 100

    wage_change = st.slider(
        "Lohn-/Gehaltsveränderung",
        min_value=0,
        max_value=15,
        value=0,
        step=1,
        format="%d %%",
    ) / 100

    productivity_change = st.slider(
        "Produktivität",
        min_value=-15,
        max_value=20,
        value=2,
        step=1,
        format="%d %%",
        help="Positive Werte bedeuten mehr Umsatz je bezahlter Stunde.",
    ) / 100

    variable_hours_change = st.slider(
        "Variable Stunden",
        min_value=-50,
        max_value=30,
        value=-15,
        step=1,
        format="%d %%",
    ) / 100

    one_off = st.number_input(
        "Sondereffekte (€)",
        value=0.0,
        step=250_000.0,
        format="%.0f",
    )

# -----------------------------
# Ausgangsbasis
# -----------------------------
with middle:
    st.subheader("Ausgangsbasis")

    plan_revenue = st.number_input(
        "Planumsatz 12 Monate (€)",
        min_value=0.0,
        value=500_000_000.0,
        step=5_000_000.0,
        format="%.0f",
    )

    plan_pc = st.number_input(
        "Plan-Personalkosten 12 Monate (€)",
        min_value=0.0,
        value=100_000_000.0,
        step=1_000_000.0,
        format="%.0f",
    )

    fixed_share = st.number_input(
        "Fixer Kostenanteil (%)",
        min_value=0.0,
        max_value=100.0,
        value=70.0,
        step=1.0,
    ) / 100

    semi_share = st.number_input(
        "Semivariabler Anteil (%)",
        min_value=0.0,
        max_value=100.0,
        value=20.0,
        step=1.0,
    ) / 100

    variable_share = 1 - fixed_share - semi_share

    if variable_share < 0:
        st.error("Fixer und semivariabler Anteil dürfen zusammen höchstens 100 % ergeben.")
        st.stop()

    st.text_input(
        "Variabler Anteil",
        value=pct(variable_share),
        disabled=True,
    )

# -----------------------------
# Modell
# -----------------------------
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

# -----------------------------
# Management Case
# -----------------------------
with right:
    st.subheader("Management Case")

    rows = [
        {
            "Kennzahl": "Umsatz",
            "Ausgangsbasis": eur_m(plan_revenue),
            "Management Case": eur_m(new_revenue),
            "Veränderung": delta_eur(new_revenue - plan_revenue),
            "_delta": new_revenue - plan_revenue,
            "_logic": "revenue",
        },
        {
            "Kennzahl": "Personalkosten",
            "Ausgangsbasis": eur_m(plan_pc),
            "Management Case": eur_m(new_pc),
            "Veränderung": delta_eur(new_pc - plan_pc),
            "_delta": new_pc - plan_pc,
            "_logic": "cost",
        },
        {
            "Kennzahl": "Personalkostenquote",
            "Ausgangsbasis": pct(base_ratio),
            "Management Case": pct(new_ratio),
            "Veränderung": delta_pp(new_ratio - base_ratio),
            "_delta": new_ratio - base_ratio,
            "_logic": "cost",
        },
        {
            "Kennzahl": "Fixe Personalkosten",
            "Ausgangsbasis": eur_m(base_fixed),
            "Management Case": eur_m(new_fixed * (1 + wage_change)),
            "Veränderung": delta_eur(new_fixed * (1 + wage_change) - base_fixed),
            "_delta": new_fixed * (1 + wage_change) - base_fixed,
            "_logic": "cost",
        },
        {
            "Kennzahl": "Semivariable Personalkosten",
            "Ausgangsbasis": eur_m(base_semi),
            "Management Case": eur_m(new_semi * (1 + wage_change)),
            "Veränderung": delta_eur(new_semi * (1 + wage_change) - base_semi),
            "_delta": new_semi * (1 + wage_change) - base_semi,
            "_logic": "cost",
        },
        {
            "Kennzahl": "Variable Personalkosten",
            "Ausgangsbasis": eur_m(base_variable),
            "Management Case": eur_m(new_variable * (1 + wage_change)),
            "Veränderung": delta_eur(new_variable * (1 + wage_change) - base_variable),
            "_delta": new_variable * (1 + wage_change) - base_variable,
            "_logic": "cost",
        },
        {
            "Kennzahl": "Sondereffekte",
            "Ausgangsbasis": "0,0 Mio. €",
            "Management Case": eur_m(one_off),
            "Veränderung": delta_eur(one_off),
            "_delta": one_off,
            "_logic": "cost",
        },
    ]

    raw_df = pd.DataFrame(rows)
    display_df = raw_df[["Kennzahl", "Ausgangsbasis", "Management Case", "Veränderung"]]

    def style_rows(row):
        idx = row.name
        delta = raw_df.loc[idx, "_delta"]
        logic = raw_df.loc[idx, "_logic"]

        styles = ["", "", "", ""]

        if abs(delta) < 1e-9:
            styles[3] = "color: #6B7280; font-weight: 600;"
        elif logic == "revenue":
            styles[3] = (
                "color: #15803D; font-weight: 700;"
                if delta > 0
                else "color: #B91C1C; font-weight: 700;"
            )
        else:
            styles[3] = (
                "color: #B91C1C; font-weight: 700;"
                if delta > 0
                else "color: #15803D; font-weight: 700;"
            )

        return styles

    styled_df = (
        display_df.style
        .apply(style_rows, axis=1)
        .set_properties(**{
            "text-align": "left",
            "font-size": "14px",
        })
        .set_table_styles([
            {
                "selector": "th",
                "props": [
                    ("font-weight", "700"),
                    ("text-align", "left"),
                ],
            }
        ])
    )

    st.dataframe(
        styled_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Kennzahl": st.column_config.TextColumn("Kennzahl", width="medium"),
            "Ausgangsbasis": st.column_config.TextColumn("Ausgangsbasis", width="small"),
            "Management Case": st.column_config.TextColumn("Management Case", width="small"),
            "Veränderung": st.column_config.TextColumn("Veränderung", width="small"),
        },
    )

# -----------------------------
# Infobox
# -----------------------------
st.info(
    """
**Wirkungslogik**

- Der **fixe Block** reagiert nicht auf Umsatzänderungen.
- Der **semivariable Block** reagiert unterproportional.
- Der **variable Block** reagiert deutlich stärker.
- Eine Veränderung der **variablen Stunden** wirkt zusätzlich direkt auf den variablen Kostenblock.
"""
)
