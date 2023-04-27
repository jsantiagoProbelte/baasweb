
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

ALL_COLORS = [COLOR_main_color, COLOR_red, COLOR_yellow, COLOR_green,
              COLOR_blue, COLOR_grey, COLOR_black, COLOR_bio_morado,
              COLOR_morado,
              COLOR_violeta, COLOR_bs_blue, COLOR_bs_indigo, COLOR_bs_purple,
              COLOR_bs_pink, COLOR_bs_red,  COLOR_bs_orange, COLOR_bs_yellow,
              COLOR_bs_green, COLOR_bs_teal, COLOR_bs_cyan, COLOR_bs_white,
              COLOR_bs_gray, COLOR_bs_gray_dark, COLOR_bs_primary,
              COLOR_bs_secondary, COLOR_bs_success, COLOR_bs_info,
              COLOR_bs_warning, COLOR_bs_danger, COLOR_bs_light,
              COLOR_bs_dark, COLOR_bs_text_color, COLOR_bg_color]


class GraphTrial:
    _graphData = []
    _level = None
    _xAxis = None
    SCATTER = 'scatter'
    BAR = 'bar'
    VIOLIN = 'violin'
    LINE = 'line'
    _colors = {}

    L_THESIS = 'thesis'
    L_REPLICA = 'replica'
    L_SAMPLE = 'sample'
    L_DATE = 'date'
    L_DAF = 'daf'
    L_DOSIS = 'dosis'
    LEVELS = [L_THESIS, L_REPLICA, L_SAMPLE]

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

    def __init__(self, level, rateType, ratedPart,
                 dataPoints, xAxis=L_DATE,
                 showTitle=True, trialCode=None,
                 useCode=False, combineTrialAssessments=False):
        self._level = level
        self._xAxis = xAxis
        self._showTitle = showTitle
        self._title = self.getTitle(rateType, ratedPart)
        self._yAxis = rateType.unit
        self._trialCode = trialCode
        self._useCode = useCode
        self._combineTrialAssessments = combineTrialAssessments
        self._graphData = self.buildData(dataPoints)
        self._colors = {}

    def preparePlots(self, typeFigure='scatter', orientation='v'):
        return self.figure(self._graphData, typeFigure=typeFigure,
                           orientation=orientation)

    def bar(self):
        return self.preparePlots(typeFigure=GraphTrial.BAR, orientation='h')

    def scatter(self):
        return self.preparePlots(typeFigure=GraphTrial.SCATTER)

    def violin(self):
        return self.preparePlots(typeFigure=GraphTrial.VIOLIN)

    def line(self):
        return self.preparePlots(typeFigure=GraphTrial.LINE)

    def draw(self):
        if self._level == GraphTrial.L_DOSIS:
            return self.line()
        elif self._level == GraphTrial.L_THESIS:
            if self._combineTrialAssessments:
                return self.scatter()
            else:
                return self.bar()
        else:
            return self.violin()

    def figure(self, thisGraph,
               typeFigure=SCATTER, orientation='v'):
        showLegend = True
        data = None
        fig = go.Figure()

        for traceKey in thisGraph['traces']:
            trace = thisGraph['traces'][traceKey]
            name = trace['name']
            color = trace['marker_color']
            symbol = trace['marker_symbol']
            if orientation == 'v':
                x = trace['x']
                y = trace['y']
            else:
                x = trace['y']
                y = trace['x']

            if typeFigure == GraphTrial.BAR:
                showLegend = False
                data = go.Bar(orientation=orientation,
                              name=name, marker={'color': color},
                              x=x, y=y)
            elif typeFigure == GraphTrial.LINE:
                markerMode = 'lines+markers'
                data = go.Scatter(name=name, x=x, y=y,
                                  marker={'color': color, 'symbol': symbol},
                                  mode=markerMode, marker_size=5)
            elif typeFigure == GraphTrial.SCATTER:
                if self._xAxis == GraphTrial.L_DATE:
                    markerMode = 'lines+markers'
                else:
                    markerMode = 'markers'
                data = go.Scatter(name=name, x=x, y=y,
                                  marker={'color': color, 'symbol': symbol},
                                  mode=markerMode, marker_size=15)
            elif typeFigure == GraphTrial.VIOLIN:
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
            title_text=thisGraph['title'] if self._showTitle else '',
            showlegend=showLegend,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-1,
                xanchor="left",
                x=0),
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title)

        if typeFigure == GraphTrial.VIOLIN:
            fig.update_layout(violinmode='group')

        # Turn graph object into local plotly graph
        plotly_plot_obj = plot({'data': fig}, output_type='div')
        return plotly_plot_obj

    @classmethod
    def classColGraphs(cls, rcolumns, max_columns):
        rcolumns = 1 if rcolumns == 0 else rcolumns
        columns = max_columns if max_columns < rcolumns else rcolumns
        return 'col-md-{}'.format(int(12 / columns))

    def traceIdLevel(self, dataPoint):
        if self._level == GraphTrial.L_THESIS:
            return dataPoint.reference.number
        elif self._level == GraphTrial.L_REPLICA:
            return dataPoint.reference.thesis.number
        elif self._level == GraphTrial.L_SAMPLE:
            return dataPoint.reference.replica.number
        elif self._level == GraphTrial.L_DOSIS:
            return dataPoint.thesis.name

    def traceId(self, dataPoint):
        theId = '{}'.format(self.traceIdLevel(dataPoint))
        if self._combineTrialAssessments:
            unitId = dataPoint.assessment.rate_type.id
            theId += '-{}'.format(unitId)
        return theId

    def getTraceNameLevel(self, dataPoint):
        if self._level == GraphTrial.L_THESIS:
            return dataPoint.reference.name
        elif self._level == GraphTrial.L_REPLICA:
            return dataPoint.reference.thesis.name
        elif self._level == GraphTrial.L_SAMPLE:
            return dataPoint.reference.replica.thesis.name
        elif self._level == GraphTrial.L_DOSIS:
            return dataPoint.thesis.name

    def getTraceName(self, dataPoint, code):
        theName = self.getTraceNameLevel(dataPoint)
        if self._combineTrialAssessments:
            theName += '-{}'.format(code)
        return theName

    def getTraceColor(self, dataPoint):
        color = 1
        if self._level == GraphTrial.L_THESIS:
            color = dataPoint.reference.number
        elif self._level == GraphTrial.L_REPLICA:
            color = dataPoint.reference.thesis.number
        elif self._level == GraphTrial.L_SAMPLE:
            color = dataPoint.reference.replica.thesis.number
        elif self._level == GraphTrial.L_DOSIS:
            color = self._colors[dataPoint.thesis.name]
        return GraphTrial.COLOR_LIST[color]

    def getTraceSymbol(self, dataPoint):
        symbol = 2
        if self._level == GraphTrial.L_REPLICA:
            symbol = dataPoint.reference.number
        elif self._level == GraphTrial.L_SAMPLE:
            symbol = dataPoint.reference.replica.number
        elif self._level == GraphTrial.L_DOSIS:
            symbol = self._colors[dataPoint.thesis.name]
        return GraphTrial.SYMBOL_LIST[symbol]

    def prepareTrace(self, dataPoint, code):
        return {
            'name': self.getTraceName(dataPoint, code),
            'marker_color': self.getTraceColor(dataPoint),
            'marker_symbol': self.getTraceSymbol(dataPoint),
            'x': [],
            'y': []}

    def getX(self, dataPoint, xAxis, code):
        if xAxis == GraphTrial.L_THESIS:
            return self.getTraceName(dataPoint, code)
        if xAxis == GraphTrial.L_DATE:
            return dataPoint.assessment.assessment_date
        if xAxis == GraphTrial.L_DAF:
            return dataPoint.assessment.daf
        if xAxis == GraphTrial.L_DOSIS:
            return dataPoint.dosis.rate

    def getTitle(self, rateType, ratedPart):
        return '{}({}) {}'.format(rateType.name, rateType.unit, ratedPart)

    def getCode(self, dataPoint):
        if self._useCode:
            if not self._trialCode:
                return dataPoint.assessment.field_trial.code
            else:
                return self._trialCode
        else:
            return None

    def assignColor(self, traceId):
        if self._level == GraphTrial.L_DOSIS:
            if traceId not in self._colors:
                number = len(list(self._colors.keys()))
                self._colors[traceId] = number + 1

    def buildData(self, dataPoints):
        # This is for diplay purposes. [[,],[,]...]
        # It has to follow the order of references
        # and then trial assessments
        if dataPoints is None or len(dataPoints) == 0:
            return None
        traces = {}
        for dataPoint in dataPoints:
            # TODO: there could be data with different units
            code = self.getCode(dataPoint)
            traceId = self.traceId(dataPoint)
            self.assignColor(traceId)
            if traceId not in traces:
                traces[traceId] = self.prepareTrace(dataPoint, code)
            traces[traceId]['y'].append(dataPoint.value)
            traces[traceId]['x'].append(
                self.getX(dataPoint, self._xAxis, code))
        if len(traces) > 0:
            return {
                'title': self._title,
                'x_axis': self._xAxis,
                'y_axis': self._yAxis,
                'traces': traces}
        return None


