import math
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Personalkosten – Retail (Szenarien)",
    page_icon="📊",
    layout="wide",
)

# -----------------------------
# Formatierung
# -----------------------------
def fmt_teur(v: float) -> str:
    return f"{v:,.0f} TEUR".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_pct(v: float) -> str:
    return f"{v:.1%}".replace(".", ",")

def fmt_delta_teur(v: float) -> str:
    sign = "+" if v > 0 else ""
    return (sign + f"{v:,.0f} TEUR").replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_delta_pp(v: float) -> str:
    sign = "+" if v > 0 else ""
    return (sign + f"{v * 100:.1f} %-Pkt.").replace(".", ",")

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
}

for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)

def reset_all():
    for key, value in DEFAULTS.items():
        st.session_state[key] = value

# -----------------------------
# Titel
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

st.info(
    """
**Wirkungslogik**

- Der **fixe Block** reagiert nicht auf Umsatzänderungen.
- Der **semivariable Block** reagiert unterproportional.
- Der **variable Block** reagiert deutlich stärker.
- Eine Veränderung der **variablen Stunden** wirkt zusätzlich direkt auf den variablen Kostenblock.
"""
)

left, middle, right = st.columns([1.05, 1, 1.3], gap="large")

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
        help="Wirkt auf den semivariablen und variablen Kostenblock.",
    ) / 100

    wage_change = st.slider(
        "Lohn-/Gehaltsveränderung",
        min_value=0,
        max_value=15,
        step=1,
        format="%d %%",
        key="wage_change",
        help="Wirkt auf alle Personalkostenblöcke.",
    ) / 100

    productivity_change = st.slider(
        "Produktivität",
        min_value=-15,
        max_value=20,
        step=1,
        format="%d %%",
        key="productivity_change",
        help="Positive Werte bedeuten mehr Umsatz je bezahlter Stunde.",
    ) / 100

    variable_hours_change = st.slider(
        "Variable Stunden",
        min_value=-50,
        max_value=30,
        step=1,
        format="%d %%",
        key="variable_hours_change",
        help="Wirkt zusätzlich direkt auf den variablen Kostenblock.",
    ) / 100

    one_off = st.number_input(
        "Sondereffekte (TEUR)",
        step=250.0,
        format="%.0f",
        key="one_off",
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

# -----------------------------
# Berechnung
# -----------------------------
base_fixed = plan_pc * fixed_share
base_semi = plan_pc * semi_share
base_variable = plan_pc * variable_share

rev_ratio = max(0.0, 1 + revenue_change)
prod_ratio = max(0.01, 1 + productivity_change)
demand_ratio = rev_ratio / prod_ratio
hours_factor = max(0.0, 1 + variable_hours_change)

after_revenue = (
    base_fixed
    + base_semi * (rev_ratio ** semi_elasticity)
    + base_variable * (rev_ratio ** variable_elasticity)
)
after_productivity = (
    base_fixed
    + base_semi * (demand_ratio ** semi_elasticity)
    + base_variable * (demand_ratio ** variable_elasticity)
)
after_hours = (
    base_fixed
    + base_semi * (demand_ratio ** semi_elasticity)
    + base_variable * (demand_ratio ** variable_elasticity) * hours_factor
)
after_wage = after_hours * (1 + wage_change)

new_revenue = plan_revenue * rev_ratio
new_fixed = base_fixed
new_semi = base_semi * demand_ratio ** semi_elasticity
new_variable = base_variable * demand_ratio ** variable_elasticity * hours_factor
new_pc = after_wage + one_off

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
            "Management Case": fmt_teur(new_fixed * (1 + wage_change)),
            "Veränderung": fmt_delta_teur(new_fixed * (1 + wage_change) - base_fixed),
            "_delta": new_fixed * (1 + wage_change) - base_fixed,
            "_logic": "cost",
        },
        {
            "Kennzahl": "Semivariable Personalkosten",
            "Ausgangsbasis": fmt_teur(base_semi),
            "Management Case": fmt_teur(new_semi * (1 + wage_change)),
            "Veränderung": fmt_delta_teur(new_semi * (1 + wage_change) - base_semi),
            "_delta": new_semi * (1 + wage_change) - base_semi,
            "_logic": "cost",
        },
        {
            "Kennzahl": "Variable Personalkosten",
            "Ausgangsbasis": fmt_teur(base_variable),
            "Management Case": fmt_teur(new_variable * (1 + wage_change)),
            "Veränderung": fmt_delta_teur(new_variable * (1 + wage_change) - base_variable),
            "_delta": new_variable * (1 + wage_change) - base_variable,
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
        .set_properties(**{"text-align": "left", "font-size": "14px"})
        .set_table_styles([
            {
                "selector": "th",
                "props": [("font-weight", "700"), ("text-align", "left")],
            }
        ])
    )

    st.dataframe(styled_df, hide_index=True, use_container_width=True)

    st.markdown("#### Einsparziel")
    k1, k2, k3 = st.columns(3)
    k1.metric("Ziel", fmt_teur(savings_target))
    k2.metric("Erreicht", fmt_teur(pc_savings))
    k3.metric(
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
warnings = []

if revenue_change < 0 and variable_hours_change > 0:
    warnings.append(
        "Der Umsatz sinkt, während die variablen Stunden steigen. Diese Kombination sollte fachlich geprüft werden."
    )

if productivity_change > 10 and variable_hours_change > 0:
    warnings.append(
        "Hohe Produktivitätssteigerung und gleichzeitig steigende variable Stunden wirken möglicherweise widersprüchlich."
    )

if not math.isnan(new_ratio) and new_ratio > base_ratio + 0.03:
    warnings.append("Die Personalkostenquote steigt um mehr als 3 Prozentpunkte.")

for warning in warnings:
    st.warning(warning)

# -----------------------------
# Untere Charts
# -----------------------------
st.divider()
chart_left, chart_right = st.columns(2, gap="large")

with chart_left:
    st.subheader("Wirkungsbrücke")

    revenue_effect = after_revenue - plan_pc
    productivity_effect = after_productivity - after_revenue
    hours_effect = after_hours - after_productivity
    wage_effect = after_wage - after_hours

    waterfall = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=["absolute", "relative", "relative", "relative", "relative", "relative", "total"],
            x=[
                "Plan-PK",
                "Umsatz",
                "Produktivität",
                "Variable Stunden",
                "Lohn",
                "Sondereffekte",
                "Neue PK",
            ],
            y=[
                plan_pc,
                revenue_effect,
                productivity_effect,
                hours_effect,
                wage_effect,
                one_off,
                0,
            ],
            connector={"line": {"color": "#9CA3AF", "width": 1}},
            increasing={"marker": {"color": "#B91C1C"}},
            decreasing={"marker": {"color": "#15803D"}},
            totals={"marker": {"color": "#1F3C88"}},
            text=[
                fmt_teur(plan_pc),
                fmt_delta_teur(revenue_effect),
                fmt_delta_teur(productivity_effect),
                fmt_delta_teur(hours_effect),
                fmt_delta_teur(wage_effect),
                fmt_delta_teur(one_off),
                fmt_teur(new_pc),
            ],
            textposition="outside",
        )
    )

    waterfall.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        yaxis_title="TEUR",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(waterfall, use_container_width=True)

