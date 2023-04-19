import json
import threading
from datetime import date
from typing import List
from aa_searcher import Aa_Searcher
from dl_searcher import Dl_Searcher
from nt_filter import AirBoundFilter, SearchEngineFilter, filter_airbounds, filter_prices, filter_search_engine
from nt_models import AirBound, PriceFilter, CabinClass
from nt_parser import results_to_dash_table, convert_ac_response_to_models, \
    convert_aa_response_to_models, convert_dl_response_to_models
from dash import Dash, dash_table, html, dcc, Output, State, Input, ctx
import dash_bootstrap_components as dbc
from ac_searcher import Ac_Searcher
from nt_sorter import get_default_sort_options, sort_airbounds
from utils import date_range


class DashApp:
    def __init__(self):
        self.dash_app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.dash_app.title = 'nt_tool'
        self.dash_app.layout = html.Div([
            html.Div([
                dbc.Stack([
                    html.Label('Origin_cities'),
                    dbc.Input(id='origins', type='text', value='LAX', placeholder='Origin IATA code'),
                ],direction="horizontal"),
                dbc.Stack([
                    html.Label('Destination_cities'),
                    dbc.Input(id='destinations', type='text', value='TYO',
                              placeholder='Destination IATA code, support comma separated multiple destinations')
                ],direction="horizontal")
            ]),
            dbc.Label('The system is to search EVERYDAY of the daterange you pick, only ONE-WAY.',
                      style={'color': 'Red', 'font-size': 20}),
            html.Div([
                dcc.DatePickerRange(id='dates',
                                    min_date_allowed=date.today(),
                                    initial_visible_month=date.today(),
                                    minimum_nights=0)
            ]),

            html.Div([dbc.Button('Search',
                                 id='search',
                                 n_clicks=0,
                                 style={'height': 35}
                                 )]),

            html.Div([
                dbc.Label('Sort by', html_for='sorter_type'),
                dcc.Dropdown(['Least stops', 'Shortest trip', 'Earliest departure time', 'Earliest arrival time'],
                             id='sorter_type')
            ]),
            html.Div([
                dbc.Label('Filters:', style={'display': 'inline-block', 'vertical-align': 'middle'}, html_for='filter'),
                dbc.Checklist(
                    ['ECO', 'PRE', 'BIZ', 'FIRST'],
                    ['ECO', 'PRE', 'BIZ', 'FIRST'],
                    id='cabin_class',
                    style={'color': 'Red', 'font-size': 20},
                    inline=True
                ),
                dbc.Checklist(
                    ['AA', 'AC', 'DL'],
                    ['AA', 'AC', 'DL'],
                    id='search_engine',
                    style={'color':'Green', 'font-size': 15},
                    inline=True
                ),
                dbc.Stack([
                    html.Label('Airline_Include'),
                    dbc.Input(id='airline_include', type='text', value='',
                              placeholder='Airline short code like AA,CA,NH'),
                ],
                    direction="horizontal"),
                dbc.Stack([
                    html.Label('Airline_Exclude'),
                    dbc.Input(id='airline_exclude', type='text', value='',
                              placeholder='Airline short code like AA,CA,NH'),
                ],
                    direction="horizontal"),
                html.Div([dbc.Button('Apply filters',
                                     id='apply_filters',
                                     n_clicks=0,
                                     style={'height': 35}
                                     )]),
                dcc.Store(id='filter_options')
            ]),
            dcc.Store(id='temp_data'),
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

        def run_thread(searcher, converter, origins, destinations, dates, airbounds):
            for ori in origins:
                for des in destinations:
                    for dt in dates:
                        response = searcher.search_for(ori, des, dt)
                        v1 = converter(response)
                        airbounds.extend(v1)

        @self.dash_app.callback(
            Output('search_data', 'data'),
            Input('search', 'n_clicks'),
            State('origins', 'value'),
            State('destinations', 'value'),
            State('dates', 'start_date'),
            State('dates', 'end_date'),
            prevent_initial_call=True
        )
        def search_results(n_clicks, origins, destinations, start_date, end_date):
            searchers = [Ac_Searcher(), Aa_Searcher(), Dl_Searcher()]
            converters = [convert_ac_response_to_models, convert_aa_response_to_models, convert_dl_response_to_models]
            if n_clicks == 0:
                return results_to_dash_table([])
            origins = [''.join(ori.split()) for ori in origins.split(',')]
            destinations = [''.join(des.split()) for des in destinations.split(',')]
            dates = date_range(start_date, end_date)
            airbounds: List[AirBound] = []
            threads = []
            for x in range(len(searchers)):
                thread = threading.Thread(target=run_thread, args=(
                    searchers[x], converters[x], origins, destinations, dates, airbounds))
                threads.append(thread)
                thread.start()
            for thread in threads:
                thread.join()
            return [x.json() for x in airbounds]

        @self.dash_app.callback(
            Output('temp_data', 'data'),
            State('search_data', 'data'),
            Input('filter_options', 'data'),
            prevent_initial_call=True, )
        def apply_filter(search_data, filter_options):
            airbound_filter = AirBoundFilter(
                max_stops=9,
                airline_include=filter_options['airline_include'].split(',')
                if filter_options['airline_include'] != '' else [],
                airline_exclude=filter_options['airline_exclude'].split(',')
                if filter_options['airline_exclude'] != '' else [],
            )
            
            search_engin_filter = SearchEngineFilter(
                search_engine = filter_options['search_engine']
            )

            price_filter = PriceFilter(
                min_quota=1,
                max_miles_per_person=999999,
                preferred_classes=[CabinClass[x] for x in filter_options['cabin_class']],
                mixed_cabin_accepted=True
            )
            airbounds = [AirBound.parse_raw(x) for x in search_data]
            airbounds = filter_airbounds(airbounds, airbound_filter)
            airbounds = filter_search_engine(airbounds, search_engin_filter)
            airbounds = filter_prices(airbounds, price_filter)
            return [x.json() for x in airbounds]

        @self.dash_app.callback(
            Output('datatable-interactivity', 'data'),
            Input('search_data', 'data'),
            Input('temp_data', 'data'),
            Input('sorter_type', 'value'),
            prevent_initial_call=True, )
        def update_table(search_data, temp_data, sorter_type):
            results = []
            triggered_id = ctx.triggered_id
            if triggered_id == 'search_data':
                airbounds = [AirBound.parse_raw(x) for x in search_data]
                for x in airbounds:
                    results.extend(x.to_flatted_list())
                return results_to_dash_table(results)
            if triggered_id == 'temp_data':
                airbounds = [AirBound.parse_raw(x) for x in temp_data]
                for x in airbounds:
                    results.extend(x.to_flatted_list())
                return results_to_dash_table(results)
            elif triggered_id == 'sorter_type':
                if temp_data is None:
                    return results_to_dash_table([])
                airbounds = [AirBound.parse_raw(x) for x in temp_data]
                sort_options = get_default_sort_options(sorter_type)
                airbounds = sort_airbounds(airbounds, sort_options)
                for x in airbounds:
                    results.extend(x.to_flatted_list())
                return results_to_dash_table(results)
            # elif triggered_id == 'filter_options':
            #     if temp_data is None:
            #         return results_to_dash_table([])
            #     airbound_filter = AirBoundFilter(
            #         max_stops=9,
            #         airline_include=filter_options['airline_include'].split(',')
            #         if filter_options['airline_include'] != '' else [],
            #         airline_exclude=filter_options['airline_exclude'].split(',')
            #         if filter_options['airline_exclude'] != '' else [],
            #     )
            #     price_filter = PriceFilter(
            #         min_quota=1,
            #         max_miles_per_person=999999,
            #         preferred_classes=[CabinClass[x] for x in filter_options['cabin_class']],
            #         mixed_cabin_accepted=True
            #     )
            #     airbounds = [AirBound.parse_raw(x) for x in temp_data]
            #     airbounds = filter_airbounds(airbounds, airbound_filter)
            #     airbounds = filter_prices(airbounds, price_filter)
            #     for x in airbounds:
            #         results.extend(x.to_flatted_list())
            #     return results_to_dash_table(results)

        @self.dash_app.callback(
            Output('filter_options', 'data'),
            Input('apply_filters', 'n_clicks'),
            State('cabin_class', 'value'),
            State('search_engine', 'value'),
            State('airline_include', 'value'),
            State('airline_exclude', 'value'),
            prevent_initial_call=True
        )
        def get_filter_options(n_clicks, cabin_class, search_engine, airline_include, airline_exclude):
            return {
                'cabin_class': cabin_class,
                'search_engine': search_engine,
                'airline_include': airline_include,
                'airline_exclude': airline_exclude
            }


if __name__ == '__main__':
    # WEB interface
    app = DashApp()
    app.dash_app.run(debug=False, host='0.0.0.0')
