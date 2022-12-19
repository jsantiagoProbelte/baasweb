
from plotly.offline import plot
import plotly.graph_objs as go


class Graph:
    _graphData = []
    SCATTER = 'scatter'
    BAR = 'bar'

    def __init__(self, level,
                 trialAssessments, dataPoints):
        self._graphData = self.buildData(level,
                                         trialAssessments, dataPoints)

    def preparePlots(self, typeFigure='scatter', orientation='v'):
        graphPlots = [self.figure(
            item['x'], item['y'], title=item['title'],
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
               xaxis_title=None, yaxis_title=None):
        data = None
        if typeFigure == Graph.BAR:
            data = go.Bar(orientation=orientation,
                          name=name, x=theY, y=theX)
        elif typeFigure == Graph.SCATTER:
            data = go.Scatter(name=name, x=theY, y=theX)
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
            return []
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
            for dataPoint in dataPoints:
                if unit.id == dataPoint.unit.id:
                    theX.append(dataPoint.reference.name)
                    theY.append(dataPoint.value)
            thisGraph['x'] = theX
            thisGraph['y'] = theY
            graphs.append(thisGraph)
        return graphs
