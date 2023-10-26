from trialapp.data_models import Assessment
from baaswebapp.baas_archive import BaaSArchive
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, Table, TableStyle
from trialapp.models import\
    FieldTrial, Thesis, Objective, Replica, \
    Product, ApplicationMode, StatusTrial, TrialType, Crop, CropVariety, \
    Plague, CultivationMethod, Irrigation, Application, SoilType
from trialapp.data_models import ReplicaData
from catalogue.models import RateUnit
from django import forms
from io import BytesIO
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render


class TrialModel():
    T_D = 'TypeDate'
    T_I = 'TypeInteger'
    T_N = 'TypeNoChange'
    T_T = 'TypeText'
    FIELDS = {
        'Goal': {
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
            'initiation_date': {'label': 'Started', 'required': True,
                                'type': T_D},
            'public': {'label': "public",
                       'required': False, 'type': T_N},
            'status_trial': {'label': 'Status', 'required': True, 'type': T_N,
                             'cls': StatusTrial},
            'completion_date': {'label': 'Completed by', 'required': False,
                                'type': T_D},
            'favorable': {'label': "Favorable",
                          'required': False, 'type': T_N},
            'responsible': {'label': 'Responsible', 'required': True,
                            'type': T_N},
        },
        'Report': {
            'description': {
                'label': "Description", 'required': False,
                'type': T_T, 'rows': 10},
            'description_en': {
                'label': "Description EN", 'required': False,
                'type': T_T, 'rows': 10},
            'comments_criteria': {
                'label': "Evaluation Criteria",
                'required': False, 'type': T_T, 'rows': 5},
            'comments_criteria_en': {
                'label': "Evaluation Criteria EN",
                'required': False, 'type': T_T, 'rows': 5},
            'conclusion': {
                'label': "Conclusion", 'required': False,
                'type': T_T, 'rows': 10},
            'conclusion_en': {
                'label': "Conclusion EN", 'required': False,
                'type': T_T, 'rows': 10},

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
            'soil': {'label': _('Soil'), 'required': False,
                     'type': T_N, 'cls': SoilType},
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
            'repetitions': {'label': "# repetitions", 'required': True,
                            'type': T_I},
            'samples_per_replica': {'label': "# samples/repetition",
                                    'required': False, 'type': T_I},
            'number_rows': {'label': "# rows", 'required': False, 'type': T_I},
            'gross_surface': {'label': "Gross area plot (m2)",
                              'required': False, 'type': T_N},
            'net_surface': {'label': "Net area plot (m2)", 'required': False,
                            'type': T_N},
            'lenght_row': {'label': "Row length (m)", 'required': False,
                           'type': T_N},
            'distance_between_rows': {'label': "Rows separation",
                                      'required': False, 'type': T_N},
            'distance_between_plants': {'label': "Plants separation",
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
            'code',
            'product', 'crop', 'plague', 'initiation_date', 'completion_date',
            'status_trial', 'contact', 'repetitions',
            'samples_per_replica')

    FIELD_TRIAL_FIELDS = (
            'name', 'trial_type', 'objective', 'responsible', 'description',
            'ref_to_eppo', 'ref_to_criteria', 'comments_criteria',
            'product', 'crop', 'plague', 'initiation_date', 'completion_date',
            'status_trial', 'contact', 'cro', 'location',
            'repetitions', 'samples_per_replica',
            'distance_between_plants', 'distance_between_rows', 'number_rows',
            'lenght_row', 'net_surface', 'gross_surface', 'code', 'irrigation',
            'application_volume', 'mode', 'crop_variety', 'cultivation',
            'crop_age', 'seed_date', 'transplant_date', 'longitude',
            'latitude', 'application_volume_unit', 'conclusion', 'soil',
            'favorable', 'public', 'description_en', 'conclusion_en',
            'comments_criteria_en')

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
                    trialForm.fields[field].widget = forms.DateInput(
                        format=('%Y-%m-%d'),
                        attrs={'class': 'form-control',
                               'type': 'date'})
                    trialForm.fields[field].show_hidden_initial = True
                elif typeField == TrialModel.T_I:
                    trialForm.fields[field].widget = forms.NumberInput()
                elif typeField == TrialModel.T_T:
                    trialForm.fields[field].widget = forms.Textarea(
                        attrs={'rows': fieldData['rows']})
        # Querysets
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
        if 'irrigation' in trialForm.fields:
            trialForm.fields['irrigation'].queryset = Irrigation.getObjects()

    @classmethod
    def showValue(cls, field, trial, trialDict, group):
        value = '?'
        if field == 'status_trial':
            value = trial.get_status_trial_display()
        elif field == 'soil':
            value = trial.get_soil_display()
        elif field in trialDict:
            value = trialDict[field]
        else:
            field_id = field + '_id'
            if field_id in trialDict:
                theId = trialDict[field_id]
                if theId is not None:
                    model = TrialModel.FIELDS[group][field]['cls']
                    value = model.objects.get(id=theId)
        return value if value is not None else '?'

    @classmethod
    def prepareDataItems(cls, trial, asArray=False):
        trialDict = trial.__dict__
        trialData = {}
        if trial.trial_meta == FieldTrial.TrialMeta.LAB_TRIAL:
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
                showValue = cls.showValue(field, trial, trialDict, group)
                if asArray:
                    trialData[group][label] = showValue
                else:
                    trialData[group].append({'name': label,
                                             'value': showValue})
        return trialData


class LayoutTrial:
    @classmethod
    def calculateLayoutDim(cls, fieldTrial, numberThesis):
        return fieldTrial.repetitions, numberThesis

    @classmethod
    def computeInitialLayout(cls, fieldTrial, numberThesis):
        columns, rows = LayoutTrial.calculateLayoutDim(
            fieldTrial, numberThesis)
        deck = [[LayoutTrial.setDeckCell(None, x=i+1, y=j+1)
                 for i in range(0, columns)] for j in range(0, rows)]
        return deck, (columns, rows)

    @classmethod
    def setDeckCell(cls, replica: Replica,
                    x=0, y=0,
                    value=None,
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
                    'value': value}

    @classmethod
    def headerLayout(cls, fieldTrial: FieldTrial):
        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I',
                   'J', 'K', 'L', 'M', 'N']
        header = []
        for i in range(0, fieldTrial.repetitions):
            header.append({'name': letters[i],
                           'replica_id': 0,
                           'number': 0})
        return header

    @classmethod
    def showLayout(cls, fieldTrial: FieldTrial, thesisTrial,
                   onlyThis=None, valuesReplica=None):
        deck, (rows, columns) = LayoutTrial.computeInitialLayout(
            fieldTrial, len(thesisTrial))
        # Place the thesis in the deck
        for thesis in thesisTrial:
            for replica in Replica.getObjects(thesis):
                if (replica.pos_x > 0) and (replica.pos_y > 0) and\
                   (replica.pos_x <= rows) and (replica.pos_y <= columns):
                    value = valuesReplica.get(replica.name, None) \
                        if valuesReplica else None
                    deck[replica.pos_y-1][replica.pos_x-1] =\
                        LayoutTrial.setDeckCell(
                            replica,
                            value=value,
                            onlyThis=onlyThis)
        return deck


class TrialFile:
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
    _page_start = 800

    _TABLE_STYLE_1 = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), "#CCCCCC"),
            ("TEXTCOLOR", (0, 0), (-1, 0), "#000000"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
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
            ("FONTSIZE", (0, 0), (-1, 0), 8),
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
        styles = getSampleStyleSheet()
        style = styles[styleName]
        paragraph = Paragraph(texto, style)

        return self.addToPage(paragraph, x, y, width)

    def toText(self, title, fields, exclude=[], includeItem=True):
        texto = ''
        if len(title) > 0:
            texto = '''<font size=20><br/><strong>''' + title +\
                    '''</strong><br/></font><br/>'''
        for item in fields:
            if item not in exclude:
                if includeItem:
                    texto += '''<strong>''' + item + ''' :</strong>   '''
                texto += str(fields[item])
                texto += '''<br/>'''
        if len(fields) > 1:
            texto += '''<br/>'''
        return texto

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
            self.toText('Goal', trialData['Goal']), self._page_start)
        (x, y) = self.writeParagraph(
            self.toText('Status', trialData['Status']), self._page_start,
            x=350)
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
        (x, y0) = self.writeParagraph(
            self.toText('Cultive', trialData['Cultive']), self._page_start)
        (x, y1) = self.writeParagraph(
            self.toText('Location', trialData['Location']), self._page_start,
            x=250)
        y1 = min([y0, y1])
        (x, y2) = self.writeParagraph(
            self.toText('Applications', trialData['Applications']), y1)
        layout1 = self.selectPartOfTotal(trialData['Layout'], 1, 2)
        (x, y3) = self.writeParagraph(
            self.toText('Layout', layout1), y1, x=250)
        layout2 = self.selectPartOfTotal(trialData['Layout'], 2, 2)
        (x, y4) = self.writeParagraph(
            self.toText('  ', layout2), y1, x=400)
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
                   style=_TABLE_STYLE_2, colums_align_right=1):
        table = Table(data)
        # Set the table style
        table.setStyle(TableStyle([
            ("ALIGN", (colums_align_right, 1), (-1, -1), "RIGHT")]))
        return self.addToPage(table, x, y, width)

    def writeThesisData(self, y):
        (x, y) = self.writeParagraph(self.toText('Treatments', []), y)
        thesis, data = Thesis.getObjectsDisplay(self._trial, asArray=True)
        (x, y) = self.writeTable(data, y, colums_align_right=2)
        return (x, y)

    def writeApplicationData(self, y):
        data = Application.getObjectsDisplay(self._trial)
        if len(data) < 2:
            return (PdfTrial._margin, y)
        (x, y) = self.writeParagraph(self.toText('Applications', []), y)
        (x, y) = self.writeTable(data, y)
        self._canvas.showPage()
        return (x, y)

    def prepareHeader(self, assessList):
        partRatedArr = ['Part Rated', '', '']
        bbchArr = ['BBCH', '', '']
        names = ['Name/Interval', '', '']
        dates = ['Date', '', '']
        rating = ['Rating (Unit)', '', '']
        for ass in assessList:
            names.append(ass.name)
            dates.append(ass.assessment_date.isoformat())
            rating.append(ass.rate_type.getName())
            partRated = ass.part_rated
            if partRated == 'Undefined' or partRated == 'None':
                partRated = ''
            partRatedArr.append(partRated)
            bbch = ass.crop_stage_majority
            if bbch == 'Undefined' or bbch == 'None':
                bbch = ''
            bbchArr.append(bbch)
        return [dates, rating, bbchArr, partRatedArr, names]

    def selectAssmts(self, assmts):
        assmtsLists = []
        index = 0
        assmtsList = []
        for assmt in assmts:
            assmtsList.append(assmt)
            if index == 2:
                assmtsLists.append(assmtsList)
                assmtsList = []
                index = 0
            else:
                index += 1
        if len(assmtsList) > 0:
            assmtsLists.append(assmtsList)
        return assmtsLists

    def writeAssessmentInfo(self, y):
        (x, y) = self.writeParagraph(self.toText('Assessments', []), y)
        assmts = Assessment.getObjects(self._trial)
        references = Replica.getFieldTrialObjects(self._trial)
        assmtsLists = self.selectAssmts(assmts)

        for block in assmtsLists:
            data = self.prepareHeader(block)
            replicaData = {}
            lastThesisId = None
            for item in references:
                if item.thesis_id != lastThesisId:
                    thesis = item.thesis
                    values = [thesis.number, thesis.name]
                    lastThesisId = thesis.id
                else:
                    values = ['', '']
                values.append(item.number)
                replicaData[item.id] = values
            for assmt in block:
                dataPoints = ReplicaData.getDataPoints(assmt)
                for reference in references:
                    for dataPoint in dataPoints:
                        if dataPoint.reference.id == reference.id:
                            replicaData[reference.id].append(dataPoint.value)
                            break
            for row in list(replicaData.values()):
                data.append(row)
            (x, y) = self.writeTable(data, y, colums_align_right=2)
        return (x, y)

    def produce(self):
        self.writeMainPage()
        (x, y) = self.writeTrialData()
        (x, y) = self.writeThesisData(y)
        (x, y) = self.writeApplicationData(y)
        self._canvas.showPage()
        (x, y) = self.writeAssessmentInfo(self._page_start - 50)
        self._canvas.save()


