from datetime import date
from dateutil.relativedelta import relativedelta
import calendar


class BaaSHelpers:
    @staticmethod
    def lastXMonthDateIso(months, iso=True, makeFirstDayOfTheMonth=True):
        lastMonthDay = (date.today() - relativedelta(months=months))
        if makeFirstDayOfTheMonth:
            lastMonthDay = lastMonthDay.replace(day=1)
        return lastMonthDay.isoformat() if iso else lastMonthDay

    @staticmethod
    def monthNameFromInt(theMonthInt,  full=False):
        if full:
            return calendar.month_name[int(theMonthInt)]
        else:
            return calendar.month_abbr[int(theMonthInt)]

    @staticmethod
    def getLastMonthsInOrder(numberMonths, includeCurrent=True):
        firstLastMonth = BaaSHelpers.lastXMonthDateIso(numberMonths,
                                                       iso=False)
        numberMonthsToIndex = numberMonths+1 if includeCurrent\
            else numberMonths
        months = [BaaSHelpers.monthNameFromInt(
            (firstLastMonth+relativedelta(months=+monthIndex)).month)
            for monthIndex in range(0, numberMonthsToIndex)]
        return months

    @staticmethod
    def nextXDays(nextDays, fromDay=None):
        if fromDay is None:
            fromDay = date.today()
        return [fromDay+relativedelta(days=+index)
                for index in range(0, nextDays)]
