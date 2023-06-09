from math import ceil
from trialapp.data_models import Assessment
from baaswebapp.baas_archive import BaaSArchive
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table, TableStyle
from trialapp.models import\
    FieldTrial, Thesis, Project, Objective, Replica,\
    Product, ApplicationMode, TrialStatus, TrialType, Crop, CropVariety,\
    Plague, CultivationMethod, Irrigation, Application
from catalogue.models import RateUnit
from django import forms
from io import BytesIO


class MyDateInput(forms.widgets.DateInput):
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        # use the browser's HTML date picker (no css/javascript required)
        context['widget']['type'] = 'date'
        return context


class TrialModel():
    T_D = 'TypeDate'
    T_I = 'TypeInteger'
    T_N = 'TypeNoChange'
    T_T = 'TypeText'
    FIELDS = {
        'Goal': {
            'project': {'label': "Project", 'required': True, 'type': T_N,
                        'cls': Project},
            'objective': {'label': "Objective", 'required': True, 'type': T_N,
                          'cls': Objective},
            'product': {'label': "Main Product", 'required': True,
                        'type': T_N, 'cls': Product},
            'crop': {'label': "Crop", 'required': True, 'type': T_N,
                     'cls': Crop},
            'plague': {'label': "Plague", 'required': False, 'type': T_N,
                       'cls': Plague},
        },
        'Status': {
            'trial_type': {'label': 'Type', 'required': True, 'type': T_N,
                           'cls': TrialType},
            'trial_status': {'label': 'Status', 'required': True, 'type': T_N,
                             'cls': TrialStatus},
            'responsible': {'label': 'Responsible', 'required': True,
                            'type': T_N},
            'initiation_date': {'label': 'Started', 'required': True,
                                'type': T_D},
            'completion_date': {'label': 'Completed by', 'required': False,
                                'type': T_D},
        },
        'Report': {
            'description': {
                'label': "Description", 'required': False,
                'type': T_T, 'rows': 10},
            'comments_criteria': {
                'label': "Evaluation Criteria",
                'required': False, 'type': T_T, 'rows': 5},
            'conclusion': {
                'label': "Conclusion", 'required': False,
                'type': T_T, 'rows': 10}
        },
        'Cultive': {
            'crop_variety': {'label': 'Crop Variety', 'required': False,
                             'type': T_N, 'cls': CropVariety},
            'cultivation': {'label': 'Cultivation Mode', 'required': False,
                            'type': T_N, 'cls': CultivationMethod},
            'irrigation': {'label': 'Irrigation', 'required': False,
                           'type': T_N, 'cls': Irrigation},
            'crop_age': {'label': 'Crop Age (years)', 'required': False,
                         'type': T_I},
            'seed_date': {'label': 'Seed date', 'required': False,
                          'type': T_D},
            'transplant_date': {'label': 'Transplante date', 'required': False,
                                'type': T_D},
        },
        'Assessments': {
            'ref_to_eppo': {'label': "EPPO Reference", 'required': False,
                            'type': T_N},
            'ref_to_criteria': {'label': "Criteria Reference",
                                'required': False, 'type': T_N},
        },
        'Applications': {
            'application_volume': {'label': "Volume",
                                   'required': False, 'type': T_N},
            'application_volume_unit': {
                'label': "Unit", 'required': False, 'type': T_N,
                'cls': RateUnit},
            'mode': {'label': "Mode", 'required': False,
                     'type': T_N, 'cls': ApplicationMode},
        },
        'Layout': {
            'blocks': {'label': "# blocks", 'required': True,
                       'type': T_I},
            'replicas_per_thesis': {'label': "# replicas", 'required': True,
                                    'type': T_I},
            'samples_per_replica': {'label': "# samples/replica ",
                                    'required': False, 'type': T_I},
            'distance_between_plants': {'label': "Plants separation",
                                        'required': False, 'type': T_N},
            'distance_between_rows': {'label': "Rows separation",
                                      'required': False, 'type': T_N},
            'number_rows': {'label': "# rows", 'required': False, 'type': T_I},
            'lenght_row': {'label': "Row length (m)", 'required': False,
                           'type': T_N},
            'net_surface': {'label': "Net area plot (m2)", 'required': False,
                            'type': T_N},
            'gross_surface': {'label': "Gross area plot (m2)",
                              'required': False, 'type': T_N},
        },
        'Location': {
            'contact': {'label': "Farmer", 'required': False, 'type': T_N},
            'cro': {'label': "CRO", 'required': False, 'type': T_N},
            'location': {'label': "City/Area", 'required': False, 'type': T_N},
            'latitude': {'label': "Latitude", 'required': False,
                         'type': T_N},
            'longitude': {'label': "Longitude", 'required': False,
                          'type': T_N},
        }
    }

    LAB_TRIAL_FIELDS = (
            'name', 'trial_type', 'objective', 'responsible', 'description',
            'project', 'code',
            'product', 'crop', 'plague', 'initiation_date', 'completion_date',
            'trial_status', 'contact', 'replicas_per_thesis',
            'samples_per_replica')

    FIELD_TRIAL_FIELDS = (
            'name', 'trial_type', 'objective', 'responsible', 'description',
            'ref_to_eppo', 'ref_to_criteria', 'comments_criteria', 'project',
            'product', 'crop', 'plague', 'initiation_date', 'completion_date',
            'trial_status', 'contact', 'cro', 'location', 'blocks',
            'replicas_per_thesis', 'samples_per_replica',
            'distance_between_plants', 'distance_between_rows', 'number_rows',
            'lenght_row', 'net_surface', 'gross_surface', 'code', 'irrigation',
            'application_volume', 'mode', 'crop_variety', 'cultivation',
            'crop_age', 'seed_date', 'transplant_date', 'longitude',
            'latitude', 'application_volume_unit', 'conclusion')

    @classmethod
    def applyModel(cls, trialForm):
        for block in TrialModel.FIELDS:
            for field in TrialModel.FIELDS[block]:
                if field not in trialForm.Meta.fields:
                    continue
                fieldData = TrialModel.FIELDS[block][field]
                trialForm.fields[field].label = fieldData['label']
                trialForm.fields[field].required = fieldData['required']
                typeField = fieldData['type']
                if typeField == TrialModel.T_D:
                    trialForm.fields[field].widget = MyDateInput()
                elif typeField == TrialModel.T_I:
                    trialForm.fields[field].widget = forms.NumberInput()
                elif typeField == TrialModel.T_T:
                    trialForm.fields[field].widget = forms.Textarea(
                        attrs={'rows': fieldData['rows']})
        # Querysets
        trialForm.fields['project'].queryset = Project.getObjects()
        trialForm.fields['objective'].queryset = Objective.getObjects()
        trialForm.fields['product'].queryset = Product.getObjects()
        trialForm.fields['crop'].queryset = Crop.getObjects()
        trialForm.fields['plague'].queryset = Plague.getObjects()
        if 'application_volume_unit' in trialForm.fields:
            trialForm.fields['application_volume_unit'].queryset =\
                RateUnit.getObjects()
        if 'crop_variety' in trialForm.fields:
            crops = CropVariety.getObjects()
            trialForm.fields['crop_variety'].queryset = crops

    @classmethod
    def prepareDataItems(cls, fieldTrial, asArray=False):
        trialDict = fieldTrial.__dict__
        trialData = {}
        if fieldTrial.trial_meta == FieldTrial.TrialMeta.LAB_TRIAL:
            modelFields = TrialModel.LAB_TRIAL_FIELDS
        else:
            modelFields = TrialModel.FIELD_TRIAL_FIELDS

        for group in TrialModel.FIELDS:
            if asArray:
                trialData[group] = {}
            else:
                trialData[group] = []
            for field in TrialModel.FIELDS[group]:
                if field not in modelFields:
                    continue
                label = TrialModel.FIELDS[group][field]['label']
                value = '?'
                if field in trialDict:
                    value = trialDict[field]
                else:
                    field_id = field + '_id'
                    if field_id not in trialDict:
                        continue
                    else:
                        theId = trialDict[field_id]
                        if theId is not None:
                            model = TrialModel.FIELDS[group][field]['cls']
                            value = model.objects.get(id=theId)
                showValue = value if value is not None else '?'
                if asArray:
                    trialData[group][label] = showValue
                else:
                    trialData[group].append({'name': label,
                                             'value': showValue})
        return trialData


