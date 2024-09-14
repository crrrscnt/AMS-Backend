from django.http import HttpResponse, HttpResponseNotFound, Http404
from django.shortcuts import render, redirect
from django.urls import reverse

from datetime import datetime, date

menu = [{'title': "Главная", 'url_name': 'home'}]

services_db = [
    {'id': 1, 'title': 'Венера', 'mission': 'VERITAS', 'content': 'Ожидается, что VERITAS (лат. «истина») будет изучать внутреннюю эволюцию и поверхность Венеры. VERITAS (Venus Emissivity, Radio Science, InSAR, Topography, and Spectroscopy).',
     'start': date(2031, 1, 1),
     'price': 2000000},
    {'id': 2, 'title': 'Титан', 'mission': 'Dragonfly', 'content': 'Двойной квадрокоптер будет исследовать различные места на спутнике Сатурна Титане на предмет возможной пригодности для жизни.',
     'start': date(2027, 1, 1),
     'price': 4000000},
    {'id': 3, 'title': 'Марс', 'mission': 'SpaceX', 'content': 'Руководитель компании SpaceX, которая производит космическую технику, Илон Маск (Elon Musk) объявил о том, что дата запуска первой миссии на Марс их компании запланирована на время открытия ближайшего стартового (трансферного) окна «Земля-Марс». Такой временной период начнётся в ноябре 2026 года и на его протяжении может быть осуществлено до восьми беспилотных миссий Starhip на Красную планету.',
     'start': date(2029, 1, 1),
     'price': 2500000},
    {'id': 4, 'title': 'Европа', 'mission': 'Europa Clipper', 'content': 'Ожидается, что Европа будет исследовать спутник Юпитера с таким же названием во время серии пролетов. В его задачи входит изучение ледяного панциря Луны и океана, а также его состава и геологии.',
     'start': date(2024, 10, 1),
     'price': 10000000},
]


orders = []
orders_test = [
    {'id': 1, 'title': 'Венера', 'mission': 'VERITAS',  'content': 'Ожидается, что VERITAS (также по-латыни «истина») будет изучать внутреннюю эволюцию и поверхность Венеры. VERITAS (Venus Emissivity, Radio Science, InSAR, Topography, and Spectroscopy).',
     'start': date(2031, 1, 1), 'price': 2000000,
     'created': date(2024, 9, 12), 'status': 'Черновик'},
    {'id': 2, 'title': 'Титан', 'mission': 'Dragonfly', 'content': 'Двойной квадрокоптер будет исследовать различные места на спутнике Сатурна Титане на предмет возможной пригодности для жизни.',
     'start': date(2027, 1, 1), 'price': 4000000,
     'created': date(2024, 9, 12), 'status': 'Черновик'},
    {'id': 3, 'title': 'Марс', 'mission': 'SpaceX', 'content': 'Руководитель компании SpaceX, которая производит космическую технику, Илон Маск (Elon Musk) объявил о том, что дата запуска первой миссии на Марс их компании запланирована на время открытия ближайшего стартового (трансферного) окна «Земля-Марс». Такой временной период начнётся в ноябре 2026 года и на его протяжении может быть осуществлено до восьми беспилотных миссий Starhip на Красную планету.',
     'start': date(2029, 1, 1), 'price': 2500000,
     'created': date(2024, 9, 12), 'status': 'Черновик'},
]
#     {'id': 4, 'title': 'Венера', 'mission': 'DAVINCI',  'content': 'Зонд DAVINCI (Исследование благородных газов, химии и визуализации в глубокой атмосфере Венеры) будет исследовать атмосферу Венеры.',
#      'start': date(2029, 6, 1), 'price': 2000000,
#      'created': date(2024, 9, 12), 'status': 'Черновик'},

def index(request):
    number_of_services = len(orders_test)            # orders_test -> orders
    search_query = request.GET.get('search_query', '')
    if search_query == '' or search_query == 'Поиск':
        filtered_data = services_db
        search_query = 'Поиск'
    else:
        filtered_data = [item for item in services_db if
                         search_query.lower() in item['content'].lower()]
    data = {'title': 'Услуги АМС',
            'menu': menu,
            'posts': filtered_data,
            'count': number_of_services,
            'search_query': search_query,
    }
    return render(request, 'index.html', context=data)

def add_to_order(request, service_id):
    temp_dict = []
    for d in services_db:
        if d['id'] == service_id:
            temp_dict = d
            temp_dict['created'] = date.today()
            temp_dict['status'] = 'Черновик'
            orders.append(temp_dict)
    return redirect('order')


def order_view(request):
    number_of_services = len(orders_test)   # orders_test -> orders
    data = {
        'title': 'АМС',
        'menu': menu,
        'orders': orders_test,              # orders_test -> orders
        'count': number_of_services,
    }
    return render(request, 'order.html', context=data)


def detail(request, detail_id):
    # if detail_id > order_length:
    #     return redirect('/')
    for d in services_db:
        if d['id'] == detail_id:
            return render(request, 'detail.html',
                          {'id': d['id'], 'content': d['content'],
                           'target': d['title'],'title': 'Детали', 'menu': menu,
                           'cost': d['price']})
    return render(request, 'detail.html', {'content': ''})


def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>Страница не найдена.</h1>")
