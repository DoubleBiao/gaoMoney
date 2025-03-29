from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from models import db, StockScan, MarketStatus
import pandas as pd

# Initialize the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Stock Market Monitor Dashboard", className="text-center my-4"), width=12)
    ]),
    
    # Market Status Card
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Market Status"),
                dbc.CardBody(id="market-status-content")
            ])
        ], width=12)
    ], className="mb-4"),
    
    # Filters
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Filters"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Date Range"),
                            dcc.DatePickerRange(
                                id='date-range',
                                start_date=datetime.now() - timedelta(days=7),
                                end_date=datetime.now()
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label("Minimum Volume Ratio"),
                            dcc.Slider(
                                id='volume-ratio-slider',
                                min=1,
                                max=5,
                                step=0.5,
                                value=2,
                                marks={i: str(i) for i in range(1, 6)}
                            )
                        ], width=6)
                    ])
                ])
            ])
        ], width=12)
    ], className="mb-4"),
    
    # Stock Table
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Stocks of Interest"),
                dbc.CardBody([
                    html.Div(id="stock-table")
                ])
            ])
        ], width=12)
    ], className="mb-4"),
    
    # Volume Analysis Chart
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Volume Analysis"),
                dbc.CardBody([
                    dcc.Graph(id="volume-chart")
                ])
            ])
        ], width=12)
    ]),
    
    # Hidden div for interval
    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # 30 seconds in milliseconds
        n_intervals=0
    )
], fluid=True)

@app.callback(
    Output("market-status-content", "children"),
    [Input("date-range", "start_date"),
     Input("date-range", "end_date"),
     Input("interval-component", "n_intervals")]
)
def update_market_status(start_date, end_date, n):
    latest_status = MarketStatus.query.order_by(MarketStatus.date.desc()).first()
    if latest_status:
        status_dict = latest_status.to_dict()
        return html.Div([
            html.H4(f"Status: {'Open' if status_dict['is_open'] else 'Closed'}"),
            html.P(f"Last Updated: {status_dict['date']}"),
            html.P(f"Next Open: {status_dict['next_open_date'] or 'N/A'}"),
            html.P(status_dict['message'])
        ])
    return "No market status data available"

@app.callback(
    Output("stock-table", "children"),
    [Input("date-range", "start_date"),
     Input("date-range", "end_date"),
     Input("volume-ratio-slider", "value"),
     Input("interval-component", "n_intervals")]
)
def update_stock_table(start_date, end_date, volume_ratio, n):
    if not start_date or not end_date:
        return "Please select a date range"
    
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    stocks = StockScan.query.filter(
        StockScan.date.between(start_date, end_date),
        StockScan.volume_ratio >= volume_ratio
    ).order_by(StockScan.date.desc()).all()
    
    if not stocks:
        return "No stocks found for the selected criteria"
    
    df = pd.DataFrame([stock.to_dict() for stock in stocks])
    
    return dbc.Table.from_dataframe(
        df,
        striped=True,
        bordered=True,
        hover=True,
        responsive=True
    )

@app.callback(
    Output("volume-chart", "figure"),
    [Input("date-range", "start_date"),
     Input("date-range", "end_date"),
     Input("interval-component", "n_intervals")]
)
def update_volume_chart(start_date, end_date, n):
    if not start_date or not end_date:
        return {}
    
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    stocks = StockScan.query.filter(
        StockScan.date.between(start_date, end_date)
    ).all()
    
    if not stocks:
        return {}
    
    df = pd.DataFrame([stock.to_dict() for stock in stocks])
    
    fig = px.scatter(
        df,
        x='date',
        y='volume_ratio',
        color='symbol',
        title='Volume Ratio Over Time',
        labels={'volume_ratio': 'Volume Ratio', 'date': 'Date'}
    )
    
    return fig

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050) 