from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Plant,BatchData,MotorData
from datetime import datetime, timedelta
import random
from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Min, Max,Count
from django.contrib.auth import get_user_model
from django.utils.timezone import make_aware
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
    
def safe_round(value, ndigits=2):
    try:
        return round(value, ndigits)
    except (TypeError, ValueError):
        return None
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
    hammer_stats = None
    pellet_stats = None

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
            motor_data = MotorData.objects.filter(plant_id=plant_id,sdate=selected_date_str).order_by('-sTime')  
            # print(motor_data)
            hammer_stats = motor_data.filter(rvfrpm__gt=0).aggregate(
                hammer_avg=Avg('rvfrpm'),
                hammer_count=Count('rvfrpm'),
                hammer_efficiency=Avg('rvfrpm') * 100 / 1800,
                avg_load=Avg('hammercurrent'),
                start_time=Min('sTime'),
                end_time=Max('sTime')
            )
            print(hammer_stats)
            # Calculate pellet mill statistics
            pellet_stats = motor_data.filter(feederRPM__gt=0).aggregate(
                pellet_avg=Avg('feederRPM'),
                pellet_count=Count('feederRPM'),
                pellet_efficiency=Avg('feederRPM') * 100 / 1500,
                avg_load=Avg('pelletcurrent'),
                start_time=Min('sTime'),
                end_time=Max('sTime')
            )

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
        'hammer_stats': hammer_stats,
        'pellet_stats': pellet_stats,
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

# Dummy fallback safe_round
def safe_round(value, digits=2):
    try:
        return round(value, digits)
    except:
        return None

def parse_datetime(sdate, stime):
    """Combine sdate and sTime strings into aware datetime object"""
    try:
        return make_aware(datetime.strptime(f"{sdate} {stime}", "%Y-%m-%d %H:%M:%S"))
    except:
        return None

@login_required
def plant_detail(request, plant_id):
    plant = get_object_or_404(Plant, plant_id=plant_id)
    from_date = to_date = None
    filtered_data = BatchData.objects.none()
    total_recipes = batch_count = recipe_name = None
    start_date = finish_date = None
    from_date_str = to_date_str = None
    hammer_stats = pellet_stats = {}

    if request.method == 'POST':
        from_date_str = request.POST.get('from_datetime')
        to_date_str = request.POST.get('to_datetime')

        if from_date_str and to_date_str:
            from_date = datetime.strptime(from_date_str, "%Y-%m-%d").date()
            to_date = datetime.strptime(to_date_str, "%Y-%m-%d").date()
        else:
            today = datetime.now().date()
            from_date = to_date = today

        # Get all sdate strings in selected range
        date_list = [
            (from_date + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range((to_date - from_date).days + 1)
        ]

        # Filter batch data
        filtered_data = BatchData.objects.filter(
            plant_id=plant_id,
            stdate__range=[from_date, to_date]
        ).order_by('stTime')

        total_recipes = batch_count = filtered_data.count()
        recipe_name = filtered_data.first().RecipeName if filtered_data.exists() else None

        # Raw motor data
        motor_data_raw = MotorData.objects.filter(
            plant_id=plant_id,
            sdate__in=date_list
        ).order_by('sdate', 'sTime')

        # Parse datetime and attach
        motor_data = []
        for row in motor_data_raw:
            dt = parse_datetime(row.sdate, row.sTime)
            if dt:
                row._datetime = dt
                motor_data.append(row)

        # Start and end times
        start_time = motor_data[0]._datetime if motor_data else None
        end_time = motor_data[-1]._datetime if motor_data else None
        runtime_minutes = safe_round((end_time - start_time).total_seconds() / 60) if start_time and end_time else None
        
        # Hammer stats
        hammer = [m for m in motor_data if m.rvfrpm > 0]
        hammer_count = len(hammer)
        hammer_avg = sum(m.rvfrpm for m in hammer) / len(hammer) if hammer else 0
        hammer_load = sum(m.hammercurrent for m in hammer) / len(hammer) if hammer else 0
        hammer_stats = {
            'hammer_avg': safe_round(hammer_avg),
            'hammer_efficiency': safe_round((hammer_avg / 1800) * 100) if hammer_avg else None,
            'avg_load': safe_round(hammer_load),
            'start_time': start_time,
            'end_time': end_time,
            'runtime_minutes': runtime_minutes,
            'hammer_count':hammer_count
        }

        # Pellet stats
        pellet = [m for m in motor_data if m.feederRPM > 0]
        pellet_count=len(pellet)
        pellet_avg = sum(m.rvfrpm for m in pellet) / len(pellet) if pellet else 0
        pellet_load = sum(m.pelletcurrent for m in pellet) / len(pellet) if pellet else 0
        pellet_stats = {
            'pellet_avg': safe_round(pellet_avg),
            'pellet_efficiency': safe_round((pellet_avg / 1500) * 100) if pellet_avg else None,
            'avg_load': safe_round(pellet_load),
            'start_time': start_time,
            'end_time': end_time,
            'runtime_minutes': runtime_minutes,
            'pellet_count':pellet_count
        }

        start_date = start_time.date() if start_time else None
        finish_date = end_time.date() if end_time else None

    return render(request, 'plant-detail.html', {
        'plant': plant,
        'filtered_data': filtered_data,
        'total_recipes': total_recipes,
        'recipe_name': recipe_name,
        'batch_count': batch_count,
        'start_date': start_date,
        'finish_date': finish_date,
        'hammer_stats': hammer_stats,
        'pellet_stats': pellet_stats,
        'from_datetime': from_date_str,
        'to_datetime': to_date_str,
    })
 