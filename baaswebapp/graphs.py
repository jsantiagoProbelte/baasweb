
from plotly.offline import plot
import plotly.graph_objs as go
# from plotly.validators.scatter.marker import SymbolValidator

COLOR_main_color = '#a500a5'
COLOR_red = '#ff6e73'
COLOR_yellow = '#ffd26e'
COLOR_green = '#92eeb9'
COLOR_blue = '#00bdeb'
COLOR_grey = '#F0EEEB'
COLOR_black = '#333333'
COLOR_bio_morado = '#aa4ae4'
COLOR_morado = '#a500a5'
COLOR_violeta = '#cfc9ff'
COLOR_bs_blue = '#325d88'
COLOR_bs_indigo = '#6610f2'
COLOR_bs_purple = '#6f42c1'
COLOR_bs_pink = '#e83e8c'
COLOR_bs_red = '#d9534f'
COLOR_bs_orange = '#f47c3c'
COLOR_bs_yellow = '#ffc107'
COLOR_bs_green = '#93c54b'
COLOR_bs_teal = '#20c997'
COLOR_bs_cyan = '#2997FF'
COLOR_bs_white = '#fff'
COLOR_bs_gray = '#8e8c84'
COLOR_bs_gray_dark = '#3e3f3a'
COLOR_bs_primary = '#325d88'
COLOR_bs_secondary = '#8e8c84'
COLOR_bs_success = '#93c54b'
COLOR_bs_info = '#29abe0'
COLOR_bs_warning = '#f47c3c'
COLOR_bs_danger = '#d9534f'
COLOR_bs_light = '#f8f5f0'
COLOR_bs_dark = '#3e3f3a'
COLOR_bs_text_color = '#f4f4f4'
COLOR_bs_text_color_table = '#fff'
COLOR_bg_color = '#282828'
COLOR_bg_color_cards = '#333333'


