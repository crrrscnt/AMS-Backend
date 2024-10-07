from django.contrib import admin
from .models import SpaceObject, FlightSpaceObject, UncrewedSpacecraft

admin.site.register(SpaceObject)
admin.site.register(UncrewedSpacecraft)
admin.site.register(FlightSpaceObject)