import time
from datetime import datetime
from parser import convert_response, results_to_excel, results_to_dash_table
from searcher import Searcher
from web import DashApp

if __name__ == '__main__':

    app = DashApp()
    app.dash_app.run(debug=True)