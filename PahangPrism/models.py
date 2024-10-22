from django.db import models
import uuid
from django.db.models import Max

# User model for managing signups and logins
class User(models.Model):
    userID = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    is_staff = models.BooleanField(default=False) 

    def __str__(self):
        return self.full_name

# Venue model for event locations
class Venue(models.Model):
    venueID = models.CharField(primary_key=True, max_length=50)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)

# Event model for storing event information
class Event(models.Model):
    eventID = models.CharField(primary_key=True, max_length=50, editable=False)
    name = models.CharField(max_length=255)
    date = models.DateField()
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.eventID:
            # Get the maximum eventID
            max_id = Event.objects.aggregate(Max('eventID'))['eventID__max']
            if max_id:
                # Extract the number, increment it, and create a new ID
                max_num = int(max_id[1:])
                new_num = max_num + 1
                self.eventID = f'E{new_num}'
            else:
                # If no events exist yet, start with E1
                self.eventID = 'E1'
        super().save(*args, **kwargs)

# StarredItem model for users to favorite venues and events
class StarredItem(models.Model):
    userID = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.CharField(max_length=50)  # 'venue' or 'event'
    object_id = models.CharField(max_length=255)

    class Meta:
        unique_together = ('userID', 'content_type', 'object_id')

# Booking model for event registrations
class Booking(models.Model):
    bookingID = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    booking_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')
