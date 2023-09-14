from plotly.offline import plot
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from django.utils.translation import gettext_lazy as _

# from plotly.validators.scatter.marker import SymbolValidator

COLOR_main_color = '#a500a5'
COLOR_red = '#ff6e73'
COLOR_yellow = '#ffd26e'
COLOR_estimulant = '#ffd26e'
COLOR_green = '#92eeb9'
COLOR_nutritional = '#92eeb9'
COLOR_blue = '#00bdeb'
COLOR_control = '#00bdeb'
COLOR_grey = '#F0EEEB'
COLOR_unknown = '#F0EEEB'
COLOR_black = '#333333'
COLOR_bio_morado = '#aa4ae4'
COLOR_KEY_THESIS = '#aa4ae4'
COLOR_CONTROL = '#B1C23F'
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
COLOR_bs_text_color_table = '#000'
COLOR_bg_color = '#282828'
COLOR_bg_color_cards = '#fff'
COLOR_TEXT = '#333'
COLOR_bg_color_cards_weather = '#F5FFFF'
COLOR_grid = '#f0f0f0'
COLOR_bio = '#aa4ae4'

CUSTOM_COLOR_0 = '#4CAF50'
CUSTOM_COLOR_1 = '#FF5722'
CUSTOM_COLOR_2 = '#3F51B5'
CUSTOM_COLOR_3 = '#009688'
CUSTOM_COLOR_4 = '#FFEB3B'
CUSTOM_COLOR_5 = '#795548'
CUSTOM_COLOR_6 = '#E91E63'
CUSTOM_COLOR_7 = '#2196F3'
CUSTOM_COLOR_8 = '#9E9E9E'
CUSTOM_COLOR_9 = '#FFC107'
CUSTOM_COLOR_10 = '#607D8B'
CUSTOM_COLOR_11 = '#9C27B0'
CUSTOM_COLOR_12 = '#03A9F4'
CUSTOM_COLOR_13 = '#8BC34A'
CUSTOM_COLOR_14 = '#FF9800'
CUSTOM_COLOR_15 = '#673AB7'
CUSTOM_COLOR_16 = '#00BCD4'
CUSTOM_COLOR_17 = '#CDDC39'
CUSTOM_COLOR_18 = '#F44336'

ALL_COLORS = [COLOR_main_color, COLOR_red, COLOR_yellow, COLOR_green,
              COLOR_blue, COLOR_grey, COLOR_bio_morado,
              COLOR_morado,
              COLOR_violeta, COLOR_bs_blue, COLOR_bs_indigo, COLOR_bs_purple,
              COLOR_bs_pink, COLOR_bs_red,  COLOR_bs_orange, COLOR_bs_yellow,
              COLOR_bs_green, COLOR_bs_teal, COLOR_bs_cyan, COLOR_bs_white,
              COLOR_bs_gray, COLOR_bs_gray_dark, COLOR_bs_primary,
              COLOR_bs_secondary, COLOR_bs_success, COLOR_bs_info,
              COLOR_bs_warning, COLOR_bs_danger, COLOR_bs_light,
              COLOR_bs_dark, COLOR_bs_text_color, COLOR_bg_color]


