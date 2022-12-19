
from plotly.offline import plot
import plotly.graph_objs as go

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
    SCATTER = 'scatter'
    BAR = 'bar'

    L_THESIS = 'thesis'
    L_REPLICA = 'replica'

    # SymbolValidator().values
    SYMBOL_LIST = ['cicle', 'square', 'star', 'diamond', 'cross',
                   'x', 'triangle-up', 'triangle-down',
                   'triangle-left', 'triangle-right']

    COLOR_LIST = [COLOR_bg_color, COLOR_morado, COLOR_bio_morado,
                  COLOR_violeta,
                  COLOR_red, COLOR_yellow, COLOR_green, COLOR_blue,
                  COLOR_bs_primary, COLOR_bs_success, COLOR_bs_info,
                  COLOR_bs_warning, COLOR_bs_danger,
                  COLOR_bs_green, COLOR_bs_secondary]

    def __init__(self, level,
                 trialAssessments, dataPoints):
        self._graphData = self.buildData(level,
                                         trialAssessments, dataPoints)

    def preparePlots(self, typeFigure='scatter', orientation='v'):
        graphPlots = [self.figure(
            item['x'], item['y'], title=item['title'],
            colors=item['colors'], symbols=item['symbols'],
            typeFigure=typeFigure, orientation=orientation,
            xaxis_title=item['x_axis'], yaxis_title=item['y_axis'])
                for item in self._graphData]
        return self.groupOnRows(graphPlots)

    def bar(self):
        return self.preparePlots(typeFigure=Graph.BAR, orientation='h')

    def scatter(self):
        return self.preparePlots(typeFigure=Graph.SCATTER)

    def figure(self, theX, theY,
               typeFigure=SCATTER, orientation='v',
               name=None, title=None,
               colors=[COLOR_morado], symbols=['cicle'],
               xaxis_title=None, yaxis_title=None):
        data = None
        if typeFigure == Graph.BAR:
            data = go.Bar(orientation=orientation,
                          name=name, x=theY, y=theX)
        elif typeFigure == Graph.SCATTER:
            data = go.Scatter(name=name, x=theX, y=theY,
                              marker={'color': colors, 'symbol': symbols},
                              mode='markers', marker_size=15)
        fig = go.Figure(data)
        # Update layout for graph object Figure
        fig.update_layout(
            paper_bgcolor="#333333",
            title_font_color="white",
            plot_bgcolor="#333333",
            font_color='white',
            title_text=title,
            xaxis_title=xaxis_title if orientation == 'v' else yaxis_title,
            yaxis_title=yaxis_title if orientation == 'v' else xaxis_title)

        # Turn graph object into local plotly graph
        plotly_plot_obj = plot({'data': fig}, output_type='div')
        return plotly_plot_obj

    def groupOnRows(self, graphs, columns=4):
        numGraphs = len(graphs)
        if numGraphs == 0:
            return [], 'col-md-12'
        classGroup = 'col-md-{}'.format(int(12 / (numGraphs % columns)))
        mgraphs = []
        count = 0
        rgraph = []
        for graph in graphs:
            if count == columns:
                count = 0
                mgraphs.append(rgraph)
                rgraph = []
            count += 1
            rgraph.append(graph)
        mgraphs.append(rgraph)
        return mgraphs, classGroup

    def buildData(self, level,
                  trialAssessments, dataPoints):
        # This is for diplay purposes. [[,],[,]...]
        # It has to follow the order of references
        # and then trial assessments
        graphs = []
        for unit in trialAssessments:
            thisGraph = {
                'title': unit.type.name,
                'x_axis': level,
                'y_axis': unit.unit.name}
            theX = []
            theY = []
            theSymbols = []
            theColors = []
            for dataPoint in dataPoints:
                if unit.id == dataPoint.unit.id:
                    xValue = None
                    symbol = 'star'
                    if level == Graph.L_THESIS:
                        xValue = dataPoint.reference.name
                        color = Graph.COLOR_LIST[
                            dataPoint.reference.number]
                    elif level == Graph.L_REPLICA:
                        symbol = Graph.SYMBOL_LIST[
                            dataPoint.reference.number]
                        color = Graph.COLOR_LIST[
                            dataPoint.reference.thesis.number]
                        xValue = dataPoint.reference.thesis.name
                    theX.append(xValue)
                    theY.append(dataPoint.value)
                    theColors.append(color)
                    theSymbols.append(symbol)
            thisGraph['x'] = theX
            thisGraph['y'] = theY
            thisGraph['symbols'] = theSymbols
            thisGraph['colors'] = theColors
            graphs.append(thisGraph)
        return graphs
