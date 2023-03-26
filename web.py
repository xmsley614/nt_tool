from datetime import date

from nt_parser import results_to_dash_table, convert_ac_response_to_models, convert_nested_jsons_to_flatted_jsons
from dash import Dash, dash_table, html, dcc, Output, State, Input

from searcher import Ac_Searcher
from utils import date_range


class DashApp:
    def __init__(self):
        self.dash_app = Dash(__name__)
        self.dash_app.title = '瓜哥的秘密花园'
        self.dash_app.layout = html.Div([
            dcc.Input(id='origins', type='text', value='BOS,NYC', placeholder='Origin IATA code'),

            dcc.Input(id='destinations', type='text', value='HKG,PVG',
                      placeholder='Destination IATA code, support comma separated multiple destinations'),
            dcc.DatePickerRange(id='dates',
                                min_date_allowed=date.today(),
                                initial_visible_month=date.today(),
                                minimum_nights=0),
            html.Button('Search', id='search', n_clicks=0),
            dash_table.DataTable(id='datatable-interactivity',
                                 data=results_to_dash_table([]),
                                 style_data={
                                     'whiteSpace': 'pre-line',
                                     'height': 'auto',
                                 },
                                 editable=True,
                                 sort_action="native",
                                 # TODO server end sort needed for some columns e.g., price and duration
                                 )
        ])
        self.dash_app.callback(Output('datatable-interactivity', 'data'),
                               Input('search', 'n_clicks'),
                               State('origins', 'value'),
                               State('destinations', 'value'),
                               State('dates', 'start_date'),
                               State('dates', 'end_date'),
                               prevent_initial_call=True, )(self.update_table)

    def update_table(self, n_clicks, origins, destinations, start_date, end_date):
        sc = Ac_Searcher()
        if n_clicks == 0:
            return results_to_dash_table([])
        origins = [''.join(ori.split()) for ori in origins.split(',')]
        destinations = [''.join(des.split()) for des in destinations.split(',')]
        dates = date_range(start_date, end_date)
        results = []
        nested_jsons_list = []
        for ori in origins:
            for des in destinations:
                for date in dates:
                    response = sc.search_for(ori, des, date)
                    v1 = convert_ac_response_to_models(response)
                    nested_jsons_list.extend(v1)
        v2 = convert_nested_jsons_to_flatted_jsons(nested_jsons_list)
        results.extend(v2)
        return results_to_dash_table(results)


if __name__ == '__main__':
    # WEB interface
    app = DashApp()
    app.dash_app.run(debug=True)
