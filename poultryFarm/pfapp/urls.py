from django.urls import path
from . import views 

urlpatterns = [
    path('', views.index, name='index'), 
    path('logout/', views.logout_view, name='logout'),
    path('contact-us', views.contact, name='contact'),
    path('profile-view', views.profile, name='profile'),
    path('plant-summary', views.dashboard, name='dashboard'), 
    path('users-list', views.usersList, name='users'), 
    path('save-user', views.save_user, name='save_user'),
    path('plant-list', views.plantList, name='plantList'),
    path('save-plant', views.save_plant, name='save_plant'),
    path('dashboard', views.plant_view, name='plant_view'),
    path('plants-detail/<int:plant_id>/', views.plant_detail, name='plant_detail'),
    path('batch-shift-report', views.batch_shift, name='batch_shift'),
    path('recipe-shift-report', views.recipe_shift, name='recipe_shift'),
    path('consumption-shift-report', views.consumption_shift, name='consumption_shift'),

]

 
 
    
    
    
    