class WeatherGraph:
    DEFAULT_HEIGHT = 175

    def __init__(self, dates, non_recent_dates, mean_temps, min_temps,
                 max_temps, precip, precip_hrs,
                 soil_moist_1, soil_moist_2, soil_moist_3, soil_moist_4,
                 soil_temps_1, soil_temps_2, soil_temps_3, soil_temps_4,
                 rel_humid, dew_point
                 ):
        self.dates = dates
        self.non_recent_dates = non_recent_dates
        self.mean_temps = mean_temps
        self.min_temps = min_temps
        self.max_temps = max_temps
        self.precip = precip
        self.precip_hrs = precip_hrs
        self.soil_moist_1 = soil_moist_1
        self.soil_moist_2 = soil_moist_2
        self.soil_moist_3 = soil_moist_3
        self.soil_moist_4 = soil_moist_4
        self.soil_temps_1 = soil_temps_1
        self.soil_temps_2 = soil_temps_2
        self.soil_temps_3 = soil_temps_3
        self.soil_temps_4 = soil_temps_4
        self.rel_humid = rel_humid
        self.dew_point = dew_point
        return

    def addTrace(self, fig, topicData, name, color, width=2, non_recent=False):
        if topicData:
            dates = self.non_recent_dates if non_recent else self.dates
            fig.add_trace(go.Scatter(
                x=dates, y=topicData,
                name=name,
                line=dict(color=color, width=width)))

    def applyDefaultLayout(self, fig,
                           title=_('weather'),
                           title_yaxes=None):
        fig.update_layout(
            paper_bgcolor=COLOR_bg_color_cards_weather,
            title_font_color=COLOR_TEXT,
            plot_bgcolor=COLOR_bg_color_cards_weather,
            font_color=COLOR_TEXT,
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5,
                        xanchor="left", x=-0.5),
            margin=dict(
                t=0,  # Adjust this value to reduce the top margin
                r=20,  # Right margin
                b=20,  # Bottom margin
                l=20   # Left margin
            ),
            title_text='',  # title.upper(),
            height=WeatherGraph.DEFAULT_HEIGHT,
            autosize=True)
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=COLOR_grid)
        if title_yaxes:
            fig.update_yaxes(title_text=title_yaxes)

    def draw_precip(self):
        if not self.dates:
            return False
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        self.addTrace(fig, self.precip_hrs,
                      _('precipitation') + _("hours"),
                      'lightblue')
        fig.add_bar(x=self.dates, y=self.precip,
                    name=_('precipitation') + '(mm)',
                    marker=dict(color='royalblue', opacity=0.3),
                    secondary_y=True)

        self.applyDefaultLayout(
            fig, title=_('precipitation'))
        fig.update_yaxes(
            title_text=_('precipitation') + ' ' + _("hours"),
            secondary_y=False)
        fig.update_yaxes(
            title_text=_('precipitation') + ' ' + '(mm)',
            secondary_y=True)

        plotly_plot_obj = plot({'data': fig}, output_type='div')
        return plotly_plot_obj

    def draw_temp(self):
        if not self.dates:
            return False
        fig = make_subplots()

        self.addTrace(fig, self.min_temps, 'Min Temp', 'lightblue')
        self.addTrace(fig, self.mean_temps, 'Mean Temp', 'yellow')
        self.addTrace(fig, self.max_temps, 'Max Temp', 'firebrick')

        self.applyDefaultLayout(
            fig, title=_('temperature'),
            title_yaxes=_('temperature') + ' ' + '(°C)')

        plotly_plot_obj = plot({'data': fig}, output_type='div')
        return plotly_plot_obj

    def draw_soil_temp(self):
        if not self.non_recent_dates:
            return False
        fig = make_subplots()

        self.addTrace(fig, self.soil_temps_1,
                      '0-7cm', '#e3f2e2', non_recent=True)
        self.addTrace(fig, self.soil_temps_2,
                      '7-28cm', '#b3d0b1', non_recent=True)
        self.addTrace(fig, self.soil_temps_3,
                      '28-100cm', '#84ae82', non_recent=True)
        self.addTrace(fig, self.soil_temps_4,
                      '100-255cm', '#558d55', non_recent=True)

        self.applyDefaultLayout(
            fig, title=_('soil temperature'),
            title_yaxes=_('soil temperature') + ' ' + '(°C)')

        if len(fig.data) > 0:
            plotly_plot_obj = plot({'data': fig}, output_type='div')
            return plotly_plot_obj
        else:
            return _('No data for soil temperature')

    def draw_soil_moist(self):
        if not self.non_recent_dates:
            return False
        fig = make_subplots()

        self.addTrace(fig, self.soil_moist_1, '0-7cm',
                      '#e3f2e2', non_recent=True)
        self.addTrace(fig, self.soil_moist_2, '7-28cm',
                      '#b3d0b1', non_recent=True)
        self.addTrace(fig, self.soil_moist_3, '28-100cm',
                      '#84ae82', non_recent=True)
        self.addTrace(fig, self.soil_moist_4, '100-255cm',
                      '#558d55', non_recent=True)

        self.applyDefaultLayout(
            fig, title=_('soil moisture'),
            title_yaxes=_('soil moisture') + ' ' + '(m³/m³)')

        if len(fig.data) > 0:
            plotly_plot_obj = plot({'data': fig}, output_type='div')
            return plotly_plot_obj
        else:
            return _('No data for soil moisture')

    def draw_humid(self):
        if not self.non_recent_dates:
            return False
        fig = make_subplots()

        self.addTrace(fig, self.rel_humid, 'relative humidity',
                      COLOR_bs_purple, non_recent=True)
        self.applyDefaultLayout(
            fig, title=_('relative humidity'),
            title_yaxes=_('relative humidity') + ' ' + "(%)")
        plotly_plot_obj = plot({'data': fig}, output_type='div')
        return plotly_plot_obj

    def draw_dew(self):
        if not self.non_recent_dates:
            return False
        fig = make_subplots()

        self.addTrace(fig, self.dew_point, 'dew point', COLOR_bs_blue,
                      non_recent=True)
        self.applyDefaultLayout(
            fig, title=_('dew point'),
            title_yaxes=_('dew point') + ' ' + "(°C)")

        plotly_plot_obj = plot({'data': fig}, output_type='div')
        return plotly_plot_obj