class GraphStat():
    def __init__(self, rawDataDict, labels, showLegend=True,
                 title=None, showTitle=False,
                 xAxis='month', yAxis='# trials', orientation='v'):
        self._graphData = None
        self._title = title
        self._orientation = orientation
        self._labels = labels
        self._rawDataDict = rawDataDict
        self._xAxis = xAxis
        self._yAxis = yAxis
        self._showTitle = showTitle
        self._showLegend = showLegend

    def plot(self):
        self.prepareData()
        return self.figure()

    def prepareColors(self, theList):
        statColors = {}
        lenColors = len(ALL_COLORS)
        for index in range(0, len(theList)):
            position = index % lenColors
            statColors[theList[index]] = ALL_COLORS[position]
        return statColors

    def prepareData(self):
        statColors = {}
        colorPerLabel = False
        if len(self._rawDataDict) > 1:
            # use datasetKeys for colors
            colorPerLabel = False
            datasetKeys = list(self._rawDataDict.keys())
            statColors = self.prepareColors(datasetKeys)
        else:
            # use labels for colors
            colorPerLabel = True
            # assume same order from labels in totals and months datasetkeys
            # since it is the same dimension, so the colors on boths grpahs
            # should match.
            statColors = list(self.prepareColors(self._labels).values())

        theDataTraces = [{
            "name": datasetKey,
            'y': [self._rawDataDict[datasetKey][label]
                  for label in self._labels],
            'x': [label for label in self._labels],
            'marker_color': statColors if colorPerLabel
            else statColors[datasetKey]
            } for datasetKey in self._rawDataDict]
        self._graphData = {"title": self._title, 'traces': theDataTraces,
                           'x_axis': self._xAxis, 'y_axis': self._yAxis}

    def figure(self, typeFigure=GraphTrial.BAR):
        showLegend = True
        data = None
        fig = go.Figure()

        for trace in self._graphData['traces']:
            name = trace['name']
            color = trace['marker_color']
            if self._orientation == 'v':
                x = trace['x']
                y = trace['y']
            else:
                x = trace['y']
                y = trace['x']

            showLegend = self._showLegend
            data = go.Bar(orientation=self._orientation,
                          name=name, marker={'color': color},
                          x=x, y=y)
            fig.add_trace(data)

        # Update layout for graph object Figure
        if self._orientation == 'v':
            xaxis_title = self._graphData['x_axis']
            yaxis_title = self._graphData['y_axis']
        else:
            xaxis_title = self._graphData['y_axis']
            yaxis_title = self._graphData['x_axis']

        fig.update_layout(
            paper_bgcolor=COLOR_bg_color_cards,
            title_font_color="white",
            plot_bgcolor=COLOR_bg_color_cards,
            font_color='white',
            title_text=self._graphData['title'] if self._showTitle else '',
            showlegend=showLegend,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-1,
                xanchor="left",
                x=0),
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title)

        # Turn graph object into local plotly graph
        plotly_plot_obj = plot({'data': fig}, output_type='div')
        return plotly_plot_obj