class LayoutTrial:
    @classmethod
    def calculateLayoutDim(cls, fieldTrial, numberThesis):
        blocks = fieldTrial.blocks
        numberReplicas = fieldTrial.replicas_per_thesis
        rows = 0 if blocks == 0 else\
            ceil(numberThesis * numberReplicas / blocks)
        return blocks, rows

    @classmethod
    def computeInitialLayout(cls, fieldTrial, numberThesis):
        blocks, rows = LayoutTrial.calculateLayoutDim(
            fieldTrial, numberThesis)
        deck = [[LayoutTrial.setDeckCell(None, None, x=i+1, y=j+1)
                 for i in range(0, blocks)] for j in range(0, rows)]
        return deck, (blocks, rows)

    @classmethod
    def setDeckCell(cls, replica: Replica, assessment,
                    x=0, y=0,
                    onlyThis=None):
        if replica is None:
            return {'name': '-',
                    'replica_id': 0,
                    'x': x,
                    'y': y,
                    'number': 0}
        else:
            number = replica.thesis.number
            if onlyThis and replica.thesis.id != onlyThis:
                number = 0
            return {'name': replica.getTitle(),
                    'replica_id': replica.id,
                    'number': number,
                    'x': replica.pos_x,
                    'y': replica.pos_y,
                    'id': replica.generateReplicaDataSetId(assessment)}

    @classmethod
    def headerLayout(cls, fieldTrial: FieldTrial):
        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I',
                   'J', 'K', 'L', 'M', 'N']
        header = []
        for i in range(0, fieldTrial.blocks):
            header.append({'name': letters[i],
                           'replica_id': 0,
                           'number': 0})
        return header

    @classmethod
    def showLayout(cls, fieldTrial: FieldTrial,
                   assessment: Assessment, thesisTrial,
                   onlyThis=None):
        deck, (rows, columns) = LayoutTrial.computeInitialLayout(
            fieldTrial, len(thesisTrial))
        # Place the thesis in the deck
        for thesis in thesisTrial:
            for replica in Replica.getObjects(thesis):
                if (replica.pos_x > 0) and (replica.pos_y > 0) and\
                   (replica.pos_x <= rows) and (replica.pos_y <= columns):
                    deck[replica.pos_y-1][replica.pos_x-1] =\
                        LayoutTrial.setDeckCell(
                            replica, assessment,
                            onlyThis=onlyThis)
        return deck