class WeatherGraphFactory:

    @classmethod
    def formatData(cls, id, graph, title, show,
                   backgroundClass='bg-weather-cards'):
        return {'id': id.lower().replace(" ", ""),
                'title': title, 'content': graph,
                'collapse': '' if show else 'collapse',
                'backgroundClass': backgroundClass}

    @classmethod
    def build(cls, dates, non_recent_dates, mean_temps, min_temps,
              max_temps, precip, precip_hrs, soil_moist_1,
              soil_moist_2, soil_moist_3, soil_moist_4,
              soil_temps_1, soil_temps_2, soil_temps_3,
              soil_temps_4, rel_humid, dew_point):
        graph = WeatherGraph(dates, non_recent_dates, mean_temps, min_temps,
                             max_temps, precip, precip_hrs, soil_moist_1,
                             soil_moist_2, soil_moist_3, soil_moist_4,
                             soil_temps_1, soil_temps_2, soil_temps_3,
                             soil_temps_4, rel_humid, dew_point)
        return [
            cls.formatData('tempGraph', graph.draw_temp(),
                           _('temperature'), True),
            cls.formatData('precipGraph', graph.draw_precip(),
                           _('precipitation'), True),
            cls.formatData('soilTempGraph', graph.draw_soil_temp(),
                           _('soil temperature'), False),
            cls.formatData('soilMoistGraph', graph.draw_soil_moist(),
                           _('soil moisture'), False),
            cls.formatData('humidGraph', graph.draw_humid(),
                           _('relative humidity'), True),
            cls.formatData('dewPointGraph', graph.draw_dew(),
                           _('dew point'), True)]


