from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Venue, Event, StarredItem, User, Booking
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from .forms import UserProfileForm
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError

def search_item(request):
    if request.method == 'GET':
        item_id = request.GET.get('id')
        item_type = request.GET.get('type')

        if item_type == 'venue':
            item = Venue.objects.filter(venueID=item_id).first()
        elif item_type == 'event':
            item = Event.objects.filter(eventID=item_id).first()
        else:
            return render(request, 'search_item.html', {'error': 'Invalid item type'})

        if item:
            return render(request, 'search_item.html', {'item': item})
        else:
            return render(request, 'search_item.html', {'error': 'Item not found'})


def index(request):
    context = {}
    if request.session.get('userID'):
        user = User.objects.get(userID=request.session['userID'])
        context['user_full_name'] = user.full_name
    return render(request, 'index.html', context)


def register(request):
    if request.method == 'POST':
        full_name = request.POST['full_name']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists!')
            return redirect('register')

        new_user = User(full_name=full_name, email=email, password=password)
        new_user.save()
        messages.success(request, 'Account created successfully! Please log in.')
        return redirect('login')

    return render(request, 'register.html')


from django.contrib.auth import login as auth_login

def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        try:
            user = User.objects.get(email=email, password=password)
            request.session['userID'] = user.userID
            request.session['is_staff'] = user.is_staff
            messages.success(request, 'You are now logged in.')
            
            # Redirect to 'next' parameter if it exists
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('index')
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'login.html')


def logout(request):
    if request.method == 'POST':
        # Clear all session data
        request.session.flush()
        messages.success(request, 'You have been successfully logged out.')
        return redirect('login')
    else:
        return redirect('index')


def event_list(request):
    events = Event.objects.all().order_by('date')  # Fetch all events, ordered by date
    userID = request.session.get('userID')
    starred_events = []
    if userID:
        starred_events = StarredItem.objects.filter(userID_id=userID, content_type='event').values_list('object_id', flat=True)
    
    context = {
        'events': events,
        'starred_events': starred_events
    }
    return render(request, 'event_list.html', context)


def venue_list(request):
    venues = Venue.objects.all()
    
    # If the user is logged in, get their starred venues
    starred_venues = []
    if request.user.is_authenticated:
        starred_items = StarredItem.objects.filter(userID=request.user, content_type='venue')
        starred_venues = [item.object_id for item in starred_items]
    
    context = {
        'venues': venues,
        'starred_venues': starred_venues
    }
    return render(request, 'venue_list.html', context)


def star_item(request, content_type, object_id):
    userID = request.session.get('userID')
    if userID:
        starred_item = StarredItem.objects.filter(userID_id=userID, content_type=content_type, object_id=object_id).first()

        if starred_item:
            starred_item.delete()  # Unstar the item
        else:
            StarredItem.objects.create(userID_id=userID, content_type=content_type, object_id=object_id)

        return redirect('starred_list')
    return redirect('login')


def starred_list(request):
    userID = request.session.get('userID')
    if userID:
        starred_items = StarredItem.objects.filter(userID_id=userID)

        # Retrieve starred venues and events
        venues = Venue.objects.filter(venueID__in=[item.object_id for item in starred_items if item.content_type == 'venue'])
        events = Event.objects.filter(eventID__in=[item.object_id for item in starred_items if item.content_type == 'event'])

        return render(request, 'starred_list.html', {'venues': venues, 'events': events})
    return redirect('login')


def book_event(request, eventID):
    if not request.session.get('userID'):
        messages.error(request, 'You must be logged in to book an event.')
        return redirect('login')

    event = get_object_or_404(Event, eventID=eventID)
    user_id = request.session['userID']

    # Check if the user has already booked this event
    if Booking.objects.filter(user_id=user_id, event=event).exists():
        messages.error(request, 'You have already booked this event.')
        return redirect('event_list')

    # Create a new booking
    Booking.objects.create(user_id=user_id, event=event)
    messages.success(request, f'You have successfully booked {event.name}.')
    return redirect('booked_events')


def booked_events(request):
    userID = request.session.get('userID')
    if not userID:
        messages.error(request, 'You must be logged in to view your booked events.')
        return redirect('login')
    
    bookings = Booking.objects.filter(user_id=userID).select_related('event')
    return render(request, 'booked_events.html', {'bookings': bookings})


