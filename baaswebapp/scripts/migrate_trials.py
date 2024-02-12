from catalogue.models import Product
from trialapp.models import FieldTrial


def run(*args):
    if len(args) != 2:
        print("Usage: python manage.py runscript migrate_trials --script-args <fromProdId> <toProdId>")
        return

    fromProdId = int(args[0])
    toProdId = int(args[1])

    trials = FieldTrial.objects.filter(product=fromProdId)

    for trial in trials:
        trial.product = Product.objects.get(id=toProdId)
        trial.save()

    print(f"Successfully migrated trials from product {fromProdId} to {toProdId}")