class GraphTrial:
    _graphData = []
    _level = None
    _xAxis = None
    SCATTER = 'scatter'
    BAR = 'bar'
    COLUMN = 'column'
    VIOLIN = 'violin'
    LINE = 'line'

    DEFAULT_HEIGHT = 275

    L_ASSMT = 'assmt'
    L_THESIS = 'thesis'
    L_REPLICA = 'replica'
    L_SAMPLE = 'sample'
    L_DATE = 'date'
    L_DAF = 'daf'
    L_DOSIS = 'dosis'
    LEVELS = [L_THESIS, L_REPLICA, L_SAMPLE]
    _title = None

    NO_DATA_AVAILABLE = 'No data available yet'

    # SYMBOL_LIST = SymbolValidator().values
    SYMBOL_LIST = ['cicle', 'square', 'star', 'diamond', 'cross',
                   'x', 'triangle-up', 'triangle-down',
                   'triangle-left', 'triangle-right', 'hexagram',
                   'star-triangle-up', 'star-triangle-down',
                   'diamond-tall', 'diamond-wide', 'square-cross',
                   'circle-cross', 'circle-x', 'asterisk', 'hash']

    COLOR_CONCLUSION_GRAPH = [COLOR_CONTROL, COLOR_KEY_THESIS]

    COLOR_LIST = [CUSTOM_COLOR_0, CUSTOM_COLOR_1, CUSTOM_COLOR_2,
                  CUSTOM_COLOR_3, CUSTOM_COLOR_4, CUSTOM_COLOR_5,
                  CUSTOM_COLOR_6, CUSTOM_COLOR_7, CUSTOM_COLOR_8,
                  CUSTOM_COLOR_9, CUSTOM_COLOR_10, CUSTOM_COLOR_11,
                  CUSTOM_COLOR_12, CUSTOM_COLOR_13, CUSTOM_COLOR_14,
                  CUSTOM_COLOR_15, CUSTOM_COLOR_16, CUSTOM_COLOR_17,
                  CUSTOM_COLOR_18]

    def __init__(self, level, rateType, ratedPart,
                 traces, xAxis=L_DATE,
                 showTitle=False):
        self._level = level
        self._showTitle = showTitle
        self._xAxis = xAxis
        self._title = self.getTitle(rateType, ratedPart)
        self._graphData = {
                'title': self._title,
                'x_axis': xAxis,
                'y_axis': rateType.unit,
                'traces': traces}

    def addColorLinesToTraces(self, colorDict):
        for thesisNumber in colorDict:
            self._graphData['traces'][thesisNumber]['trace_color'] = colorDict[thesisNumber]  # noqa E501

    def addTrace(self, line, name, color='#C3C3C3',
                 shape='dot', marker_symbol='cicle'):
        trace = {'x': line['x'], 'y': line['y'],
                 'name': name,
                 'trace_color': color, 'dash': shape}
        if marker_symbol:
            trace['marker_symbol'] = marker_symbol
            trace['marker_size'] = 20
        self._graphData['traces'][0] = trace

    def preparePlots(self, typeFigure='scatter', orientation='v'):
        fig = self.figure(self._graphData, typeFigure=typeFigure,
                          orientation=orientation)
        return self.plot(fig)

    def drawConclussionGraph(self, typeFigure=LINE,
                             orientation='v'):
        fig = self.figure(self._graphData, typeFigure=typeFigure,
                          showLegend=False, orientation=orientation)
        return self.plot(fig)

    def bar(self):
        return self.preparePlots(typeFigure=GraphTrial.BAR, orientation='h')

    def column(self):
        return self.preparePlots(typeFigure=GraphTrial.BAR, orientation='v')

    def scatter(self):
        return self.preparePlots(typeFigure=GraphTrial.SCATTER)

    def violin(self):
        return self.preparePlots(typeFigure=GraphTrial.VIOLIN)

    def line(self):
        return self.preparePlots(typeFigure=GraphTrial.LINE)

    DRAW_TYPE = {LINE: line,
                 BAR: bar,
                 SCATTER: scatter,
                 VIOLIN: violin,
                 COLUMN: column}
    DRAW_LEVEL = {L_DOSIS: line,
                  L_ASSMT: column,
                  L_THESIS: bar}

    def formatFigure(self, fig, thisGraph, showLegend,
                     orientation, typeFigure, num_x):
        # Update layout for graph object Figure
        if orientation == 'v':
            xaxis_title = thisGraph['x_axis']
            yaxis_title = thisGraph['y_axis']
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=COLOR_grid)
        else:
            xaxis_title = thisGraph['y_axis']
            yaxis_title = thisGraph['x_axis']
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=COLOR_grid)

        legend = dict(orientation="v", yanchor="middle", y=0.5,
                      xanchor="left", x=-0.5)

        fig.update_layout(
            paper_bgcolor=COLOR_bg_color_cards,
            title_font_color=COLOR_TEXT,
            plot_bgcolor=COLOR_bg_color_cards,
            font_color=COLOR_TEXT,
            title_text=thisGraph['title'] if self._showTitle else '',
            showlegend=showLegend,
            autosize=True,
            legend=legend,
            margin=dict(
                t=0,  # Adjust this value to reduce the top margin
                r=20,  # Right margin
                b=20,  # Bottom margin
                l=20   # Left margin
            ),
            height=GraphTrial.DEFAULT_HEIGHT,
            yaxis_title=yaxis_title)

        if self._xAxis != GraphTrial.L_DATE:
            fig.update_layout(xaxis_title=xaxis_title)

        if typeFigure == GraphTrial.BAR:
            fig.update_traces(textfont_size=20)

        if num_x == 1 and self._xAxis == GraphTrial.L_DATE:
            if orientation == 'v':
                fig.update_layout(xaxis=dict(tickformat='%d %b %Y'))
            else:
                fig.update_layout(yaxis=dict(tickformat='%d %b %Y'))

        if typeFigure == GraphTrial.VIOLIN:
            fig.update_layout(violinmode='group')
        fig.update_yaxes(automargin=True)

    def applyBar(self, x, y, orientation, name, color):
        if orientation == 'h':
            xValues = [round(v, 2) for v in x]
            yValues = y
            text = xValues
        else:
            yValues = [round(v, 2) for v in y]
            text = yValues
            xValues = x
        data = go.Bar(orientation=orientation,
                      name=name, marker={'color': color},
                      text=text,
                      x=xValues, y=yValues)
        return data

    def figure(self, thisGraph, showLegend=True,
               typeFigure=SCATTER, orientation='v'):
        data = None
        fig = go.Figure()

        for traceKey in thisGraph['traces']:
            trace = thisGraph['traces'][traceKey]
            name = trace['name']
            color = trace['trace_color']
            marker_symbol = trace.get('marker_symbol', 'circle')
            marker_size = trace.get('marker_size', 10)
            marker = {'color': color, 'symbol': marker_symbol,
                      'size': marker_size}
            if orientation == 'v':
                x = trace['x']
                y = trace['y']
            else:
                x = trace['y']
                y = trace['x']

            if typeFigure == GraphTrial.BAR:
                data = self.applyBar(x, y, orientation, name, color)
            elif typeFigure == GraphTrial.LINE:
                marker = {}
                line = {'color': color, 'width': 3}
                if 'dash' in trace:
                    line['dash'] = trace['dash']
                if 'marker' in trace:
                    markerMode = 'lines+markers'
                    marker = marker
                else:
                    markerMode = 'lines'
                data = go.Scatter(name=name, x=x, y=y,
                                  line=line, mode=markerMode,
                                  marker=marker)
            elif typeFigure == GraphTrial.SCATTER:
                if self._xAxis == GraphTrial.L_DATE:
                    markerMode = 'lines+markers'
                else:
                    markerMode = 'markers'
                data = go.Scatter(name=name, x=x, y=y,
                                  marker=marker,
                                  mode=markerMode, marker_size=15)
            elif typeFigure == GraphTrial.VIOLIN:
                data = go.Violin(name=name, x=x, y=y,
                                 box_visible=True,
                                 meanline_visible=True,
                                 line_color=color)
            fig.add_trace(data)

        self.formatFigure(fig, thisGraph, showLegend, orientation,
                          typeFigure, len(x))
        return fig

    def plot(self, fig):
        # Turn graph object into local plotly graph
        plotly_plot_obj = plot({'data': fig}, output_type='div')
        return plotly_plot_obj

    @ classmethod
    def classColGraphs(cls, rcolumns, max_columns):
        rcolumns = 1 if rcolumns == 0 else rcolumns
        columns = max_columns if max_columns < rcolumns else rcolumns
        return 'col-md-{}'.format(int(12 / columns))

    def getTitle(self, rateType, ratedPart):
        return '{}({}) {}'.format(rateType.name, rateType.unit, ratedPart)


