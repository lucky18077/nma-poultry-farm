from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Plant,BatchData,MotorData
from datetime import datetime
import random
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils.dateparse import parse_datetime
User = get_user_model()

# Create your views here.
def index(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
            if user.password == password:  # ⚠️ Not secure! Use authenticate() in production.
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')

                # 🔁 Get all child user IDs recursively
                child_ids = []
                iterable = [user.id]

                while iterable:
                    child_ids.extend(iterable)
                    users = User.objects.filter(reporting_manager_id__in=iterable)
                    iterable = [u.id for u in users]

                request.session['child_ids'] = child_ids 
                print("Logged-in User ID:", user.id)
                print("All Child User IDs:", child_ids) 
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password')
        except User.DoesNotExist:
            messages.error(request, 'Invalid username or password')

    return render(request, 'login.html')

def contact(request):
    return render(request,'contact.html')

@login_required
def profile(request):
    return render(request, 'profile.html', {'user': request.user})

def logout_view(request):
    logout(request)   
    messages.success(request, 'You have been logged out successfully.')   
    return redirect('index')

 
@login_required
def usersList(request):
    users = User.objects.filter(is_superuser=False)
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

        # Find the only admin user
        # admin_user = User.objects.filter(designation='admin').first()
        reporting_manager_id = request.POST.get('reporting_manager_id')

        if user_id:
            user = User.objects.get(id=user_id)
            user.username = username
            user.email = email
            user.password = password  # (hash if needed)
            user.designation = designation
            user.reporting_manager_id=reporting_manager_id
            # user.reporting_manager = admin_user
            user.save()
        else:
            User.objects.create(
                username=username,
                email=email,
                password=password,  # (hash if needed)
                designation=designation,
                reporting_manager_id=reporting_manager_id
                # reporting_manager=admin_user
            )
        return redirect('users')
    
@login_required
def plantList(request):
    plants = Plant.objects.all()
    managers = User.objects.filter(designation='plant_owner')
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
    batch = None
    recipestartTime = None
    batchno = None
    totalBatch = None
    recipename = None
    motor_data = None
    selected_datetime = None
    plants = []
    plant_id = None

    # Get plant list or plant_id
    if request.user.is_superuser:
        plants = Plant.objects.all()
    elif request.user.designation == 'manufacture':
        child_ids = request.session.get('child_ids', [])
        plants = Plant.objects.filter(plant_owner_id__in=child_ids)
            
    elif request.user.designation == 'plant_owner':
        # Correct filter to get plant for owner
        plant = Plant.objects.filter(plant_owner_id=request.user.id).first()
        if plant:
            plant_id = plant.plant_id
        

    if request.method == 'POST': 
        selected_datetime_str = request.POST.get('select_date') 
        # Only get plant_id from POST for non-plant-owner
        if request.user.designation != 'plant_owner':
            plant_id = request.POST.get('plant_id')

        # fallback if still not found
        if not plant_id and request.user.designation == 'plant_owner':
            plant = Plant.objects.filter(plant_owner_id=request.user.id).first()
            if plant:
                plant_id = plant.plant_id

        if selected_datetime_str:
            selected_datetime = datetime.strptime(selected_datetime_str, '%Y-%m-%d')
            selected_date_str = selected_datetime.strftime('%Y-%m-%d') 

        if plant_id:
            plant_id = int(plant_id)
            batch = BatchData.objects.filter(plant_id=plant_id, stdate=selected_date_str).order_by('-stTime').first()
            recipestartTime = batch.stTime if batch else None
            batchno = batch.BatchNum if batch else None
            totalBatch = batch.TotalBatchNum if batch else None
            recipename = batch.RecipeName if batch else None
            motor_data = MotorData.objects.filter(plant_id=plant_id).order_by('-sdate').first()
            

    else:
        # GET request — plant_owner should see their plant's data
        if request.user.designation == 'plant_owner' and plant_id:
            batch = BatchData.objects.filter(plant_id=plant_id).order_by('-stTime').first() 
            recipestartTime = batch.stTime if batch else None
            batchno = batch.BatchNum if batch else None
            totalBatch = batch.TotalBatchNum if batch else None
            recipename = batch.RecipeName if batch else None
            motor_data = MotorData.objects.filter(plant_id=plant_id).order_by('-sdate').first()

    return render(request, 'dashboard.html', {
        'recipename': recipename,
        'recipestartTime': recipestartTime,
        'batchno': batchno,
        'totalBatch': totalBatch,
        'motor_data': motor_data,
        'plants': plants,
        'selected_datetime': selected_datetime,
        'is_plant_owner': request.user.designation == 'plant_owner',
    })
    
    
@login_required
def plant_view(request): 
    plants = [] 
    if request.user.is_superuser:
        plants = Plant.objects.all()   
    elif request.user.designation == 'manufacture': 
        child_ids = request.session.get('child_ids', [])
        plants = Plant.objects.filter(plant_owner_id__in=child_ids)  
    elif request.user.designation == 'plant_owner': 
        plant = Plant.objects.filter(plant_owner_id=request.user.id).first()
        if plant:
            plant_id = plant.plant_id
            plants = [plant] 

    return render(request, 'plant-view.html', {'plants': plants})

@login_required
def plant_detail(request, plant_id):
    plant = Plant.objects.get(plant_id=plant_id)
    from_datetime = None
    to_datetime = None
    filtered_data = BatchData.objects.none()   
    total_recipes = 0
    batch_count = None
    recipe_name=None
    start_date = finish_date = pre_start_date = None

    if request.method == 'POST':
        from_datetime_str = request.POST.get('from_datetime')
        to_datetime_str = request.POST.get('to_datetime')

        if from_datetime_str and to_datetime_str:
            from_datetime = datetime.strptime(from_datetime_str, '%Y-%m-%d')
            to_datetime = datetime.strptime(to_datetime_str, '%Y-%m-%d')

            filtered_data = BatchData.objects.filter(
                plant_id=plant_id,
                stdate__range=[from_datetime, to_datetime]
            ).order_by('-stTime')
        else:
            filtered_data = BatchData.objects.filter(plant_id=plant_id).order_by('-stTime')

        total_recipes = filtered_data.count()
        batch_count = filtered_data.count() 
        recipe_name = filtered_data.first().RecipeName if filtered_data.exists() else None
        if filtered_data.exists():
            start_date = datetime.strptime(filtered_data.first().stdate, '%Y-%m-%d')
            finish_date = datetime.strptime(filtered_data.last().stdate, '%Y-%m-%d')
            # pre_start_date = start_date - timedelta(days=1)
            pre_start_date = None

    return render(request, 'plant-detail.html', {
        'plant': plant,
        'filtered_data': filtered_data,   
        'total_recipes': total_recipes,   
        'recipe_name': recipe_name,   
        'batch_count': batch_count, 
        'start_date': start_date,
        'finish_date': finish_date,
        'pre_start_date': pre_start_date,   
    })
 