class Graph:
    _graphData = []
    _level = None
    SCATTER = 'scatter'
    BAR = 'bar'
    VIOLIN = 'violin'

    L_THESIS = 'thesis'
    L_REPLICA = 'replica'
    L_SAMPLE = 'sample'
    L_DATE = 'date'

    # SYMBOL_LIST = SymbolValidator().values
    SYMBOL_LIST = ['cicle', 'square', 'star', 'diamond', 'cross',
                   'x', 'triangle-up', 'triangle-down',
                   'triangle-left', 'triangle-right', 'hexagram',
                   'star-triangle-up', 'star-triangle-down',
                   'diamond-tall', 'diamond-wide', 'square-cross',
                   'circle-cross', 'circle-x', 'asterisk', 'hash']

    COLOR_LIST = [COLOR_bg_color, COLOR_morado, COLOR_bio_morado,
                  COLOR_violeta,
                  COLOR_red, COLOR_yellow, COLOR_green, COLOR_blue,
                  COLOR_bs_primary, COLOR_bs_success, COLOR_bs_info,
                  COLOR_bs_warning, COLOR_bs_danger,
                  COLOR_bs_green, COLOR_bs_secondary]

    def __init__(self, level, trialAssessments,
                 dataPoints, xAxis=L_THESIS):
        self._level = level
        self._graphData = self.buildData(trialAssessments,
                                         dataPoints, xAxis=xAxis)

    def preparePlots(self, typeFigure='scatter', orientation='v'):
        graphPlots = [self.figure(item, typeFigure=typeFigure,
                                  orientation=orientation)
                      for item in self._graphData]
        return self.groupOnRows(graphPlots)

    def bar(self):
        return self.preparePlots(typeFigure=Graph.BAR, orientation='h')

    def scatter(self):
        return self.preparePlots(typeFigure=Graph.SCATTER)

    def violin(self):
        return self.preparePlots(typeFigure=Graph.VIOLIN)

    def adaptative(self, variants, threshold=3):
        if variants > threshold:
            return self.violin()
        else:
            return self.scatter()

    def figure(self, thisGraph,
               typeFigure=SCATTER, orientation='v'):
        data = None
        fig = go.Figure()

        for traceKey in thisGraph['traces']:
            trace = thisGraph['traces'][traceKey]
            name = trace['name']
            color = trace['marker_color']
            symbol = trace['marker_symbol']
            x = trace['x']
            y = trace['y']

            if typeFigure == Graph.BAR:
                data = go.Bar(orientation=orientation,
                              name=name, marker={'color': color},
                              x=x, y=y)
            elif typeFigure == Graph.SCATTER:
                data = go.Scatter(name=name, x=x, y=y,
                                  marker={'color': color, 'symbol': symbol},
                                  mode='markers', marker_size=15)
            elif typeFigure == Graph.VIOLIN:
                data = go.Violin(name=name, x=x, y=y,
                                 box_visible=True,
                                 meanline_visible=True,
                                 line_color=color)
            fig.add_trace(data)

        # Update layout for graph object Figure
        if orientation == 'v':
            xaxis_title = thisGraph['x_axis']
            yaxis_title = thisGraph['y_axis']
        else:
            xaxis_title = thisGraph['y_axis']
            yaxis_title = thisGraph['x_axis']

        fig.update_layout(
            paper_bgcolor=COLOR_bg_color_cards,
            title_font_color="white",
            plot_bgcolor=COLOR_bg_color_cards,
            font_color='white',
            title_text=thisGraph['title'],
            showlegend=True,
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title)

        if typeFigure == Graph.VIOLIN:
            fig.update_layout(violinmode='group')

        # Turn graph object into local plotly graph
        plotly_plot_obj = plot({'data': fig}, output_type='div')
        return plotly_plot_obj

    def groupOnRows(self, graphs, columns=4):
        numGraphs = len(graphs)
        if numGraphs == 0:
            return [], 'hide'
        rcolumns = columns
        if numGraphs < columns:
            rcolumns = numGraphs
        classGroup = 'col-md-{}'.format(int(12 / rcolumns))
        mgraphs = []
        count = 0
        rgraph = []
        for graph in graphs:
            if count == rcolumns:
                count = 0
                mgraphs.append(rgraph)
                rgraph = []
            count += 1
            rgraph.append(graph)
        mgraphs.append(rgraph)
        return mgraphs, classGroup

    def traceId(self, dataPoint):
        if self._level == Graph.L_THESIS:
            return dataPoint.reference.number
        elif self._level == Graph.L_REPLICA:
            return dataPoint.reference.thesis.number
        elif self._level == Graph.L_SAMPLE:
            return dataPoint.reference.replica.number

    def getTraceName(self, dataPoint):
        if self._level == Graph.L_THESIS:
            return dataPoint.reference.name
        elif self._level == Graph.L_REPLICA:
            return dataPoint.reference.thesis.name
        elif self._level == Graph.L_SAMPLE:
            return dataPoint.reference.replica.thesis.name

    def getTraceColor(self, dataPoint):
        color = 1
        if self._level == Graph.L_THESIS:
            color = dataPoint.reference.number
        elif self._level == Graph.L_REPLICA:
            color = dataPoint.reference.thesis.number
        elif self._level == Graph.L_SAMPLE:
            color = dataPoint.reference.replica.thesis.number
        return Graph.COLOR_LIST[color]

    def getTraceSymbol(self, dataPoint):
        symbol = 2
        if self._level == Graph.L_REPLICA:
            symbol = dataPoint.reference.number
        elif self._level == Graph.L_SAMPLE:
            symbol = dataPoint.reference.replica.number
        return Graph.SYMBOL_LIST[symbol]

    def prepareTrace(self, dataPoint):
        return {
            'name': self.getTraceName(dataPoint),
            'marker_color': self.getTraceColor(dataPoint),
            'marker_symbol': self.getTraceSymbol(dataPoint),
            'x': [],
            'y': []
        }

    def getX(self, dataPoint, xAxis):
        if xAxis == Graph.L_THESIS:
            return self.getTraceName(dataPoint)
        if xAxis == Graph.L_DATE:
            return dataPoint.evaluation.evaluation_date

    def buildData(self, trialAssessments,
                  dataPoints, xAxis=L_THESIS):
        # This is for diplay purposes. [[,],[,]...]
        # It has to follow the order of references
        # and then trial assessments
        graphs = []
        if dataPoints is None or len(dataPoints) == 0:
            return []
        for unit in trialAssessments:
            thisGraph = {
                'title': unit.type.name,
                'x_axis': xAxis,
                'y_axis': unit.unit.name,
                'traces': []}
            traces = {}
            for dataPoint in dataPoints:
                if unit.id == dataPoint.unit.id:
                    traceId = self.traceId(dataPoint)
                    if traceId not in traces:
                        traces[traceId] = self.prepareTrace(dataPoint)
                    traces[traceId]['y'].append(dataPoint.value)
                    traces[traceId]['x'].append(self.getX(
                        dataPoint, xAxis))
            if len(traces) > 0:
                thisGraph['traces'] = traces
                graphs.append(thisGraph)
        return graphs
