from django.http import HttpResponseRedirect, HttpResponseNotFound, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import connection
from lab2.models import SpaceObject, UncrewedSpacecraft, FlightSpaceObject

from datetime import date, datetime

menu = [{'title': "Главная", 'url_name': 'home'}]


# @login_required
def index(request):
    services_list = []
    draft_request = UncrewedSpacecraft.get_draft_request(request.user)
    spacecraft_spaceobjects = FlightSpaceObject.objects.filter(
        spacecraft=draft_request)
    num_objects = spacecraft_spaceobjects.count()
    no_click = ''
    if num_objects == 0:
        no_click = 'class = "no-click"'
    space_object = request.GET.get('space_object', '')

    if space_object == '':
        services = SpaceObject.objects.filter(is_active=True).values(
            'id',
            'name',
            'description',
            'image_url'
        )
    else:
        services = SpaceObject.objects.filter(
            is_active=True,
            name__icontains=space_object
        ).values(
            'id',
            'name',
            'description',
            'image_url'
        )

    for service in services:
        services_list.append(service)

    data = {'title': 'Услуги АМС',
            'menu': menu,
            'no_click': no_click,
            'space_objects': services_list,
            'space_object': space_object,
            'num_objects': num_objects,
            'draft_request': draft_request,
            }
    return render(request, 'index.html', context=data)


# @login_required
def detail(request, detail_id):
    space_object = get_object_or_404(SpaceObject, id=detail_id)
    data = {
        'menu': menu,
        'space_object': space_object,
    }
    return render(request, 'detail.html', context=data)


def spacecraft(request, spacecraft_id=None):
    if spacecraft_id:
        draft_request = get_object_or_404(UncrewedSpacecraft, id=spacecraft_id)
    else:
        draft_request = UncrewedSpacecraft.get_draft_request(request.user)

    # Проверяем статус заявки
    if draft_request.status != 'draft':
        return redirect('home')

    flights = FlightSpaceObject.objects.filter(spacecraft=draft_request)
    num_draft_request = flights.count()
    choices_dict = dict(UncrewedSpacecraft.STATUS_CHOICES)
    status_name = choices_dict.get(draft_request.status, '')

    if not draft_request:
        return redirect('home')

    data = {
        'title': 'Космические объекты в заявке',
        'menu': menu,
        'status_name': status_name,
        'draft_request': draft_request,
        'num_draft_request': num_draft_request,
        'space_objects': draft_request.space_objects.all(),
    }
    return render(request, 'spacecraft.html', context=data)


def add_object(request):
    object_id = request.POST.get('object_id')
    space_object = get_object_or_404(SpaceObject, id=object_id)
    draft_request = UncrewedSpacecraft.get_draft_request(request.user)

    if not draft_request:
        # Если нет черновой заявки, создаем новую
        draft_request = UncrewedSpacecraft.objects.create(
            user=request.user,
            status='draft')
    # Проверяем, существует ли уже связь между заявкой и объектом
    if not FlightSpaceObject.objects.filter(spacecraft=draft_request,
                                            space_object=space_object).exists():
        # Добавляем космический объект в заявку
        FlightSpaceObject.objects.create(spacecraft=draft_request,
                                         space_object=space_object,
                                         create_date=date.today())

    return HttpResponseRedirect(
        reverse('spacecraft', args=[draft_request.id]))


def delete_spacecraft(request):
    spacecraft_id = request.POST.get('spacecraft_id')
    # Выполнение логического удаления через SQL-запрос
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE spacecraft SET status = 'deleted' WHERE id = %s",
            [spacecraft_id])
    return redirect('home')


def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>Страница не найдена.</h1>")
