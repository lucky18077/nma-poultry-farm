from django.urls import path
from . import views 

urlpatterns = [
    path('', views.index, name='index'), 
    path('logout/', views.logout_view, name='logout'),
    path('contact-us', views.contact, name='contact'),
    path('dashboard', views.dashboard, name='dashboard'), 
    path('users-list', views.usersList, name='users'), 
    path('save-user', views.save_user, name='save_user'),
    path('plant-list', views.plantList, name='plantList'),
    path('save-plant', views.save_plant, name='save_plant'),

]

 
 
    
    
    
    