def cancel_booking(request, bookingID):
    if not request.session.get('userID'):
        messages.error(request, 'You must be logged in to cancel a booking.')
        return redirect('login')

    booking = get_object_or_404(Booking, bookingID=bookingID, user_id=request.session['userID'])
    event_name = booking.event.name
    booking.delete()
    messages.success(request, f'Your booking for {event_name} has been cancelled.')
    return redirect('booked_events')

def search(request):
    query = request.GET.get('q')
    events = []
    venues = []
    if query:
        events = Event.objects.filter(
            Q(name__icontains=query) |
            Q(venue__name__icontains=query)
        )
        venues = Venue.objects.filter(
            Q(name__icontains=query) |
            Q(location__icontains=query)
        )
    
    starred_venues = request.session.get('starred_venues', [])
    
    context = {
        'query': query,
        'events': events,
        'venues': venues,
        'starred_venues': starred_venues,
    }
    return render(request, 'search.html', context)

def user_dashboard(request):
    if not request.session.get('userID'):
        messages.error(request, 'You must be logged in to view your dashboard.')
        return redirect('login')
    
    user = User.objects.get(userID=request.session['userID'])
    bookings = Booking.objects.filter(user=user).select_related('event', 'event__venue')
    
    context = {
        'user': user,
        'bookings': bookings,
    }
    return render(request, 'user_dashboard.html', context)

def update_profile(request):
    if not request.session.get('userID'):
        messages.error(request, 'You must be logged in to update your profile.')
        return redirect('login')
    
    if request.method == 'POST':
        user = User.objects.get(userID=request.session['userID'])
        user.full_name = request.POST.get('full_name')
        user.email = request.POST.get('email')
        
        new_password = request.POST.get('new_password')
        if new_password:
            if new_password == request.POST.get('confirm_password'):
                user.password = make_password(new_password)
            else:
                messages.error(request, 'Passwords do not match.')
                return redirect('user_dashboard')
        
        try:
            user.full_clean()
            user.save()
            messages.success(request, 'Your profile has been updated successfully.')
        except ValidationError as e:
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    return redirect('index')

def about(request):
    return render(request, 'about.html')

def admin_dashboard(request):
    if not request.session.get('userID') or not request.session.get('is_staff'):
        messages.error(request, 'You must be logged in as staff to access the admin dashboard.')
        return redirect('login')
    
    venues = Venue.objects.all()
    
    if request.method == 'POST':
        if 'add_event' in request.POST:
            name = request.POST['event_name']
            date = request.POST['event_date']
            venue_id = request.POST.get('event_venue')
            
            try:
                venue = Venue.objects.get(venueID=venue_id)
                Event.objects.create(name=name, date=date, venue=venue)
                messages.success(request, 'Event added successfully!')
            except Venue.DoesNotExist:
                messages.error(request, f'Selected venue (ID: {venue_id}) does not exist. Please choose a valid venue.')
        
        elif 'add_venue' in request.POST:
            venueID = request.POST['venue_id']
            name = request.POST['venue_name']
            location = request.POST['venue_location']
            image = request.FILES.get('venue_image')
            
            image_path = 'default_venue_image.jpg'
            if image:
                file_name = f"venue_{venueID}_{image.name}"
                path = default_storage.save(f'venue_images/{file_name}', ContentFile(image.read()))
                image_path = os.path.join('venue_images', file_name)
            
            Venue.objects.create(venueID=venueID, name=name, location=location, image_path=image_path)
            messages.success(request, 'Venue added successfully!')
        
        return redirect('admin_dashboard')
    
    return render(request, 'admin_dashboard.html', {'venues': venues})

def is_staff(user):
    return user.is_staff

def admin_database_management(request):
    if not request.session.get('userID') or not request.session.get('is_staff'):
        messages.error(request, 'You must be logged in as staff to access this page.')
        return redirect('login')

    users = User.objects.all()
    venues = Venue.objects.all()
    events = Event.objects.all()
    bookings = Booking.objects.all()

    context = {
        'users': users,
        'venues': venues,
        'events': events,
        'bookings': bookings,
    }
    return render(request, 'admin_database_management.html', context)

def edit_user(request, userID):
    if not request.session.get('userID') or not request.session.get('is_staff'):
        messages.error(request, 'You must be logged in as staff to access this page.')
        return redirect('login')

    user = get_object_or_404(User, userID=userID)
    if request.method == 'POST':
        user.full_name = request.POST.get('full_name')
        user.email = request.POST.get('email')
        user.is_staff = request.POST.get('is_staff') == 'on'
        user.save()
        messages.success(request, f'User {user.full_name} has been updated successfully.')
        return redirect('admin_database_management')
    return render(request, 'edit_user.html', {'user': user})