class TrialPermission:
    _trial = None
    _user = None
    _permissions = {}
    _type = None
    _owner = False
    _status = None
    _isDone = None

    # --- Permissions
    # Can change any status and data
    EDITABLE = 'edit_trial_perm'
    # Can access trial
    READIBLE = 'read_trial'
    # Can find trial and see internal values (status, owner)
    DISCOVERABLE = 'discover_trial'
    # Can download status
    DOWNLOADABLE = 'download_trial'
    # Can clone status
    CLONABLE = 'clone_trial'

    # --- Type users
    EXTERNAL = 'ext'
    INTERNAL = 'int'
    ADMIN = 'adm'

    def __init__(self, trial, user):
        self._trial = trial
        self._user = user
        self.getType()
        if trial:
            self.isOwner()
            self.isDone()
            self.setPermissions()

    def getType(self):
        self._type = TrialPermission.EXTERNAL
        if self._user.is_superuser:
            self._type = TrialPermission.ADMIN
        elif self._user.is_staff:
            self._type = TrialPermission.INTERNAL

    def isOwner(self):
        self._owner = self._trial.responsible == self._user.username

    def isDone(self):
        self._isDone = self._trial.status_trial == StatusTrial.DONE

    def setPermissions(self):
        self._permissions = {
            TrialPermission.EDITABLE: False,
            TrialPermission.READIBLE: False,
            TrialPermission.DISCOVERABLE: False,
            TrialPermission.DOWNLOADABLE: False,
            TrialPermission.CLONABLE: False}
        if self.setDiscover():
            if self.setRead():
                self.setDownload()
                self.setEdit()
                self.setClone()

    def canDiscover(self):
        return self._permissions[TrialPermission.DISCOVERABLE]

    def setDiscover(self):
        permit = False
        if self._owner or self._type == TrialPermission.ADMIN or \
           self._type == TrialPermission.INTERNAL:
            permit = True
        elif self._type == TrialPermission.EXTERNAL:
            if self._trial.public and self._isDone:
                permit = True
        self._permissions[TrialPermission.DISCOVERABLE] = permit
        return permit

    def canRead(self):
        return self._permissions[TrialPermission.READIBLE]

    def setRead(self):
        permit = False
        if self._owner or self._type == TrialPermission.ADMIN:
            permit = True
        elif self._type == TrialPermission.INTERNAL:
            if self._isDone:
                permit = True
        elif self._type == TrialPermission.EXTERNAL:
            if self._isDone and self._trial.public:
                permit = True
        self._permissions[TrialPermission.READIBLE] = permit
        return permit

    def canDownload(self):
        return self._permissions[TrialPermission.DOWNLOADABLE]

    def setDownload(self):
        permit = False
        if self._type == TrialPermission.ADMIN:
            permit = True
        elif self._type == TrialPermission.INTERNAL:
            if self._isDone and self._trial.favorable:
                permit = True
        elif self._type == TrialPermission.EXTERNAL:
            if self._isDone and self._trial.favorable and self._trial.public:
                permit = True
        self._permissions[TrialPermission.DOWNLOADABLE] = permit
        return permit

    def setClone(self):
        permit = False
        if self._type == TrialPermission.ADMIN:
            permit = True
        elif self._owner:
            permit = True

        self._permissions[TrialPermission.CLONABLE] = permit
        print(f"Is Clonable = {self._permissions[TrialPermission.CLONABLE]}")
        return permit

    def canClone(self):
        return self._permissions[TrialPermission.CLONABLE]

    def canEdit(self):
        return self._permissions[TrialPermission.EDITABLE]

    def setEdit(self):
        permit = False
        if self._type == TrialPermission.ADMIN:
            permit = True
        elif self._owner and not self._isDone:
            permit = True
        self._permissions[TrialPermission.EDITABLE] = permit
        return permit

    def getPermisions(self):
        return self._permissions

    def getError(self):
        if not self._permissions[TrialPermission.READIBLE] or \
           not self._permissions[TrialPermission.DISCOVERABLE]:
            return _('You do not have permission to access this trial')
        elif not self._permissions[TrialPermission.DOWNLOADABLE]:
            return _('You do not have permission to download this trial')
        elif not self._permissions[TrialPermission.EDITABLE]:
            return _('You do not have permission to edit this trial')
        elif not self._permissions[TrialPermission.CLONABLE]:
            return _('You do not have permissions to clone this trial')
        return _('No limitations on permissions')

    def renderError(self, request, error=None):
        if error is None:
            error = self.getError()
        return render(request, 'baaswebapp/show_permission_error.html',
                      {'error': error})
