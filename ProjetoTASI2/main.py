import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px

# Caminho do arquivo CSV (ajustar se necessário)
caminho_arquivo = './Steam_2024_bestRevenue_1500.csv'

# Carregar os dados
df = pd.read_csv(caminho_arquivo)

# Converter a coluna 'releaseDate' para datetime com o formato correto
df['releaseDate'] = pd.to_datetime(df['releaseDate'], format='%d-%m-%Y', errors='coerce')

# Criar uma nova coluna para o tamanho das bolhas (cópias vendidas)
df['bubble_size'] = df['copiesSold'].apply(lambda x: min(x, 5000000))  # Limitar a 5M
df['bubble_size'] = df['bubble_size'].apply(lambda x: 100 if x >= 5000000 else (x / 5000000) * 100)  # Ajustando tamanho fixo para bolhas maiores

# Filtrando bolhas com tamanho menor que 1
df = df[df['bubble_size'] >= 1]

# Extrair o mês e o ano da data de lançamento como string
df['releaseMonth'] = df['releaseDate'].dt.strftime('%Y-%m')

# Contagem dos jogos por desenvolvedor
contagem_desenvolvedores = df['developers'].value_counts().reset_index()
contagem_desenvolvedores.columns = ['developers', 'num_jogos']
top_10_desenvolvedores = contagem_desenvolvedores.nlargest(10, 'num_jogos')['developers']
df_top_10 = df[df['developers'].isin(top_10_desenvolvedores)]

# Inicializando a aplicação Dash com Bootstrap
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout do Dashboard com cabeçalho, rodapé e cor de fundo
app.layout = dbc.Container([
    # Cabeçalho
    dbc.Row([
        dbc.Col(html.H1("Dashboard de Jogos da Steam", className="text-center text-light bg-primary py-3"), width=12)
    ], className="mb-4"),

    # Corpo principal
    dbc.Row([
        # Filtro
        dbc.Col([
            html.Label("Filtrar por Classe de Publisher:"),
            dcc.Dropdown(
                id='publisher-class-filter',
                options=[{'label': publisher, 'value': publisher} for publisher in df['publisherClass'].unique()],
                multi=True,
                value=df['publisherClass'].unique().tolist(),
                placeholder="Selecione a Classe de Publisher",
            )
        ], width=6, className="mb-4"),

        # Gráfico de bolhas
        dbc.Col(dcc.Graph(id='review-score-bubble'), width=12, className="mb-4"),

        # Gráficos principais
        dbc.Col(dcc.Graph(id='avg-price-by-month'), width=6, className="mb-4"),
        dbc.Col(dcc.Graph(id='copies-sold-by-month'), width=6, className="mb-4"),

        # Gráfico de cópias vs preço
        dbc.Col(dcc.Graph(id='copies-vs-price'), width=12, className="mb-4"),

        # Gráficos adicionais
        dbc.Col(dcc.Graph(id='boxplot-review-score'), width=6, className="mb-4"),
        dbc.Col(dcc.Graph(id='developer-review-score'), width=6, className="mb-4"),
    ]),

    # Rodapé
    dbc.Row([
        dbc.Col(html.Footer("© 2024 Steam Dashboard.", 
                            className="text-center text-light bg-secondary py-2"), width=12)
    ])
], fluid=True, style={"backgroundColor": "#f8f9fa", "padding": "20px"})

# Callback para atualizar os gráficos
@app.callback(
    Output('review-score-bubble', 'figure'),
    Output('avg-price-by-month', 'figure'),
    Output('copies-sold-by-month', 'figure'),
    Output('copies-vs-price', 'figure'),
    Output('boxplot-review-score', 'figure'),
    Output('developer-review-score', 'figure'),
    Input('publisher-class-filter', 'value'),
)
def update_graphs(selected_publishers):
    # Filtrar os dados com base no seletor de Publisher Class
    filtered_df = df[df['publisherClass'].isin(selected_publishers)]

    # Gráficos
    bubble_fig = px.scatter(filtered_df, x='releaseDate', y='reviewScore', color='publisherClass', size='bubble_size',
                            hover_data=['name'], title='Pontuação de Avaliação por Classe de Publisher (Gráfico de Bolhas)')
    bubble_fig.update_layout(xaxis_title='Data de Lançamento', yaxis_title='Pontuação de Avaliação', plot_bgcolor='#f5f5f5')

    price_fig = px.line(filtered_df.groupby(['releaseMonth', 'publisherClass'], as_index=False)['price'].mean(),
                        x='releaseMonth', y='price', color='publisherClass', title='Preço Médio dos Jogos por Mês')
    price_fig.update_layout(xaxis_title='Mês de Lançamento', yaxis_title='Preço Médio', plot_bgcolor='#f5f5f5')

    copies_fig = px.line(filtered_df.groupby([pd.Grouper(key='releaseDate', freq='M'), 'publisherClass'])['copiesSold'].sum().reset_index(),
                         x='releaseDate', y='copiesSold', color='publisherClass', title='Cópias Vendidas por Mês')
    copies_fig.update_layout(xaxis_title='Data de Lançamento', yaxis_title='Cópias Vendidas', plot_bgcolor='#f5f5f5')

    # Gráfico de cópias vs preço
    copies_vs_price_fig = px.scatter(
        filtered_df,
        x="copiesSold",
        y="price",
        color='publisherClass',
        hover_data=['name'],  # Adiciona o nome dos jogos no hover
        title='Cópias Vendidas por Preço'
    )
    copies_vs_price_fig.update_layout(
        xaxis=dict(type='log', title='Cópias Vendidas'),
        yaxis=dict(type='log', title='Preço'),
        margin=dict(l=40, r=40, t=40, b=40),
        plot_bgcolor='#f5f5f5'
    )

    boxplot_fig = px.box(filtered_df, x='publisherClass', y='reviewScore', color='publisherClass', 
                         title='Distribuição da Pontuação de Avaliação por Classe de Publicação')
    boxplot_fig.update_layout(xaxis_title='Classe de Publicação', yaxis_title='Pontuação de Avaliação', plot_bgcolor='#f5f5f5')

    # Substituir o gráfico final por um stripchart
    dev_review_score_fig = px.strip(filtered_df, x='reviewScore', y='publisherClass', color='publisherClass',
                                    title='Stripchart: Pontuação de Avaliação por Classe de Publicação', hover_data=['name'])
    dev_review_score_fig.update_layout(xaxis_title='Pontuação de Avaliação', yaxis_title='Classe de Publicação', plot_bgcolor='#f5f5f5')

    return bubble_fig, price_fig, copies_fig, copies_vs_price_fig, boxplot_fig, dev_review_score_fig

# Rodar a aplicação
if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)
