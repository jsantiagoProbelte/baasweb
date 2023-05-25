from plotly.offline import plot
import plotly.graph_objs as go
from plotly.subplots import make_subplots

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


class WeatherGraph:
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

    def draw_precip(self):
        if not self.dates:
            return False
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        self.addTrace(fig, self.precip_hrs, 'Precipitation Hours', 'lightblue')
        fig.add_bar(x=self.dates, y=self.precip,
                    name='Precipitation (mm)', marker=dict(
                        color='royalblue', opacity=0.3), secondary_y=True)

        fig.update_layout(
            paper_bgcolor=COLOR_bg_color_cards,
            title_font_color="white",
            plot_bgcolor=COLOR_bg_color_cards,
            font_color='white',
            showlegend=False,
            autosize=True
        )
        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="Precipitation Hours", secondary_y=False)
        fig.update_yaxes(title_text="Precipitation (mm)", secondary_y=True)

        plotly_plot_obj = plot({'data': fig}, output_type='div')
        return plotly_plot_obj

    def draw_temp(self):
        if not self.dates:
            return False
        fig = make_subplots()

        self.addTrace(fig, self.min_temps, 'Min Temp', 'lightblue')
        self.addTrace(fig, self.mean_temps, 'Mean Temp', 'yellow')
        self.addTrace(fig, self.max_temps, 'Max Temp', 'firebrick')

        fig.update_layout(
            paper_bgcolor=COLOR_bg_color_cards,
            title_font_color="white",
            plot_bgcolor=COLOR_bg_color_cards,
            font_color='white',
            showlegend=False,
            autosize=True
        )

        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="Temperatures (°C)")

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

        fig.update_layout(
            paper_bgcolor=COLOR_bg_color_cards,
            title_font_color="white",
            plot_bgcolor=COLOR_bg_color_cards,
            font_color='white',
            autosize=True
        )

        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="Soil Temperatures (°C)")

        if len(fig.data) > 0:
            plotly_plot_obj = plot({'data': fig}, output_type='div')
            return plotly_plot_obj
        else:
            return 'No data for soil temperature'

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

        fig.update_layout(
            paper_bgcolor=COLOR_bg_color_cards,
            title_font_color="white",
            plot_bgcolor=COLOR_bg_color_cards,
            font_color='white',
            autosize=True
        )

        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="Soil Moisture (m³/m³)")

        if len(fig.data) > 0:
            plotly_plot_obj = plot({'data': fig}, output_type='div')
            return plotly_plot_obj
        else:
            return 'No data for soil moisture'

    def draw_humid(self):
        if not self.non_recent_dates:
            return False
        fig = make_subplots()

        self.addTrace(fig, self.rel_humid, 'Relative Humidity',
                      COLOR_bs_purple, non_recent=True)
        fig.update_layout(
            paper_bgcolor=COLOR_bg_color_cards,
            title_font_color="white",
            plot_bgcolor=COLOR_bg_color_cards,
            font_color='white',
            autosize=True
        )
        fig.update_yaxes(title_text="Relative Humidity (%)")
        fig.update_xaxes(title_text="Date")
        plotly_plot_obj = plot({'data': fig}, output_type='div')
        return plotly_plot_obj

    def draw_dew(self):
        if not self.non_recent_dates:
            return False
        fig = make_subplots()

        self.addTrace(fig, self.dew_point, 'Dew Point', COLOR_bs_blue,
                      non_recent=True)
        fig.update_layout(
            paper_bgcolor=COLOR_bg_color_cards,
            title_font_color="white",
            plot_bgcolor=COLOR_bg_color_cards,
            font_color='white',
            autosize=True
        )
        fig.update_yaxes(title_text="Dew Point (°C)")
        fig.update_xaxes(title_text="Date")
        plotly_plot_obj = plot({'data': fig}, output_type='div')
        return plotly_plot_obj


class WeatherGraphFactory:
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
        return {'tempGraph': graph.draw_temp(),
                'precipGraph': graph.draw_precip(),
                'soilTempGraph': graph.draw_soil_temp(),
                'soilMoistGraph': graph.draw_soil_moist(),
                'humidGraph': graph.draw_humid(),
                'dewPointGraph': graph.draw_dew()}


class GraphTrial:
    _graphData = []
    _level = None
    _xAxis = None
    SCATTER = 'scatter'
    BAR = 'bar'
    VIOLIN = 'violin'
    LINE = 'line'

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
                 traces, xAxis=L_DATE,
                 showTitle=True):
        self._level = level
        self._showTitle = showTitle
        self._graphData = {
                'title': self.getTitle(rateType, ratedPart),
                'x_axis': xAxis,
                'y_axis': rateType.unit,
                'traces': traces}

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
