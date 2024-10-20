from django.contrib import admin
from .models import SpaceObject, UncrewedSpacecraft, FlightSpaceObject, \
    AuthUser

admin.site.register(SpaceObject)
admin.site.register(UncrewedSpacecraft)
admin.site.register(FlightSpaceObject)
admin.site.register(AuthUser)
