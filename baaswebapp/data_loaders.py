'''
To create db execute this in python manage.py shell
from baaswebapp.data_loaders import TrialDbInitialLoader
TrialDbInitialLoader.loadInitialTrialValues()
'''
from baaswebapp.models import ModelHelpers
from catalogue.models import Product, ProductCategory, Vendor
from trialapp.models import TrialType, TrialStatus, ApplicationMode,\
                            Project, Objective, RateUnit, AssessmentType,\
                            AssessmentUnit, Plague, Crop, FieldTrial,\
                            Irrigation, CultivationMethod, CropVariety
from trialapp.data_models import ThesisData


class TrialDbInitialLoader:
    @classmethod
    def initialTrialModelValues(cls):
        return {
            TrialType: [ModelHelpers.UNKNOWN, 'Development',
                        'Commercial Demo', 'Registry', 'Demand Generation'],
            TrialStatus: [ModelHelpers.UNKNOWN, 'Open', 'In Progress',
                          'Anual Recurrence', 'Close'],
            Irrigation: [ModelHelpers.UNKNOWN, 'Dry', 'Manta',
                         'Aspersion', 'Drip', 'Hydroponic', 'Others'],
            ApplicationMode: [
                ModelHelpers.UNKNOWN, 'Foliar', 'Foliar Spray', 'Drench',
                'Fertigation', 'Seeder', 'Fertiliser', 'Specific',
                'Irrigation', 'Drip Irrigation'],
            Project: [ModelHelpers.UNKNOWN, 'Botrybel', 'ExBio', 'Beltanol',
                      'Belthirul',
                      'Biopron', 'Bulhnova',
                      'Nemapron', 'Nutrihealth', 'Verticibel'],
            Objective: [ModelHelpers.UNKNOWN, 'Fertilizer Reduction',
                        'Biological effectiveness'],
            Product: [ModelHelpers.UNKNOWN, 'Botrybel', 'ExBio', 'Beltanol',
                      'Belthirul',
                      'Biopron', 'Bulhnova', 'Canelys', 'ChemBio', 'Mimotem',
                      'Nemapron', 'Nutrihealth', 'Verticibel',
                      '-- No Product --'],
            CultivationMethod: [
                ModelHelpers.UNKNOWN, 'Open Air', 'Greenhouse', 'Netting'],
            RateUnit: ['Kg/hectare', 'Liters/hectare'],
            AssessmentUnit: [
                '%; 0; 100', '%UNCK; -; -', 'Fruit Size',
                'Number', 'SPAD', 'Kilograms', 'Meters',
                'EWRS;1;9', 'Severity;0;5'],
            AssessmentType: [
                '# Galls', '# Nematodes', 'P-phosphate',
                'K-Potassium', 'Fruit firmness', '°Brix',
                'Fruit size', 'Yield', 'Fruit weight',
                'N-Nitrogen', 'Greenness', 'Plant height',
                'CONTRO', 'PESINC', 'PESSEV', 'PHYGEN'],
            ProductCategory: [
                'Fertilizers', 'Pest Control', 'Herbicide', 'Fungicide',
                'Other'],
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
                'Unknown': {'crop_id': 1}
            },
            Plague: {
                ModelHelpers.UNKNOWN: {'other': None},
                "Mites": {"other": "Acaros"},
                "Aguado/Citric Bacteriosis":
                    {"other": "Aguado/Bacteriosis Citricos"},
                "Alternary": {"other": "Alternaria"},
                "Anarsia/Grafolite": {"other": "Anarsia/Grafolita"},
                "Antilimacos": {"other": "Antilimacos"},
                "Anthracnosis": {"other": "Antracnosis"},
                "Crazy oat (oats)": {"other": "Avena Loca (Avena)"},
                "Bacteriosis": {"other": "Bacteriosis"},
                "Barrenadores": {"other": "Barrenadores"},
                "Biofertilization": {"other": "BioFertilizacion"},
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
                "Insects in general": {"other": "Insectos En General"},
                "Insects stored grains":
                    {"other": "Insectos Granos Almacenados"},
                "Winter insects prefloration":
                    {"other": "Insectos Invierno Prefloracion"},
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
                "Nematodes": {"other": "Nematodos"},
                "Oidio": {"other": "Oidio"},
                "Other deficiencies": {"other": "Otras Carencias"},
                "Other wooden diseases":
                    {"other": "Otras Enfermedades De La Madera"},
                "Other gramineas weeds":
                    {"other": "Otras Malas Hierbas Gramineas"},
                "Paulilla/Paulillon": {"other": "Paulilla/Paulillon"},
                "Phytophthora citrus": {"other": "Phytophthora Citricos"},
                "Piral de la Vid": {"other": "Piral De La Vid"},
                "Cluster moth": {"other": "Polilla Del Racimo"},
                "Prays Citri": {"other": "Prays Citri"},
                "Prays del Olivo": {"other": "Prays Del Olivo"},
                "Psyla": {"other": "Psyla"},
                "Aphids": {"other": "Pulgones"},
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
                "YESCA DE LA VID": {"other": "Yesca De La Vid"}}}

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


class TrialStats:
    @classmethod
    def getGeneralStats(cls):
        return {
            'products': Product.objects.count(),
            'field_trials': FieldTrial.objects.count(),
            'points': ThesisData.objects.count()}
