from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Plant,BatchData,MotorData
from datetime import datetime
import random
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your views here.
def index(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
            if user.password == password:   
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')  
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid email or password')
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password')

    return render(request, 'login.html')

def contact(request):
    return render(request,'contact.html')

def logout_view(request):
    logout(request)   
    messages.success(request, 'You have been logged out successfully.')   
    return redirect('index')

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

@login_required
def usersList(request):
    users = User.objects.all()
    managers = User.objects.filter(designation='manufacture')
    return render(request, 'users.html', {'users': users, 'managers': managers})

@login_required
def save_user(request):
    if request.method == "POST":
        user_id = request.POST.get('id')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        designation = request.POST.get('designation')
        reporting_manager_id = request.POST.get('reporting_manager_id')
        
        if user_id:  # Update existing user
            user = User.objects.get(id=user_id)
            user.username = username
            user.email = email
            user.password = password
            user.designation = designation
            user.reporting_manager_id=reporting_manager_id
            user.save()
        else:  # Create new user
            User.objects.create(
                username=username,
                email=email,
                password=password,
                designation=designation,
                reporting_manager_id=reporting_manager_id
            )
        return redirect('users')
    
@login_required
def plantList(request):
    plants = Plant.objects.all()
    managers = User.objects.filter(designation='manufacture')
    return render(request, 'plant-list.html', {'plants': plants,'managers':managers})

@login_required
def save_plant(request):
    if request.method == "POST":
        plant_id = request.POST.get('id')
        plant_name = request.POST.get('plant_name')
        plant_owner_id = request.POST.get('plant_owner_id')

        # Validation: check if plant_name is empty
        if not plant_name or plant_owner_id.strip() == "":
            messages.error(request, "Plant Owner is required.")
        if not plant_name or plant_name.strip() == "":
            messages.error(request, "Plant name is required.")
            return redirect('plantList')
        if plant_id:  
            plant = Plant.objects.get(id=plant_id)
            plant.plant_name = plant_name
            plant.plant_owner_id = plant_owner_id
            plant.save()
        else:  
            # Generate unique plant_id
            while True:
                now = datetime.now().strftime("%H%M%S")  # current timestamp
                random_number = random.randint(1000, 9999)     # random 4-digit number
                generated_plant_id = f"{now}{random_number}"

                if not Plant.objects.filter(plant_id=generated_plant_id).exists():
                    break  # Unique ID found

            # Save new plant
            Plant.objects.create(
                plant_id=generated_plant_id,
                plant_name=plant_name,
                plant_owner_id=plant_owner_id
            )

        messages.success(request, "Plant saved successfully!")
        return redirect('plantList')   
    
 
@login_required
def dashboard(request):
    batch = BatchData.objects.order_by('-stdate').first()
    recipestartTime = batch.stTime if batch else None
    batchno = batch.BatchNum if batch else None   
    totalBatch = batch.TotalBatchNum if batch else None   
    recipename = batch.RecipeName if batch else None   
    motor_data = MotorData.objects.order_by('-sdate').first()
    return render(request, 'dashboard.html', {
        'recipename': recipename,
        'recipestartTime': recipestartTime,
        'batchno': batchno, 
        'totalBatch': totalBatch,
        'motor_data':motor_data
    })
 