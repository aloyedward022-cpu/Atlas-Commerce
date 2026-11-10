from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from donnees import filtrer, calculer_kpis, mad, df
from dash import Dash, html, dcc, Input, Output, ctx 

# Initialize app with Bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
app.title = "ATLAS COMMERCE - Dashboard"

# --- HELPER FUNCTIONS ---
def figure_vide(titre):
    """Affiche un message pour les filtres sans ventes."""
    fig = go.Figure()
    fig.add_annotation(
        text="Aucune vente pour ces filtres",
        x=0.5, y=0.5, xref="paper", yref="paper",
        showarrow=False
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(title=titre, template="plotly_white", height=350)
    return fig

def harmoniser(fig):
    """Applique une hauteur et un fond communs aux figures."""
    fig.update_layout(
        template="plotly_white", height=360,
        margin=dict(l=25, r=20, t=60, b=35)
    )
    return fig
# App Layout
app.layout = dbc.Container([
    html.Div([
        html.H1("ATLAS COMMERCE", className="text-white m-0"),
        html.P("Tableau de bord analytique des ventes (Maroc)", className="text-white-50 mb-0")
    ], style={"backgroundColor": "#0d6dfdd4", "padding": "20px", "borderRadius": "8px"}, className="mb-4"),
    
    html.Hr(),

    dbc.Row([
        dbc.Col([
            html.Label("Catégorie de produit :"),
            dcc.Dropdown(
                id="filtre-categorie",
                options=["Toutes"] + sorted(df["Categorie"].unique().tolist()),
                value="Toutes",
                clearable=False
            )
        ], width=4, className="mb-4")
    ]),

    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Chiffre d'Affaires", className="card-title text-muted fs-6"),
                html.H2(id="kpi-ca", className="text-success")
            ])
        ], className="shadow-sm"), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Commandes", className="card-title text-muted fs-6"),
                html.H2(id="kpi-commandes", className="text-primary")
            ])
        ], className="shadow-sm"), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Panier Moyen", className="card-title text-muted fs-6"),
                html.H2(id="kpi-panier", className="text-info")
            ])
        ], className="shadow-sm"), width=3),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Marge Totale", className="card-title text-muted fs-6"),
                html.H2(id="kpi-marge", className="text-warning")
            ])
        ], className="shadow-sm"), width=3),
    ], className="mb-4"),
    
   # Charts Row
       dbc.Row([
           dbc.Col([
               dbc.Card([
                   dbc.CardBody([
                       html.H4("Évolution du Chiffre d'Affaires Mensuel", className="card-title text-muted fs-6 mb-3"),
                       dcc.Graph(id="graph-tendance-ca", config={"displayModeBar": False})
                   ])
               ], className="shadow-sm mb-4")
           ], width=12)
       ]),
       # Regional Breakdown Row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Chiffre d'Affaires par Région", className="card-title text-muted fs-6 mb-3"),
                    dcc.Graph(id="graph-region-ca", config={"displayModeBar": False})
                ])
            ], className="shadow-sm mb-4")
        ], width=12)
    ]),
    # Margins Breakdown Row
      dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Marge commerciale par catégorie", className="card-title text-muted fs-6 mb-3"),
                    dcc.Graph(id="marges")
                ])
            ], className="shadow-sm mb-4")
        ], width=12)
    ]),
    # Top 10 Products Row
    dbc.Row([
        dbc.Col([
            html.H5(id="titre-top", className="text-secondary mb-3"),
            dcc.Graph(id="top-produits", config={"displayModeBar": False})
        ], width=12)
    ], className="g-3 mb-4"),
    dcc.Store(id="region-active", data=None),
    
    dbc.Row([
        dbc.Col(dbc.Button(
            "Effacer le filtre région", id="reset-region",
            color="outline-secondary", className="mb-3"
        ), xs=12)
    ]), 
    dbc.Alert(id="lecture-metier", color="info", className="mt-4"),
], fluid=True)

@app.callback(
    [Output("kpi-ca", "children"),
     Output("kpi-commandes", "children"),
     Output("kpi-panier", "children"),
     Output("kpi-marge", "children")],
    [Input("filtre-categorie", "value")]
)
def mettre_a_jour_kpis(categorie):
    donnees_filtrees = filtrer(categorie=categorie)
    kpis = calculer_kpis(donnees_filtrees)
    return (
        mad(kpis["ca"]),
        f"{kpis['commandes']:,}".replace(",", " "),
        mad(kpis["panier"]),
        mad(kpis["marge"])
    )