class TrialHelper:
    _archive = None

    def __init__(self, root_path=None, trialsFolder=None):
        self._archive = BaaSArchive(root_path=root_path,
                                    trialsFolder=trialsFolder)

    def uploadTrialFile(self, trial, filepath):
        fileBits = filepath.split('/')
        filename = fileBits[-1]
        filepath = '/'.join(fileBits[:-1])
        filepath += '/'
        self._archive.uploadFile(filename,
                                 filepath,
                                 trial.code)
        trial.report_filename = '/'.join([trial.code, filename])
        trial.save()

    def createTrialFolder(self, fieldTrialFolder):
        self._archive.createFolder(fieldTrialFolder)


class PdfTrial:
    # pagesize=(595.27,841.89),
    _canvas = None
    _trial = None
    _width = 595
    _height = 841
    _margin = 25
    _buffer = None
    _filename = None

    _TABLE_STYLE_1 = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), "#CCCCCC"),
            ("TEXTCOLOR", (0, 0), (-1, 0), "#000000"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("BACKGROUND", (0, 1), (-1, -1), "#EEEEEE"),
            ("TEXTCOLOR", (0, 1), (-1, -1), "#000000"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("ALIGN", (0, 1), (-1, -1), "RIGHT")])
    _TABLE_STYLE_2 = TableStyle([
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 10)])

    def getName(self):
        if self._filename is None:
            self._filename = self._trial.code + '_trial.pdf'
        return self._filename

    def __init__(self, trial, useBuffer=False, folder='.'):
        self._trial = trial
        self._filename = self.getName()

        if useBuffer:
            self._buffer = BytesIO()
            persistor = self._buffer
        else:
            persistor = '/'.join([folder, self._filename])
        self._canvas = Canvas(persistor)

    def getBuffer(self):
        self._buffer.seek(0)
        return self._buffer

    def writeParagraph(self, texto, y, x=_margin,
                       styleName='Normal',
                       width=0):
        # styleSheet = getSampleStyleSheet()
        # style = styleSheet['BodyText']
        styles = getSampleStyleSheet()
        style = styles[styleName]
        paragraph = Paragraph(texto, style)

        return self.addToPage(paragraph, x, y, width)

    def toText(self, title, fields, exclude=[], includeItem=True):
        texto = ''
        if len(title) > 0:
            texto = '''<font size=20><strong>''' + title +\
                    '''</strong></font><br/>'''
        for item in fields:
            if item not in exclude:
                if includeItem:
                    texto += '''<strong>''' + item + ''' :</strong>   '''
                texto += str(fields[item])
                texto += '''<br/>'''
        return texto + '''<br/><br/>'''

    def selectPartOfTotal(self, data, part, total):
        newVector = {}
        fields = list(data.keys())
        totals = len(fields)
        block = int(totals / total)
        first = block * (part - 1)
        last = block * part if part < total else totals
        selected = fields[first:last]
        newVector = {item: data[item] for item in selected}
        return newVector

    def writeTrialData(self):
        # A4 : 210, 297 mm
        trialData = TrialModel.prepareDataItems(self._trial, asArray=True)
        self.writeParagraph(
            self.toText('Goal', trialData['Goal']), 800)
        (x, y) = self.writeParagraph(
            self.toText('Status', trialData['Status']), 350, 800)
        (x, y) = self.writeParagraph(
            self.toText('Protocol',
                        {**trialData['Report'], **trialData['Assessments']},
                        exclude=['Conclusion']), y)

        if (len(trialData['Report']['Conclusion']) > 0):
            (x, y) = self.writeParagraph(
                self.toText('Conclusion', trialData['Report'],
                            exclude=['Description', 'Evaluation Criteria'],
                            includeItem=False), y)
        self._canvas.showPage()

        # Second page
        self.writeParagraph(
            self.toText('Cultive', trialData['Cultive']), 800)
        (x, y1) = self.writeParagraph(
            self.toText('Location', trialData['Location']), 800, x=200)
        (x, y2) = self.writeParagraph(
            self.toText('Applications', trialData['Applications']), y1)
        layout1 = self.selectPartOfTotal(trialData['Layout'], 1, 2)
        (x, y3) = self.writeParagraph(
            self.toText('Layout', layout1), y1, x=200)
        layout2 = self.selectPartOfTotal(trialData['Layout'], 2, 2)
        (x, y4) = self.writeParagraph(
            self.toText('  ', layout2), y1, x=200)
        new_y = min([y2, y3, y4])
        return (x, new_y)

    def writeMainPage(self):
        (x, y) = self.writeParagraph(
            self._trial.code + ' Trial', 550, x=100,
            styleName='Title')
        self.writeParagraph(
            self._trial.name, y - 100, x=100,
            styleName='Heading2')
        self._canvas.showPage()

    def addToPage(self, block, x, y, width):
        if width == 0:
            aW = self._width - x - PdfTrial._margin
        else:
            aW = width
        w, h = block.wrap(aW, y)
        if w <= aW and h <= y:
            block.drawOn(self._canvas, x, y - h)
        else:
            self._canvas.showPage()
            return self.addToPage(block, PdfTrial._margin, self._height, width)
        return (x+w, y-h)

    def writeTable(self, data, y, x=_margin, width=0,
                   style=_TABLE_STYLE_1):
        table = Table(data)
        # Set the table style
        table.setStyle(style)
        return self.addToPage(table, x, y, width)

    def writeThesisData(self, y):
        (x, y) = self.writeParagraph(self.toText('Treatments', []), y)
        thesis, data = Thesis.getObjectsDisplay(self._trial, asArray=True)
        (x, y) = self.writeTable(data, y)
        return (x, y)

    def writeApplicationData(self, y):
        data = Application.getObjectsDisplay(self._trial)
        if len(data) < 2:
            return (PdfTrial._margin, y)
        (x, y) = self.writeParagraph(self.toText('Applications', []), y)
        (x, y) = self.writeTable(data, y)
        self._canvas.showPage()
        return (x, y)

    # def writeAssessmentInfo(self, y):
    #     data = Assessment.getObjectsDisplay(self._trial)
    #     if len(data) < 2:
    #         return (PdfTrial._margin, y)
    #     (x, y) = self.writeParagraph(self.toText('', []), y)
    #     (x, y) = self.writeTable(data, PdfTrial._margin, y)
    #     self._canvas.showPage()
    #     return (x, y)

    def produce(self):
        self.writeMainPage()
        (x, y) = self.writeTrialData()
        (x, y) = self.writeThesisData(y)
        (x, y) = self.writeApplicationData(y)
        self._canvas.showPage()
        # (x, y) = self.writeAssessmentInfo()

        self._canvas.save()
