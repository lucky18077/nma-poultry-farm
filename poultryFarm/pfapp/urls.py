from django.urls import path
from . import views 
from . import api_views

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
    path('daily-batch-report', views.daily_batch, name='daily_batch'),
    path('daily-recipe-report', views.daily_recipe, name='daily_recipe'),
    path('daily-consumption-report', views.daily_consumption, name='daily_consumption'),
    path('batch-shift-report', views.batch_shift, name='batch_shift'),
    path('recipe-shift-report', views.recipe_shift, name='recipe_shift'),
    path('consumption-shift-report', views.consumption_shift, name='consumption_shift'),
    path('custom-batch-report', views.custom_batch, name='custom_batch'),
    path('custom-recipe-report', views.custom_recipe, name='custom_recipe'),
    path('custom-consumption-report', views.custom_consumption, name='custom_consumption'),
    path('custom-motor-report', views.custom_motor, name='custom_motor'),
    path('summary-report', views.summary_reports, name='summary_reports'),
    
    
    # *********API Route*************
    path('api/plants/', api_views.plant_list_api, name='api_plant_list'),
    path('api/insert-batchdata/', api_views.insert_batchdata, name='api_insert_batchdata'),
    path('api/insert-recipe/', api_views.insert_recipe, name='api_insert_recipe'),
    path('api/insert-motordata/', api_views.insert_motordata, name='api_insert_motordata'),
    path('api/insert-materialname/', api_views.insert_materialname, name='api_insert_materialname'),
    path('api/insert-binname/', api_views.insert_binname, name='api_insert_binname'),
    path('api/insert-bagdata/', api_views.insert_bagdata, name='api_insert_bagdata'),
    

]

 
 
    
    
    
    