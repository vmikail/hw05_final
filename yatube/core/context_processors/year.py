import datetime


def year(request):
    now = datetime.datetime.now()
    year = now.year
    return {
        'year': year
    }
