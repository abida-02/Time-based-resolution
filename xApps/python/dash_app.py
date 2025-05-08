import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import requests
import plotly.graph_objs as go

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='live-update-graph'),
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # in milliseconds
        n_intervals=0
    )
])

@app.callback(Output('live-update-graph', 'figure'),
              Input('interval-component', 'n_intervals'))
def update_graph_live(n):
    # Fetch data from the Flask backend
    response = requests.get("http://localhost:5000/get_prb_data")
    data = response.json()
    
    # Extract data for plotting
    times = [d['timestamp'] for d in data]
    prb_min_values = [d['prb_min'] for d in data]
    prb_max_values = [d['prb_max'] for d in data]
    
    # Create traces
    prb_min_trace = go.Scatter(
        x=times,
        y=prb_min_values,
        mode='lines+markers',
        name='PRB Min'
    )
    
    prb_max_trace = go.Scatter(
        x=times,
        y=prb_max_values,
        mode='lines+markers',
        name='PRB Max'
    )
    
    return {
        'data': [prb_min_trace, prb_max_trace],
        'layout': go.Layout(
            xaxis=dict(range=[min(times), max(times)]),
            yaxis=dict(range=[0, max(prb_max_values) + 1]),
            title='PRB Allocation Over Time'
        )
    }

if __name__ == '__main__':
    app.run_server(debug=True, port=8050)

