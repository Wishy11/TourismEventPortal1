from django.contrib import admin
from .models import User, Event, Venue, StarredItem, Booking
# Register your models here.
admin.site.register(User)
admin.site.register(Event)
admin.site.register(Venue)
admin.site.register(StarredItem)
admin.site.register(Booking)

