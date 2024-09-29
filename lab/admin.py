from django.contrib import admin
from .models import SpaceObject, UncrewedSpacecraft, Flight

admin.site.register(SpaceObject)
admin.site.register(UncrewedSpacecraft)
admin.site.register(Flight)