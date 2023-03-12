import json
from datetime import date
from typing import List

from aa_searcher import Aa_Searcher
from nt_models import AirBound
from nt_parser import results_to_dash_table, convert_ac_response_to_models, convert_nested_jsons_to_flatted_jsons, \
    convert_aa_response_to_models
from dash import Dash, dash_table, html, dcc, Output, State, Input, ctx
import dash_bootstrap_components as dbc

from ac_searcher import Ac_Searcher
from utils import date_range



class DashApp:
    def __init__(self):
        self.dash_app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.dash_app.title = 'nt_tool'
        self.dash_app.layout = html.Div([
            html.Div(
                [dbc.Input(id='origins', type='text', value='NYC,ORD', placeholder='Origin IATA code'),

                 dbc.Input(id='destinations', type='text', value='LHR,CDG',
                           placeholder='Destination IATA code, support comma separated multiple destinations')]
            ),
            html.Div([
                dbc.Checklist(
                    ['ECO', 'BIZ', 'FIRST'],
                    ['ECO', 'BIZ', 'FIRST'],
                    id='cabin_class',
                    style={'color': 'Red', 'font-size': 20},
                    inline=True
                )
            ]),

            html.Div([dcc.DatePickerRange(id='dates',
                                          min_date_allowed=date.today(),
                                          initial_visible_month=date.today(),
                                          minimum_nights=0)]),

            html.Div([dbc.Button('Search',
                                 id='search',
                                 n_clicks=0,
                                 style={'height': 35}
                                 )]),

            html.Div([
                dbc.Label('Sort by', html_for='filter_type'),
                dcc.Dropdown(['Least stops', 'Shortest trip', 'Earliest departure time', 'Earliest arrival time'],
                             id='filter_type')
            ]),
            dcc.Loading(
                id="loading-1",
                type="default",
                children=[dash_table.DataTable(id='datatable-interactivity',
                                               data=results_to_dash_table([]),
                                               style_data={
                                                   'whiteSpace': 'pre-line',
                                                   'height': 'auto',
                                               },
                                               # editable=True,
                                               # filter_action="native",
                                               # sort_action="native",
                                               # TODO server end sort needed for some columns e.g., price and duration
                                               ),
                          dcc.Store(id='search_data')]
            ),

            html.Div([
                html.A('NT-tool is powered by an opensource library',
                       href='https://github.com/xmsley614/nt_tool',
                       target="_blank")
            ]),

        ],

        )
        self.data = []

        @self.dash_app.callback(
            Output('search_data', 'data'),
            Input('search', 'n_clicks'),
            State('origins', 'value'),
            State('destinations', 'value'),
            State('cabin_class', 'value'),
            State('dates', 'start_date'),
            State('dates', 'end_date'),
            prevent_initial_call=True
        )
        def search_results(n_clicks, origins, destinations, cabin_class, start_date, end_date):
            searchers = [Ac_Searcher(), Aa_Searcher()]
            converters = [convert_ac_response_to_models, convert_aa_response_to_models]
            if n_clicks == 0:
                return results_to_dash_table([])
            origins = [''.join(ori.split()) for ori in origins.split(',')]
            destinations = [''.join(des.split()) for des in destinations.split(',')]
            dates = date_range(start_date, end_date)
            airbounds:List[AirBound] = []
            for x in range(2):
                for ori in origins:
                    for des in destinations:
                        for dt in dates:
                            response = searchers[x].search_for(ori, des, dt, cabin_class)
                            v1 = converters[x](response)
                            airbounds.extend(v1)
            return [x.json() for x in airbounds]

        @self.dash_app.callback(
            Output('datatable-interactivity', 'data'),
            Input('search_data', 'data'),
            Input('filter_type', 'value'),
            prevent_initial_call=True, )
        def update_table(search_data, filter_type):
            results = []
            triggered_id = ctx.triggered_id
            if triggered_id == 'search_data':
                airbounds = [AirBound.parse_raw(x) for x in search_data]
                for x in airbounds:
                    results.extend(x.to_flatted_list())
                return results_to_dash_table(results)
            elif triggered_id == 'filter_type':
                pass
                # if search_data is None:
                #     return results_to_dash_table([])
                # nested_jsons_list = json.loads(search_data)
                # return self.apply_sort(nested_jsons_list, filter_type)

    # def apply_sort(self, origin_results, filter_type):
    #     if filter_type == 'Least stops':
    #         seg_sorter = {
    #             'key': 'stops',  # only takes 'duration_in_all', 'stops', 'departure_time' and 'arrival_time'.
    #             'ascending': True
    #         }
    #     elif filter_type == 'Earliest departure time':
    #         seg_sorter = {
    #             'key': 'departure_time',  # only takes 'duration_in_all', 'stops', 'departure_time' and 'arrival_time'.
    #             'ascending': True
    #         }
    #     elif filter_type == 'Shortest trip':
    #         seg_sorter = {
    #             'key': 'duration_in_all',
    #             # only takes 'duration_in_all', 'stops', 'departure_time' and 'arrival_time'.
    #             'ascending': True
    #         }
    #     elif filter_type == 'Earliest arrival time':
    #         seg_sorter = {
    #             'key': 'arrival_time',
    #             # only takes 'duration_in_all', 'stops', 'departure_time' and 'arrival_time'.
    #             'ascending': True
    #         }
    #     else:
    #         seg_sorter = {}
    #     v2 = convert_nested_jsons_to_flatted_jsons(origin_results=origin_results, seg_sorter=seg_sorter)
    #     return results_to_dash_table(v2)


if __name__ == '__main__':
    # WEB interface
    app = DashApp()
    app.dash_app.run(debug=True)