def delete_user(request, userID):
    if not request.session.get('userID') or not request.session.get('is_staff'):
        messages.error(request, 'You must be logged in as staff to access this page.')
        return redirect('login')
    
    user = get_object_or_404(User, userID=userID)
    if request.method == 'POST':
        user.delete()
        messages.success(request, f'User {user.full_name} has been deleted successfully.')
        return redirect('admin_database_management')
    return render(request, 'confirm_delete.html', {'item': user, 'item_type': 'User'})

def edit_venue(request, venueID):
    if not request.session.get('userID') or not request.session.get('is_staff'):
        messages.error(request, 'You must be logged in as staff to access this page.')
        return redirect('login')
    
    venue = get_object_or_404(Venue, venueID=venueID)
    if request.method == 'POST':
        venue.name = request.POST.get('name')
        venue.location = request.POST.get('location')
        if 'image' in request.FILES:
            image = request.FILES['image']
            file_name = f"venue_{venueID}_{image.name}"
            # Delete the old image if it exists
            if venue.image_path and os.path.isfile(os.path.join(settings.MEDIA_ROOT, venue.image_path)):
                os.remove(os.path.join(settings.MEDIA_ROOT, venue.image_path))
            # Save the new image
            path = default_storage.save(f'venue_images/{file_name}', ContentFile(image.read()))
            venue.image_path = path
        venue.save()
        messages.success(request, f'Venue {venue.name} has been updated successfully.')
        return redirect('admin_database_management')
    return render(request, 'edit_venue.html', {'venue': venue})

def delete_venue(request, venueID):
    if not request.session.get('userID') or not request.session.get('is_staff'):
        messages.error(request, 'You must be logged in as staff to access this page.')
        return redirect('login')
    
    venue = get_object_or_404(Venue, venueID=venueID)
    if request.method == 'POST':
        venue.delete()
        messages.success(request, f'Venue {venue.name} has been deleted successfully.')
        return redirect('admin_database_management')
    return render(request, 'confirm_delete.html', {'item': venue, 'item_type': 'Venue'})

def edit_event(request, eventID):
    if not request.session.get('userID') or not request.session.get('is_staff'):
        messages.error(request, 'You must be logged in as staff to access this page.')
        return redirect('login')
    
    event = get_object_or_404(Event, eventID=eventID)
    venues = Venue.objects.all()
    if request.method == 'POST':
        event.name = request.POST.get('name')
        event.date = request.POST.get('date')
        event.venue = get_object_or_404(Venue, venueID=request.POST.get('venue'))
        event.save()
        messages.success(request, f'Event {event.name} has been updated successfully.')
        return redirect('admin_database_management')
    return render(request, 'edit_event.html', {'event': event, 'venues': venues})

def delete_event(request, eventID):
    if not request.session.get('userID') or not request.session.get('is_staff'):
        messages.error(request, 'You must be logged in as staff to access this page.')
        return redirect('login')
    
    event = get_object_or_404(Event, eventID=eventID)
    if request.method == 'POST':
        event.delete()
        messages.success(request, f'Event {event.name} has been deleted successfully.')
        return redirect('admin_database_management')
    return render(request, 'confirm_delete.html', {'item': event, 'item_type': 'Event'})
    
def edit_booking(request, bookingID):
    if not request.session.get('userID') or not request.session.get('is_staff'):
        messages.error(request, 'You must be logged in as staff to access this page.')
        return redirect('login')
    
    booking = get_object_or_404(Booking, bookingID=bookingID)
    users = User.objects.all()
    events = Event.objects.all()
    if request.method == 'POST':
        booking.user = get_object_or_404(User, userID=request.POST.get('user'))
        booking.event = get_object_or_404(Event, eventID=request.POST.get('event'))
        booking.save()
        messages.success(request, f'Booking {booking.bookingID} has been updated successfully.')
        return redirect('admin_database_management')
    return render(request, 'edit_booking.html', {'booking': booking, 'users': users, 'events': events})

def delete_booking(request, bookingID):
    if not request.session.get('userID') or not request.session.get('is_staff'):
        messages.error(request, 'You must be logged in as staff to access this page.')
        return redirect('login')
    
    booking = get_object_or_404(Booking, bookingID=bookingID)
    if request.method == 'POST':
        booking.delete()
        messages.success(request, f'Booking {booking.bookingID} has been deleted successfully.')
        return redirect('admin_database_management')
    return render(request, 'confirm_delete.html', {'item': booking, 'item_type': 'Booking'})