with chart_right:
    st.subheader("12M IST + Forecast")

    today = pd.Timestamp.today().to_period("M").to_timestamp()
    actual_months = pd.date_range(end=today, periods=12, freq="MS")
    forecast_months = pd.date_range(start=today + pd.offsets.MonthBegin(1), periods=12, freq="MS")

    # Beispielhafte IST-Historie mit eigenem Verlauf
    monthly_base = plan_pc / 12
    actual_pattern = pd.Series(
        [0.95, 0.97, 1.01, 0.99, 1.02, 1.00, 1.03, 1.01, 0.98, 1.04, 1.08, 0.92]
    )
    actual_values = monthly_base * actual_pattern
    actual_values = actual_values * (plan_pc / actual_values.sum())

    # Forecast startet am letzten IST-Wert und entwickelt sich von dort weiter.
    last_actual = float(actual_values.iloc[-1])

    # Saisonale Zukunftsfaktoren – bewusst nicht identisch zur IST-Kurve
    future_seasonality = pd.Series(
        [0.99, 1.00, 1.01, 1.02, 1.01, 1.00, 0.99, 1.01, 1.03, 1.05, 1.08, 0.96]
    )

    # Gesamte Szenariowirkung relativ zur Planung
    scenario_ratio = new_pc / plan_pc if plan_pc else 1.0

    # Die Wirkung wird über 12 Monate schrittweise aufgebaut
    phase_in = pd.Series([i / 12 for i in range(1, 13)])
    scenario_path = 1 + (scenario_ratio - 1) * phase_in

    raw_forecast = last_actual * future_seasonality * scenario_path

    # Auf den berechneten 12-Monats-Forecast kalibrieren
    forecast_values = raw_forecast * (new_pc / raw_forecast.sum()) if raw_forecast.sum() else raw_forecast

    actual_df = pd.DataFrame({
        "Monat": actual_months,
        "Personalkosten": actual_values.values,
        "Typ": "IST",
    })

    forecast_df = pd.DataFrame({
        "Monat": forecast_months,
        "Personalkosten": forecast_values.values,
        "Typ": "Forecast",
    })

    # Letzten IST-Punkt als Anker in die Forecast-Linie aufnehmen
    forecast_plot_months = [actual_df["Monat"].iloc[-1]] + forecast_df["Monat"].tolist()
    forecast_plot_values = [actual_df["Personalkosten"].iloc[-1]] + forecast_df["Personalkosten"].tolist()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=actual_df["Monat"],
            y=actual_df["Personalkosten"],
            mode="lines+markers",
            name="IST",
            line=dict(color="#1F3C88", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast_plot_months,
            y=forecast_plot_values,
            mode="lines+markers",
            name="Forecast",
            line=dict(color="#4F46E5", width=2, dash="dash"),
        )
    )

    fig.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=10, b=10),
        yaxis_title="TEUR",
        xaxis_title="Monat",
        legend_title="",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Der Forecast startet am letzten IST-Wert. Die Szenariowirkung wird über die kommenden Monate schrittweise sichtbar.")