class GraphStat():
    def __init__(self, rawDataDict, labels, showLegend=True,
                 title=None, showTitle=False,
                 xAxis='month', yAxis='# trials', orientation='v',
                 barmode="group"):
        self._graphData = None
        self._title = title
        self._orientation = orientation
        self._labels = labels
        self._rawDataDict = rawDataDict
        self._xAxis = xAxis
        self._yAxis = yAxis
        self._showTitle = showTitle
        self._showLegend = showLegend
        self._barmode = barmode

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
            'trace_color': statColors if colorPerLabel
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
            color = trace['trace_color']
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
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor=COLOR_grid)
        else:
            xaxis_title = self._graphData['y_axis']
            yaxis_title = self._graphData['x_axis']
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor=COLOR_grid)

        fig.update_layout(
            paper_bgcolor=COLOR_bg_color_cards,
            title_font_color=COLOR_TEXT,
            plot_bgcolor=COLOR_bg_color_cards,
            font_color=COLOR_TEXT,
            title_text=self._graphData['title'] if self._showTitle else '',
            showlegend=showLegend,
            margin=dict(
                t=20,  # Adjust this value to reduce the top margin
                r=10,  # Right margin
                b=20,  # Bottom margin
                l=10   # Left margin
            ),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=0,
                xanchor="left",
                x=0),
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            barmode=self._barmode)

        if self._orientation == 'h':
            fig.update_yaxes(autorange="reversed")

        # Turn graph object into local plotly graph
        plotly_plot_obj = plot({'data': fig}, output_type='div')
        return plotly_plot_obj


class EfficacyGraph:
    @staticmethod
    def draw(numNameDict, numValueDict,
             title_text=_('efficacy') + '(%)', showLegend=False,
             yaxis_title='Abbott (%)', xaxis_title='thesis',
             barmode='group'):

        colors = []
        values = []
        labels = []
        for key in numNameDict:
            if key in numValueDict:
                values.append(numValueDict[key])
                colors.append(GraphTrial.COLOR_LIST[key])
                labels.append(numNameDict[key])

        # Create a bar trace
        trace = go.Bar(
            x=labels,
            y=values,
            text=values,
            marker=dict(color=colors))

        # Create the figure
        figure = go.Figure(data=[trace])
        figure.update_layout(
            paper_bgcolor=COLOR_bg_color_cards,
            title_font_color=COLOR_TEXT,
            plot_bgcolor=COLOR_bg_color_cards,
            font_color=COLOR_TEXT,
            title_text=title_text,
            showlegend=showLegend,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=0,
                xanchor="left",
                x=0),
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            barmode=barmode)
        figure.update_traces(textfont_size=20)
        figure.update_yaxes(showgrid=True, gridwidth=1, gridcolor=COLOR_grid)
        plotly_plot_obj = plot({'data': figure}, output_type='div')
        return plotly_plot_obj


