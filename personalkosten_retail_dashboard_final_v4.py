import math
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Personalkosten – Retail",
    page_icon="📊",
    layout="wide",
)

# -----------------------------
# Formatierung
# -----------------------------
def fmt_teur(value: float) -> str:
    return f"{value:,.0f} TEUR".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_pct(value: float) -> str:
    return f"{value:.1%}".replace(".", ",")

def fmt_delta_teur(value: float) -> str:
    sign = "+" if value > 0 else ""
    return (sign + f"{value:,.0f} TEUR").replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_delta_pp(value: float) -> str:
    sign = "+" if value > 0 else ""
    return (sign + f"{value * 100:.1f} %-Pkt.").replace(".", ",")

# -----------------------------
# Standardwerte
# -----------------------------
DEFAULTS = {
    "plan_revenue": 500_000.0,
    "plan_pc": 100_000.0,
    "fixed_share": 70.0,
    "semi_share": 20.0,
    "savings_target": 5_000.0,
    "semi_elasticity": 0.30,
    "variable_elasticity": 0.80,
    "revenue_change": -10,
    "wage_change": 3,
    "productivity_change": 2,
    "variable_hours_change": -15,
    "one_off": 0.0,
    "hiring_freeze": "Nein",
    "freeze_partial_effect": 2.0,
    "freeze_full_effect": 5.0,
}

for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)

def reset_all() -> None:
    for key, value in DEFAULTS.items():
        st.session_state[key] = value

# -----------------------------
# Kopfbereich
# -----------------------------
title_left, title_right = st.columns([3, 1])

with title_left:
    st.title("Personalkosten – Retail")
    st.caption("Theoretischer 12-Monats-Effekt")

with title_right:
    st.write("")
    st.button(
        "Auf Ausgangswerte zurücksetzen",
        on_click=reset_all,
        use_container_width=True,
    )

info_left, _ = st.columns([3, 1])

with info_left:
    st.info(
        """
**Wirkungslogik**

- **Fixer Block:** keine Reaktion auf Umsatzänderungen
- **Semivariabler Block:** *(tlw. anpassbar, aber durch Vertragsstunden und Mindestbesetzung begrenzt)*
- **Variabler Block:** stärkere Reaktion *(z. B. Aushilfen und Mehrarbeit)*
- **Einstellungsstopp:** wirkt über nicht oder verzögert nachbesetzte Stellen
"""
    )

# -----------------------------
# Hauptlayout
# -----------------------------
left, middle, right = st.columns([1.05, 1, 1.35], gap="large")

# -----------------------------
# Treiber
# -----------------------------
with left:
    st.subheader("Treiber")

    revenue_change = st.slider(
        "Planumsatz-Veränderung",
        min_value=-30,
        max_value=30,
        step=1,
        format="%d %%",
        key="revenue_change",
    ) / 100

    wage_change = st.slider(
        "Lohn-/Gehaltsveränderung",
        min_value=0,
        max_value=15,
        step=1,
        format="%d %%",
        key="wage_change",
    ) / 100

    productivity_change = st.slider(
        "Produktivität",
        min_value=-15,
        max_value=20,
        step=1,
        format="%d %%",
        key="productivity_change",
    ) / 100

    variable_hours_change = st.slider(
        "Variable Stunden",
        min_value=-50,
        max_value=30,
        step=1,
        format="%d %%",
        key="variable_hours_change",
    ) / 100

    one_off = st.number_input(
        "Sondereffekte (TEUR)",
        step=250.0,
        format="%.0f",
        key="one_off",
    )

    hiring_freeze = st.selectbox(
        "Einstellungsstopp",
        options=["Nein", "Teilweise", "Ja"],
        key="hiring_freeze",
    )

