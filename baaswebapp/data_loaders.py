'''
To create db execute this in python manage.py shell
from baaswebapp.data_loaders import TrialDbInitialLoader
TrialDbInitialLoader.loadInitialTrialValues()
'''
from baaswebapp.models import ModelHelpers, RateTypeUnit
from catalogue.models import Product, Vendor, Batch, \
    ProductVariant, DEFAULT, RateUnit, Treatment, UNTREATED
from trialapp.models import TrialType, TrialStatus, ApplicationMode, \
                            Objective, Plague, Crop, FieldTrial, \
                            Irrigation, CultivationMethod, CropVariety
from trialapp.data_models import ThesisData, ReplicaData, SampleData


class TrialDbInitialLoader:
    @classmethod
    def initialTrialModelValues(cls):
        return {
            TrialType: [ModelHelpers.UNKNOWN, 'Development',
                        'Commercial Demo', 'Registry', 'Technical Demo'],
            TrialStatus: [ModelHelpers.UNKNOWN, TrialStatus.OPEN,
                          'In Progress', 'Anual Recurrence',
                          TrialStatus.FINISHED, 'Imported'],
            Irrigation: [ModelHelpers.UNKNOWN, 'Dry', 'Manta',
                         'Aspersion', 'Drip', 'Hydroponic', 'Others'],
            ApplicationMode: [
                ModelHelpers.UNKNOWN, 'Foliar', 'Foliar Spray', 'Drench',
                'Fertigation', 'Seeder', 'Fertiliser', 'Specific',
                'Irrigation', 'Drip Irrigation'],
            Objective: [ModelHelpers.UNKNOWN, 'Fertilizer Reduction',
                        'Biological effectiveness'],
            Product: [ModelHelpers.UNKNOWN, 'Botrybel', 'ExBio', 'Beltanol',
                      'Belthirul',
                      'Biopron', 'Bulhnova', 'Canelys', 'ChemBio', 'Mimotem',
                      'Nemapron', 'Nutrihealth', 'Verticibel',
                      '-- No Product --'],
            CultivationMethod: [
                ModelHelpers.UNKNOWN, 'Open Air', 'Greenhouse', 'Netting'],
            RateUnit: ['Kg/hectare', 'Liters/hectare', DEFAULT, 'ml/l'],
            Vendor: [
                'Probelte', 'Syngenta', 'BASF', 'Corteva']
        }

    @classmethod
    def initialTrialModelComplexValues(cls):
        return {
            Crop: {
                ModelHelpers.UNKNOWN: {'other': None},
                'Agave': {'other': None},
                'Avocado': {'other': 'Aguacate'},
                'Strawberry': {'other': 'Fresa'},
                'Melon': {'other': None},
                'Watermelon': {'other': 'Sandia'},
                'Tomato': {'other': 'Tomate'},
                'Potato': {'other': 'Patata'},
                'Cotton': {'other': 'Algodon'},
                'Blackberry': {'other': 'Arandano'},
                'Corn': {'other': 'Maiz'},
                'Brocoli': {'other': None},
                'Citrics': {'other': 'Arandano'},
                'Onion': {'other': 'Cebolla'},
                'Raspberry': {'other': 'Frambuesa'},
                'Banan': {'other': 'Platano'},
                'Jitomate': {'other': None},
                'Chili': {'other': 'Chile'},
                'Pepper': {'other': 'Pimiento'},
                'Pumkin': {'other': 'Calabaza'},
                'Cucumber': {'other': 'Pepino'},
                'Cucurbit': {'other': 'Cucurbetacea'},
                'Grape': {'other': 'Uva'},
                'Olive': {'other': 'Olivo'},
                'Cauliflower': {'other': 'Coliflor'},
                'Lettuce': {'other': 'Lechuga'},
                'Apple': {'other': 'Manzana'},
                'Peach': {'other': 'Melocoton'},
                'Carrot': {'other': 'Zanahoria'}},
            CropVariety: {
                'Unknown': {'crop_id': 1}},
            Plague: {
                ModelHelpers.UNKNOWN: {'other': None},
                ModelHelpers.NOT_APPLICABLE: {'other': None},
                "Mites": {"other": "Acaros"},
                "Aguado/Citric Bacteriosis":
                    {"other": "Aguado/Bacteriosis Citricos"},
                "Alternary": {"other": "Alternaria"},
                "Anarsia/Grafolite": {"other": "Anarsia/Grafolita"},
                "Antilimacos": {"other": "Antilimacos"},
                "Anthracnosis": {"other": "Antracnosis"},
                "Botrytis": {"other": "Botrytis"},
                "Bremia": {"other": "Bremia"},
                "Bromine": {"other": "Bromo"},
                "Carpocapsa": {"other": "Carpocapsa"},
                "Cercospora": {"other": "Cercospora"},
                "CLADOSPORIOSIS (Fulvia Fulva)":
                    {"other": "Cladosporiosis (Fulvia Fulva)"},
                "Cochinillas": {"other": "Cochinillas"},
                "Unbrotaries": {"other": "Desbrotadores"},
                "Desiccants/defoliant": {"other": "Desecantes/Defoliantes"},
                "Nascence diseases": {"other": "Enfermedades De Nascencia"},
                "Eriofidos": {"other": "Eriofidos"},
                "Potato beetle": {"other": "Escarabajo De La Patata"},
                "Soil fertilizers": {"other": "Fertilizantes Suelo"},
                "Fitor regulators": {"other": "Fitorreguladores"},
                "Heliothis spp.": {"other": "Heliothis spp."},
                "Contact herbicides": {"other": "Herbicidas De Contacto"},
                "Residual herbicides": {"other": "Herbicidas Residuales"},
                "Cereal fungi": {"other": "Hongos Cereal"},
                "Seed fungi": {"other": "Hongos De Semilla"},
                "Soil fungi": {"other": "Hongos De Suelo"},
                "Fungi in general": {"other": "Hongos En General"},
                "Fungi winter prefloration":
                    {"other": "Hongos Invierno Prefloracion"},
                "Ants": {"other": "Hormigas"},
                "Soil insects": {"other": "Insectos De Suelo"},
                "Funeral (cyperus)": {"other": "Juncia (Cyperus)"},
                "Locust": {"other": "Langosta"},
                "Lava salts": {"other": "Lava Sales"},
                "Lepidopteros": {"other": "Lepidopteros"},
                "Leprosy": {"other": "Lepra"},
                "Dicotyledoneas weeds":
                    {"other": "Malas Hierbas Dicotiledoneas"},
                "Pest mixture": {"other": "Mezcla De Plagas"},
                "Mildew": {"other": "Mildiu"},
                "Leaf minators": {"other": "Minadores De Hojas"},
                "Mojantes": {"other": "Mojantes"},
                "Mollusquicides": {"other": "Molusquicidas"},
                "Moniliosis": {"other": "Moniliosis"},
                "White fly": {"other": "Mosca Blanca"},
                "Fruit fly": {"other": "Mosca De La Fruta"},
                "Olive fly": {"other": "Mosca Del Olivo"},
                "Mottled": {"other": "Moteado"},
                "Mycosphaerella (in general)":
                    {"other": "Mycosphaerella (en general)"},
                "Bold": {"other": "Negrilla"},
                "Beet thumb": {"other": "Pulguilla De La Remolacha"},
                "Pyricularia Oryzae": {"other": "Pyricularia Oryzae"},
                "Olive repilement": {"other": "Repilo Del Olivo"},
                "Rhizoctonia": {"other": "Rhizoctonia"},
                "Royas": {"other": "Royas"},
                "Sclerotinia": {"other": "Sclerotinia"},
                "Septoria": {"other": "Septoria"},
                "Stempphylium vesicarium": {"other": "Stemphylium Vesicarium"},
                "Drill of the corn": {"other": "Taladro Del Maiz"},
                "Post harvest treatments":
                    {"other": "Tratamientos Post Cosecha"},
                "Trips": {"other": "Trips"},
                "Absolute tutta": {"other": "Tutta Absoluta"},
                "Vallico (Lolium)": {"other": "Vallico (Lolium)"},
                "YESCA DE LA VID": {"other": "Yesca De La Vid"}},
            RateTypeUnit: {
                ModelHelpers.UNKNOWN: {'unit': ModelHelpers.UNKNOWN},
                'PESINC': {'unit': 'NUMBER'},
                'PESSEV': {'unit': 'Range 0-5'},
                'PLANT LENGHT': {'unit': 'cm'}}}

    # Use location='shhtunnel_db'
    @classmethod
    def loadInitialTrialValues(cls, location='default'):
        initialValues = cls.initialTrialModelValues()
        for modelo in initialValues:
            for value in initialValues[modelo]:
                if modelo.objects.filter(name=value).exists():
                    continue
                thisObj = {'name': value}
                theObject = modelo(**thisObj)
                theObject.save(using=location)

        initialValues = cls.initialTrialModelComplexValues()
        for modelo in initialValues:
            for name in initialValues[modelo]:
                if modelo.objects.filter(name=name).exists():
                    continue
                values = initialValues[modelo][name]
                thisObj = {key: values[key] for key in values}
                thisObj['name'] = name

                theObject = modelo(**thisObj)
                theObject.save(using=location)

        # Created untreated product, batch, etc...
        defaultRateUnit = RateUnit.objects.get(name=DEFAULT)
        noproduct = Product.objects.create(name=UNTREATED)
        novariant = ProductVariant.objects.create(product=noproduct,
                                                  name=DEFAULT)
        nobatch = Batch.objects.create(name=DEFAULT,
                                       rate=0, rate_unit=defaultRateUnit,
                                       product_variant=novariant)
        Treatment.objects.create(name=UNTREATED, batch=nobatch,
                                 rate=0, rate_unit=defaultRateUnit)


class TrialStats:
    @classmethod
    def getGeneralStats(cls):
        points = ThesisData.objects.count() +\
                 ReplicaData.objects.count() +\
                 SampleData.objects.count()
        return {
            'products': Product.objects.count(),
            'field_trials': FieldTrial.objects.filter(
                trial_meta=FieldTrial.TrialMeta.FIELD_TRIAL).count(),
            'lab_trials': FieldTrial.objects.filter(
                trial_meta=FieldTrial.TrialMeta.LAB_TRIAL).count(),
            'points': points}