class ProductCategoryGraph:

    @staticmethod
    def draw(dictValues, bios=3,
             title_text=None, showLegend=True,
             yaxis_title='trials', xaxis_title='Trials'):

        colors = []
        values = []
        labels = []
        totals = 0
        for key in dictValues:
            value = dictValues[key]['value']
            color = dictValues[key]['color']
            key = key if key else 'Undefined'
            totals += value
            values.append(value)
            colors.append(color)
            labels.append(f'{value} {key}')

        # Create a bar trace
        trace_outer = go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            textinfo='none',  # Do not display labels on the chart
            hoverinfo='label',
            hole=0.9)

        trace_center = go.Pie(
            labels=[' '],
            values=[totals],
            marker_colors=[COLOR_bs_white],
            textinfo='none',
            hole=0.85)

        trace_inner = go.Pie(
            labels=[' ', f'{bios} Bio'],
            values=[totals-bios, bios],
            marker_colors=[COLOR_bs_white, COLOR_bio],
            textinfo='none',  # Do not display labels on the chart
            hoverinfo='label',
            hole=0.8)

        # Create the figure
        figure = go.Figure(data=[trace_inner, trace_center, trace_outer])

        annotations = [
            dict(text='trials',
                 x=0.5, y=0.3, font_size=20,
                 font_color='grey',
                 showarrow=False),
            dict(text=f'{totals}',
                 x=0.5, y=0.5, font_size=64,
                 showarrow=False)]

        figure.update_layout(
            annotations=annotations,
            paper_bgcolor=COLOR_bg_color_cards,
            title_font_color=COLOR_TEXT,
            plot_bgcolor=COLOR_bg_color_cards,
            font_color=COLOR_TEXT,
            font_size=24,
            title_text=title_text,
            showlegend=showLegend,
            margin=dict(
                t=20,  # Adjust this value to reduce the top margin
                r=20,  # Right margin
                b=20,  # Bottom margin
                l=20   # Left margin
            ),
            legend=dict(
                font_size=14,
                orientation="h",
                yanchor="top",
                y=0,
                xanchor="left",
                x=0),
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title)
        figure.update_traces(textfont_size=20)
        plotly_plot_obj = plot({'data': figure}, output_type='div')
        return plotly_plot_obj


class PieGraph:

    @staticmethod
    def draw(keyValue, label, totals,
             title_text=None, showLegend=False,
             yaxis_title='trials', xaxis_title='Trials'):

        trace = go.Pie(
            labels=[' ', f'{keyValue} {label}'],
            values=[totals-keyValue, keyValue],
            marker_colors=[COLOR_bs_white, COLOR_bio],
            textinfo='none',  # Do not display labels on the chart
            hoverinfo='label',
            hole=0.85)

        # Create the figure
        figure = go.Figure(data=[trace])

        annotations = [
            dict(text=label,
                 x=0.5, y=0.25, font_size=20,
                 font_color='grey',
                 showarrow=False),
            dict(text=f'{keyValue}',
                 x=0.5, y=0.8, font_size=30,
                 showarrow=False)]

        figure.update_layout(
            annotations=annotations,
            paper_bgcolor='#F7F7F7',
            title_font_color=COLOR_TEXT,
            plot_bgcolor='#F7F7F7',
            font_color=COLOR_TEXT,
            font_size=12,
            title_text=title_text,
            showlegend=showLegend,
            margin=dict(
                t=20,  # Adjust this value to reduce the top margin
                r=20,  # Right margin
                b=20,  # Bottom margin
                l=20   # Left margin
            ),
            legend=dict(
                font_size=14,
                orientation="h",
                yanchor="top",
                y=0,
                xanchor="left",
                x=0),
            height=150,
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title)
        figure.update_traces(textfont_size=20)
        plotly_plot_obj = plot({'data': figure}, output_type='div')
        return plotly_plot_obj