# -----------------------------
# Ausgangsbasis
# -----------------------------
with middle:
    st.subheader("Ausgangsbasis")

    plan_revenue = st.number_input(
        "Planumsatz 12 Monate (TEUR)",
        min_value=0.0,
        step=5_000.0,
        format="%.0f",
        key="plan_revenue",
    )

    plan_pc = st.number_input(
        "Plan-Personalkosten 12 Monate (TEUR)",
        min_value=0.0,
        step=1_000.0,
        format="%.0f",
        key="plan_pc",
    )

    fixed_share = st.number_input(
        "Fixer Kostenanteil (%)",
        min_value=0.0,
        max_value=100.0,
        step=1.0,
        key="fixed_share",
    ) / 100

    semi_share = st.number_input(
        "Semivariabler Anteil (%)",
        min_value=0.0,
        max_value=100.0,
        step=1.0,
        key="semi_share",
    ) / 100

    variable_share = 1 - fixed_share - semi_share

    if variable_share < 0:
        st.error("Fixer und semivariabler Anteil dürfen zusammen höchstens 100 % ergeben.")
        st.stop()

    st.text_input(
        "Variabler Anteil",
        value=fmt_pct(variable_share),
        disabled=True,
    )

    savings_target = st.number_input(
        "Einsparziel Personalkosten (TEUR)",
        min_value=0.0,
        step=500.0,
        format="%.0f",
        key="savings_target",
    )

    with st.expander("Modellannahmen"):
        semi_elasticity = st.slider(
            "Elastizität semivariabler Block",
            min_value=0.0,
            max_value=1.5,
            step=0.05,
            key="semi_elasticity",
        )

        variable_elasticity = st.slider(
            "Elastizität variabler Block",
            min_value=0.0,
            max_value=1.5,
            step=0.05,
            key="variable_elasticity",
        )

        freeze_partial_effect = st.slider(
            "Effekt teilweiser Einstellungsstopp (%)",
            min_value=0.0,
            max_value=10.0,
            step=0.5,
            key="freeze_partial_effect",
        ) / 100

        freeze_full_effect = st.slider(
            "Effekt vollständiger Einstellungsstopp (%)",
            min_value=0.0,
            max_value=15.0,
            step=0.5,
            key="freeze_full_effect",
        ) / 100

# -----------------------------
# Berechnung
# -----------------------------
base_fixed = plan_pc * fixed_share
base_semi = plan_pc * semi_share
base_variable = plan_pc * variable_share

revenue_ratio = max(0.0, 1 + revenue_change)
productivity_ratio = max(0.01, 1 + productivity_change)
demand_ratio = revenue_ratio / productivity_ratio
hours_factor = max(0.0, 1 + variable_hours_change)

new_revenue = plan_revenue * revenue_ratio

new_fixed_before_wage = base_fixed
new_semi_before_freeze = base_semi * (demand_ratio ** semi_elasticity)

freeze_reduction = {
    "Nein": 0.0,
    "Teilweise": freeze_partial_effect,
    "Ja": freeze_full_effect,
}[hiring_freeze]

new_semi_before_wage = new_semi_before_freeze * (1 - freeze_reduction)
freeze_effect_before_wage = new_semi_before_wage - new_semi_before_freeze

new_variable_before_wage = (
    base_variable
    * (demand_ratio ** variable_elasticity)
    * hours_factor
)

new_fixed = new_fixed_before_wage * (1 + wage_change)
new_semi = new_semi_before_wage * (1 + wage_change)
new_variable = new_variable_before_wage * (1 + wage_change)
freeze_effect = freeze_effect_before_wage * (1 + wage_change)

new_pc = new_fixed + new_semi + new_variable + one_off

base_ratio = plan_pc / plan_revenue if plan_revenue else math.nan
new_ratio = new_pc / new_revenue if new_revenue else math.nan

pc_savings = plan_pc - new_pc
remaining_gap = max(0.0, savings_target - pc_savings)
target_achievement = pc_savings / savings_target if savings_target > 0 else math.nan

