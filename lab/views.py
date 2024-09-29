from random import choices

from django.http import HttpResponseRedirect, HttpResponseNotFound, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import connection
from lab.models import SpaceObject, UncrewedSpacecraft, Flight

from datetime import date, datetime

menu = [{'title': "Главная", 'url_name': 'home'}]


# @login_required
def index(request):
    services_list = []
    draft_request = UncrewedSpacecraft.get_draft_request(request.user)
    ais_flights = Flight.objects.filter(uncrewed_spacecraft=draft_request)
    num_objects = ais_flights.count()
    no_click = ''
    if num_objects == 0:
        no_click = 'class = "no-click"'
    space_object = request.GET.get('space_object', '')

    if space_object == '': #  or object_search == 'Поиск'
        services = SpaceObject.objects.filter(is_active=True).values(
            'id',
            'name',
            'uncrewed_spacecraft',
            'description',
            'price',
            'scheduled_at',
            'image_url'
        )
        #object_search = 'Поиск'
    else:
        services = SpaceObject.objects.filter(
            is_active=True,
            name__icontains=space_object
        ).values(
            'id',
            'name',
            'uncrewed_spacecraft',
            'description',
            'price',
            'scheduled_at',
            'image_url'
        )

    for service in services:
        services_list.append(service)

    data = {'title': 'Услуги АМС',
            'menu': menu,
            'no_click': no_click,
            'space_objects': services_list,
            'space_object': space_object,
            # 'flight_request': flight_request,
            'num_objects': num_objects,
            'draft_request': draft_request,
            # 'draft_count': draft_request.space_objects.count() if draft_request else 0
            }
    return render(request, 'index.html', context=data)


# @login_required
def detail(request, detail_id):
    space_object = get_object_or_404(SpaceObject, id=detail_id)
    draft_request = UncrewedSpacecraft.get_draft_request(request.user)

    if request.method == 'POST':
        if not draft_request:
                 # Если нет черновой заявки, создаем новую
            draft_request = UncrewedSpacecraft.objects.create(user=request.user,
                                                              status='draft')
            # Проверяем, существует ли уже связь между заявкой и объектом
        if not Flight.objects.filter(uncrewed_spacecraft=draft_request,
                                             space_object=space_object).exists():
                 # Добавляем космический объект в заявку
            Flight.objects.create(uncrewed_spacecraft=draft_request,
                                          space_object=space_object,
                                          create_date=date.today())

        return HttpResponseRedirect(reverse('order_detail', args=[draft_request.id]))


    data = {
        'menu': menu,
        'space_object': space_object,
        # 'draft_request': draft_request
    }

    return render(request, 'detail.html', context=data)


#def handle_form_request(draft_request):
#    draft_request.status = "formed"
#    draft_request.create_date = date.today()
#    draft_request.save()

def order(request, order_id=None):
    # Получаем черновик заявки
    if order_id:
        draft_request = get_object_or_404(UncrewedSpacecraft, id=order_id)
    else:
        draft_request = UncrewedSpacecraft.get_draft_request(request.user)

    # Проверяем статус заявки
    if draft_request is None or draft_request.status != 'draft':
        return redirect('home')

    ais_flights = Flight.objects.filter(uncrewed_spacecraft=draft_request)
    num_draft_request = ais_flights.count()
    choices_dict = dict(UncrewedSpacecraft.STATUS_CHOICES)
    status_name = choices_dict.get(draft_request.status, '')

    data = {
        'title': 'Космические объекты в заявке',
        'menu': menu,
        'status_name': status_name,
        'draft_request': draft_request,
        'num_draft_request': num_draft_request,
        'space_objects': draft_request.space_objects.all(),
    }
    return render(request, 'order.html', context=data)


def order_add(request, order_id, service_id):
    # Добавление услуги в заявку через ORM
    draft_request = get_object_or_404(UncrewedSpacecraft, id=order_id)

    if draft_request.status != 'draft':
        return redirect('home')

    service = get_object_or_404(SpaceObject, id=service_id)
    Flight.objects.create(uncrewed_spacecraft=draft_request, space_object=service, create_date=date.today())


def order_delete(request, order_id):
    # Удаление заявки через SQL-запрос
    draft_request = get_object_or_404(UncrewedSpacecraft, id=order_id)

    if draft_request.status == 'draft':
        with connection.cursor() as cursor:
            cursor.execute(
                """UPDATE "UncrewedSpacecraft" SET status = 'deleted' WHERE id = %s""",
                [draft_request.id]
            )
    return redirect('home')

def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>Страница не найдена.</h1>")
