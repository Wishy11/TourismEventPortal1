from django.urls import path
from . import views

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),
    path('events/', views.event_list, name='event_list'),
    path('venues/', views.venue_list, name='venue_list'),
    path('search/', views.search, name='search'),
    path('starred/', views.starred_list, name='starred_list'),
    path('booked/', views.booked_events, name='booked_events'),
    path('star-item/<str:content_type>/<str:object_id>/', views.star_item, name='star_item'),
    path('book-event/<str:eventID>/', views.book_event, name='book_event'),
    path('cancel-booking/<int:bookingID>/', views.cancel_booking, name='cancel_booking'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('about/', views.about, name='about'),
    path('database-management/', views.admin_database_management, name='admin_database_management'),
    path('user/edit/<int:userID>/', views.edit_user, name='edit_user'),
    path('user/delete/<int:userID>/', views.delete_user, name='delete_user'),
    path('venue/edit/<str:venueID>/', views.edit_venue, name='edit_venue'),
    path('venue/delete/<str:venueID>/', views.delete_venue, name='delete_venue'),
    path('event/edit/<str:eventID>/', views.edit_event, name='edit_event'),
    path('event/delete/<str:eventID>/', views.delete_event, name='delete_event'),
    path('booking/edit/<str:bookingID>/', views.edit_booking, name='edit_booking'),
    path('booking/delete/<str:bookingID>/', views.delete_booking, name='delete_booking'),
]