# -----------------------------
# Management Case
# -----------------------------
with right:
    st.subheader("Management Case")

    rows = [
        {
            "Kennzahl": "Umsatz",
            "Ausgangsbasis": fmt_teur(plan_revenue),
            "Management Case": fmt_teur(new_revenue),
            "Veränderung": fmt_delta_teur(new_revenue - plan_revenue),
            "_delta": new_revenue - plan_revenue,
            "_logic": "revenue",
        },
        {
            "Kennzahl": "Personalkosten",
            "Ausgangsbasis": fmt_teur(plan_pc),
            "Management Case": fmt_teur(new_pc),
            "Veränderung": fmt_delta_teur(new_pc - plan_pc),
            "_delta": new_pc - plan_pc,
            "_logic": "cost",
        },
        {
            "Kennzahl": "Personalkostenquote",
            "Ausgangsbasis": fmt_pct(base_ratio),
            "Management Case": fmt_pct(new_ratio),
            "Veränderung": fmt_delta_pp(new_ratio - base_ratio),
            "_delta": new_ratio - base_ratio,
            "_logic": "cost",
        },
        {
            "Kennzahl": "Fixe Personalkosten",
            "Ausgangsbasis": fmt_teur(base_fixed),
            "Management Case": fmt_teur(new_fixed),
            "Veränderung": fmt_delta_teur(new_fixed - base_fixed),
            "_delta": new_fixed - base_fixed,
            "_logic": "cost",
        },
        {
            "Kennzahl": "Semivariable Personalkosten",
            "Ausgangsbasis": fmt_teur(base_semi),
            "Management Case": fmt_teur(new_semi),
            "Veränderung": fmt_delta_teur(new_semi - base_semi),
            "_delta": new_semi - base_semi,
            "_logic": "cost",
        },
        {
            "Kennzahl": "davon Einstellungsstopp",
            "Ausgangsbasis": "0 TEUR",
            "Management Case": fmt_teur(freeze_effect),
            "Veränderung": fmt_delta_teur(freeze_effect),
            "_delta": freeze_effect,
            "_logic": "cost",
        },
        {
            "Kennzahl": "Variable Personalkosten",
            "Ausgangsbasis": fmt_teur(base_variable),
            "Management Case": fmt_teur(new_variable),
            "Veränderung": fmt_delta_teur(new_variable - base_variable),
            "_delta": new_variable - base_variable,
            "_logic": "cost",
        },
        {
            "Kennzahl": "Sondereffekte",
            "Ausgangsbasis": "0 TEUR",
            "Management Case": fmt_teur(one_off),
            "Veränderung": fmt_delta_teur(one_off),
            "_delta": one_off,
            "_logic": "cost",
        },
    ]

    raw_df = pd.DataFrame(rows)
    display_df = raw_df[
        ["Kennzahl", "Ausgangsbasis", "Management Case", "Veränderung"]
    ]

    def style_change_column(row):
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
        .apply(style_change_column, axis=1)
        .set_properties(**{"text-align": "left", "font-size": "14px"})
        .set_table_styles(
            [
                {
                    "selector": "th",
                    "props": [
                        ("font-weight", "700"),
                        ("text-align", "left"),
                    ],
                }
            ]
        )
    )

    st.dataframe(
        styled_df,
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("#### Einsparziel")
    kpi1, kpi2, kpi3 = st.columns(3)

    kpi1.metric("Ziel", fmt_teur(savings_target))
    kpi2.metric("Erreicht", fmt_teur(pc_savings))
    kpi3.metric(
        "Zielerreichung",
        fmt_pct(target_achievement) if not math.isnan(target_achievement) else "–",
    )

    if remaining_gap > 0:
        st.warning(f"Verbleibende Lücke zum Einsparziel: {fmt_teur(remaining_gap)}")
    else:
        st.success("Das Einsparziel wird im Modell erreicht.")

# -----------------------------
# Plausibilitätschecks
# -----------------------------
if revenue_change < 0 and variable_hours_change > 0:
    st.warning(
        "Der Umsatz sinkt, während die variablen Stunden steigen. "
        "Diese Kombination sollte fachlich geprüft werden."
    )

if hiring_freeze == "Ja" and revenue_change > 10:
    st.warning(
        "Bei starkem Umsatzwachstum und vollständigem Einstellungsstopp "
        "sollte die operative Umsetzbarkeit geprüft werden."
    )