@app.callback(
    Output("graph-tendance-ca", "figure"),
    [Input("filtre-categorie", "value")]
)
def mettre_a_jour_tendance(categorie):
    donnees_filtrees = filtrer(categorie=categorie)
    df_mensuel = donnees_filtrees.copy()
    df_mensuel["Mois"] = df_mensuel["Date"].dt.to_period("M").dt.to_timestamp()
    df_ca = df_mensuel.groupby("Mois")["Chiffre_Affaires"].sum().reset_index()
    
    fig = px.line(
        df_ca, x="Mois", y="Chiffre_Affaires",
        markers=True,
        labels={"Mois": "Période", "Chiffre_Affaires": "Chiffre d'Affaires (MAD)"},
        template="plotly_white"
    )
    fig.update_traces(line_color="#0d6efd", line_width=3)
    fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=350)
    return fig

@app.callback(
    Output("graph-region-ca", "figure"),
    [Input("filtre-categorie", "value")]
)
def mettre_a_jour_regions(categorie):
    donnees_filtrees = filtrer(categorie=categorie)
    df_region = donnees_filtrees.groupby("Region")["Chiffre_Affaires"].sum().reset_index()
    df_region = df_region.sort_values(by="Chiffre_Affaires", ascending=True)

    fig = px.bar(
        df_region, x="Chiffre_Affaires", y="Region",
        orientation="h",
        labels={"Region": "Région", "Chiffre_Affaires": "Chiffre d'Affaires (MAD)"},
        template="plotly_white"
    )
    fig.update_traces(marker_color="#20c997")
    fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=350)
    return fig

@app.callback(
    Output("marges", "figure"),
    [Input("filtre-categorie", "value")]
)
def tracer_marges(categorie):
    ventes = filtrer(categorie=categorie)
    if ventes.empty:
        return figure_vide("Marge par catégorie")
    
    resume = (
        ventes.groupby("Categorie", as_index=False)["Marge"]
        .sum()
        .sort_values("Marge", ascending=False)
    )
    
    fig = px.bar(
        resume, x="Categorie", y="Marge", color="Categorie",
        title="Marge commerciale par catégorie",
        template="plotly_white"
    )
    fig.update_layout(showlegend=False, margin=dict(t=40, b=20, l=20, r=20), height=350)
    return fig

@app.callback(
    [Output("top-produits", "figure"),
     Output("titre-top", "children")],
    [Input("filtre-categorie", "value"),
     Input("region-active", "data")]
)
def tracer_top(categorie, region):
    ventes = filtrer(categorie=categorie)
    if region:
        ventes = ventes[ventes["Region"] == region].copy()
    
    titre = f"Top 10 des produits — {categorie}" + (f" ({region})" if region else " — Toutes régions")
    
    if ventes.empty:
        return figure_vide(titre), titre
        
    resume = (
        ventes.groupby("Produit", as_index=False)["Chiffre_Affaires"]
        .sum()
        .nlargest(10, "Chiffre_Affaires")
        .sort_values("Chiffre_Affaires", ascending=True)
    )
    
    fig = px.bar(
        resume, x="Chiffre_Affaires", y="Produit",
        orientation="h",
        labels={"Chiffre_Affaires": "Chiffre d'Affaires (MAD)", "Produit": "Produit"},
        template="plotly_white"
    )
    fig.update_traces(marker_color="#fd7e14")
    fig.update_layout(margin=dict(t=20, b=20, l=120, r=20), height=400)
    return fig, titre

@app.callback(
    Output("region-active", "data"),
    [Input("graph-region-ca", "clickData"),
     Input("reset-region", "n_clicks")],
    prevent_initial_call=True
)
def selectionner_region(clic, reset):
    triggered_id = ctx.triggered_id
    if triggered_id == "graph-region-ca" and clic and clic.get("points"):
        return clic["points"][0].get("y")  # Since Region is on the y-axis for horizontal bars
    return None

@app.callback(
    Output("lecture-metier", "children"),
    [Input("filtre-categorie", "value")]
)
def recommandation_metier(categorie):
    ventes = filtrer(categorie=categorie)
    if ventes.empty:
        return "Aucune vente — élagissez la plage ou changez la catégorie."
    
    par_region = ventes.groupby("Region")["Chiffre_Affaires"].sum()
    par_categorie = ventes.groupby("Categorie")["Marge"].sum()
    
    region_max = par_region.idxmax()
    cat_max = par_categorie.idxmax()
    
    return (
        f"Région au CA le plus élevé : {region_max}. "
        f"Catégorie à la marge totale la plus forte : {cat_max}. "
        "Analyse sur les filtres courants, pas en temps réel."
    )
if __name__ == "__main__":
    app.run(debug=True)