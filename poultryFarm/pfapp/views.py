from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Plant,BatchData,MotorData,Recipemain,BinName,MaterialName,BagData
# from datetime import datetime, timedelta,time
from datetime import datetime as dt, time, timedelta
from datetime import datetime, timedelta
import random
from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Min, Max,Count,F, ExpressionWrapper, FloatField,OuterRef, Subquery,Sum
from django.db.models.functions import Cast
from django.contrib.auth import get_user_model
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from django.db.models import Q
User = get_user_model()
import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# Login views.
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
                # print("Logged-in User ID:", user.id)
                # print("All Child User IDs:", child_ids) 
                return redirect('plant_view')
            else:
                messages.error(request, 'Invalid username or password')
        except User.DoesNotExist:
            messages.error(request, 'Invalid username or password')

    return render(request, 'login.html')

# Contact views.
def contact(request):
    return render(request,'contact.html')

# Profile views.
@login_required
def profile(request): 
    return render(request, 'profile.html', {'user': request.user})

# Logout views.
def logout_view(request):
    logout(request)   
    messages.success(request, 'You have been logged out successfully.')   
    return redirect('index')

# Users List views.
@login_required
def usersList(request):
    users = User.objects.filter(is_superuser=False)
    managers = User.objects.filter(designation='manufacture')
    return render(request, 'users.html', {'users': users, 'managers': managers})

# Login Save views.
@login_required
def save_user(request):
    if request.method == "POST":
        user_id = request.POST.get('id')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        designation = request.POST.get('designation')
        first_name = request.POST.get('first_name')
        profile_photo = request.FILES.get('last_name')
        # Find the only admin user
        # admin_user = User.objects.filter(designation='admin').first()
        reporting_manager_id = request.POST.get('reporting_manager_id')
        upload_dir = os.path.join(settings.BASE_DIR, 'static', 'asset', 'last_name')
        os.makedirs(upload_dir, exist_ok=True)
        if user_id:
            user = User.objects.get(id=user_id)
            user.username = username
            user.email = email
            user.password = password  # (hash if needed)
            user.designation = designation
            user.first_name = first_name
            user.reporting_manager_id=reporting_manager_id
            # user.reporting_manager = admin_user
            if profile_photo:
                image_path = os.path.join(upload_dir, profile_photo.name)
                with open(image_path, 'wb+') as f:
                    for chunk in profile_photo.chunks():
                        f.write(chunk)
                user.last_name = f"asset/last_name/{profile_photo.name}"

            user.save()
        else:
            user = User(
                username=username,
                email=email,
                designation=designation,
                first_name=first_name,
                reporting_manager_id=reporting_manager_id
            )
            if password:
                user.set_password(password)

            if profile_photo:
                image_path = os.path.join(upload_dir, profile_photo.name)
                with open(image_path, 'wb+') as f:
                    for chunk in profile_photo.chunks():
                        f.write(chunk)
                user.last_name = f"asset/last_name/{profile_photo.name}"

            user.save()

        return redirect('users')

# Plant List views.    
@login_required
def plantList(request):
    plants = Plant.objects.all()
    managers = User.objects.filter(designation='plant_owner')
    return render(request, 'plant-list.html', {'plants': plants,'managers':managers})

# Plant CRUD views.
@login_required
def save_plant(request):
    if request.method == "POST":
        plant_id = request.POST.get('id')
        plant_name = request.POST.get('plant_name')
        plant_owner_id = request.POST.get('plant_owner_id')
        shiftA_start_str = request.POST.get('shiftA')
        profile_photo = request.FILES.get('profile_image') 
        upload_dir = os.path.join(settings.BASE_DIR, 'static', 'asset', 'plant_images')
        os.makedirs(upload_dir, exist_ok=True)

        # Validation
        if not plant_owner_id or plant_owner_id.strip() == "":
            messages.error(request, "Plant Owner is required.")
            return redirect('plantList')
        if not plant_name or plant_name.strip() == "":
            messages.error(request, "Plant name is required.")
            return redirect('plantList')

        try:
            shiftA_start = datetime.strptime(shiftA_start_str, '%H:%M')
        except ValueError:
            messages.error(request, "Invalid time format for shiftA.")
            return redirect('plantList')

        shiftB_start = shiftA_start + timedelta(hours=8)
        shiftC_start = shiftB_start + timedelta(hours=8)

        if plant_id:
            plant = Plant.objects.get(id=plant_id)
            plant.plant_name = plant_name
            plant.plant_owner_id = plant_owner_id
            plant.shiftA = shiftA_start.time()
            plant.shiftB = shiftB_start.time()
            plant.shiftC = shiftC_start.time()
            if profile_photo:
                image_path = os.path.join(upload_dir, profile_photo.name)
                with open(image_path, 'wb+') as f:
                    for chunk in profile_photo.chunks():
                        f.write(chunk)
                plant.profile_image = f"asset/plant_images/{profile_photo.name}"  
            plant.save()
        else:
            # === Create new plant with unique ID ===
            while True:
                now = datetime.now().strftime("%H%M%S")
                random_number = random.randint(1000, 9999)
                generated_plant_id = f"{now}{random_number}"
                if not Plant.objects.filter(plant_id=generated_plant_id).exists():
                    break

            image_path = None
            if profile_photo:
                image_path = os.path.join(upload_dir, profile_photo.name)
                with open(image_path, 'wb+') as f:
                    for chunk in profile_photo.chunks():
                        f.write(chunk)
                image_relative_path = f"asset/plant_images/{profile_photo.name}"
            else:
                image_relative_path = None

            Plant.objects.create(
                plant_id=generated_plant_id,
                plant_name=plant_name,
                plant_owner_id=plant_owner_id,
                shiftA=shiftA_start.time(),
                shiftB=shiftB_start.time(),
                shiftC=shiftC_start.time(),
                profile_image=image_relative_path
            )

        messages.success(request, "Plant saved successfully!")
        return redirect('plantList')   
    
def safe_round(value, ndigits=2):
    try:
        return round(value, ndigits)
    except (TypeError, ValueError):
        return None
 
# Dashboard views.    
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
            motor_data = MotorData.objects.filter(plant_id=plant_id).order_by('-sTime')  
            hammer_stats = motor_data.filter(rvfrpm__gt=0).aggregate(
                hammer_avg=Avg('rvfrpm'),
                hammer_count=Count('rvfrpm'),
                hammer_efficiency=Avg('rvfrpm') * 100 / 1800,
                avg_load=Avg('hammercurrent'),
                start_time=Min('sTime'),
                end_time=Max('sTime')
            )
            # print(hammer_stats)
            # Calculate pellet mill statistics
            pellet_stats = motor_data.filter(feederRPM__gt=0).aggregate(
                pellet_avg=Avg('feederRPM'),
                pellet_count=Count('feederRPM'),
                pellet_efficiency=Avg('feederRPM') * 100 / 1500,
                avg_load=Avg('pelletcurrent'),
                start_time=Min('sTime'),
                end_time=Max('sTime')
            )

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
    batch_data = BatchData.objects.none()
    start_date = finish_date = None
    from_date_str = to_date_str = None
    unique_recipe_data=None
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

        batch_data = BatchData.objects.filter(
            plant_id=plant_id,
            stdate__range=[from_date, to_date]
        )
        recipe_weight_expr = ExpressionWrapper(
            F('Bin1SetWt') + F('Bin2SetWt') + F('Bin3SetWt') +
            F('Bin4SetWt') + F('Bin5SetWt') + F('Bin6SetWt') +
            F('Bin7SetWt') + F('Bin8SetWt') + F('Bin9SetWt') +
            F('Bin10SetWt') + F('Bin11SetWt') + F('Bin12SetWt') +
            F('Bin13SetWt') + F('Bin14SetWt') + F('Bin15SetWt') + F('Bin16SetWt') +
            F('Oil1SetWt') + F('Oil2SetWt') + F('MedSetWt')+
            F('MolassesSetWt') + F('Premix1Set') + F('Premix2Set')+
            F('Man1SetWt') + F('Man2SetWt') + F('Man3SetWt') +
            F('Man4SetWt') + F('Man5SetWt') + F('Man6SetWt') +
            F('Man7SetWt') + F('Man8SetWt') + F('Man9SetWt') +
            F('Man10SetWt') + F('Man11SetWt') + F('Man12SetWt'),
            output_field=FloatField()
        )
        recipe_subquery = Recipemain.objects.filter(RecipeID=OuterRef('RecipeID')).annotate(
            total_weight=recipe_weight_expr
        ).values('total_weight')[:1]
        # Use annotate to get the first and last RecipeName per RecipeID
        unique_recipe_data = batch_data.values('RecipeID') \
            .annotate(
                First_RecipeName=Min('RecipeName'),  
                Last_RecipeName=Max('RecipeName'),
                batch_count=Count('RecipeID'), 
                start_time=Min('stTime'),
                end_time=Min('endTime'),
                total_recipe_weight=Subquery(recipe_subquery)
            ).order_by('RecipeID')
            
                 
        for item in unique_recipe_data:
            st_time = item['start_time']
            end_time = item['end_time'] 
            if isinstance(st_time, str):
                st_time = datetime.strptime(st_time, '%H:%M:%S')
            if isinstance(end_time, str):
                end_time = datetime.strptime(end_time, '%H:%M:%S') 
            if st_time and end_time: 
                time_diff = end_time - st_time 
                if time_diff.total_seconds() < 0:
                    time_diff += timedelta(days=1)
                total_seconds = int(time_diff.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                item['total_time'] = f'{hours:02}:{minutes:02}:{seconds:02}'
            else:
                item['total_time'] = '00:00:00'   
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
        'unique_recipe_data': unique_recipe_data,
        'start_date': start_date,
        'finish_date': finish_date,
        'hammer_stats': hammer_stats,
        'pellet_stats': pellet_stats,
        'from_datetime': from_date_str,
        'to_datetime': to_date_str,
    })
 
@login_required
def daily_batch(request):
    plants = []
    start_date = None
    batch_data = []
    recipe_ids = []
    batch_counts = []
    materialName = MaterialName.objects.all()
    plant_id = None
    plant_name = None

    # Get plants based on user role
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

    if request.method == "POST":
        start_date = request.POST.get('start_date')
        plant_id = request.POST.get('plant_id')

        try:
            if plant_id and start_date:
                plant_name = Plant.objects.filter(plant_id=request.POST.get('plant_id')).first()
                batch_data = BatchData.objects.filter(
                    plant_id=plant_id,
                    stdate=start_date   
                )
                
                recipe_ids = batch_data.values_list('RecipeID', flat=True).distinct()

                setWT = Recipemain.objects.filter(RecipeID__in=recipe_ids).annotate(
                    total_soya=Sum(
                        F('Bin1SetWt') + F('Bin2SetWt') + F('Bin3SetWt') + F('Bin4SetWt') +
                        F('Bin5SetWt') + F('Bin6SetWt') + F('Bin7SetWt') + F('Bin8SetWt') +
                        F('Bin9SetWt') + F('Bin10SetWt') + F('Bin11SetWt') + F('Bin12SetWt') +
                        F('Bin13SetWt') + F('Bin14SetWt') + F('Bin15SetWt') + F('Bin16SetWt')
                    ),
                    total_ddgs=Sum(
                        F('Man1SetWt') + F('Man2SetWt') + F('Man3SetWt') + F('Man4SetWt') +
                        F('Man5SetWt') + F('Man6SetWt') + F('Man7SetWt') + F('Man8SetWt') +
                        F('Man9SetWt') + F('Man10SetWt') + F('Man11SetWt') + F('Man12SetWt') +
                        F('Man13SetWt') + F('Man14SetWt') + F('Man15SetWt') + F('Man16SetWt')
                    ),
                    total_maize=F('Oil1SetWt'),
                    total_mbm=F('Oil2SetWt'),
                    total_mdoc=F('Premix1Set'),
                    total_oil1=F('Premix2Set'),
                )

                batch_counts = []
                for rec in setWT:
                    related_batches = batch_data.filter(RecipeID=rec.RecipeID)
                    per_batch_data = []

                    for b in related_batches:
                        per_batch_data.append({
                            'BatchNum': b.BatchNum,
                            'stTime': b.stTime,
                            'total_soya': sum([
                                b.Bin1Act, b.Bin2Act, b.Bin3Act, b.Bin4Act,
                                b.Bin5Act, b.Bin6Act, b.Bin7Act, b.Bin8Act,
                                b.Bin9Act, b.Bin10Act, b.Bin11Act, b.Bin12Act,
                                b.Bin13Act, b.Bin14Act, b.Bin15Act, b.Bin16Act
                            ]),
                            'total_ddgs': sum([
                                b.ManWt1, b.ManWt2, b.ManWt3, b.ManWt4,
                                b.ManWt5, b.ManWt6, b.ManWt7, b.ManWt8,
                                b.ManWt9, b.ManWt10, b.ManWt11, b.ManWt12,
                                b.ManWt13, b.ManWt14, b.ManWt15, b.ManWt16
                            ]),
                            'Oil1SetWt': b.Oil1Act,
                            'Oil2SetWt': b.Oil2Act,
                            'Premix1Set': b.PremixWt1,
                            'Premix2Set': b.PremixWt2
                        })

                    batch_counts.append({
                        'RecipeID': rec.RecipeID,
                        'count': related_batches.count(),
                        'total_soya': rec.total_soya,
                        'total_ddgs': rec.total_ddgs,
                        'Oil1SetWt': rec.total_maize,
                        'Oil2SetWt': rec.total_mbm,
                        'Premix1Set': rec.total_mdoc,
                        'Premix2Set': rec.total_oil1,
                        'actual_data': per_batch_data
                    })

        except Exception as e:
            print("Error:", e)

    return render(request, 'daily-batch-report.html', {
        'plants': plants,
        'plant_name': plant_name,
        'batch_data': batch_data,
        'recipe_ids': recipe_ids,
        'batch_counts': batch_counts,
        'materialName': materialName,
        'start_date': start_date,
        'is_plant_owner': request.user.designation == 'plant_owner',
    })

@login_required
def daily_recipe(request):
    plants = []
    recipe_ids = []
    batch_data = []
    batch_actual = []
    plant_id = None
    start_date = None
    plant_name = None

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

    if request.method == "POST":
        start_date = request.POST.get('start_date')
        plant_id = request.POST.get('plant_id')

        try:
            if plant_id and start_date:
                plant_name = Plant.objects.filter(plant_id=plant_id).first()

                # Filter by plant_id and stdate (string date match)
                batch_data = BatchData.objects.filter(
                    plant_id=plant_id,
                    stdate=start_date
                )

                recipe_ids = batch_data.values_list('RecipeID', flat=True).distinct()
                recipe_data_dict = {
                    recipe.RecipeID: recipe for recipe in Recipemain.objects.filter(RecipeID__in=recipe_ids)
                }

                for item in batch_data:
                    # Actual values
                    soya_fields = [getattr(item, f'Bin{i}Act') or 0 for i in range(1, 17)]
                    ddgs_fields = [getattr(item, f'ManWt{i}') or 0 for i in range(1, 17)]
                    total_soya = sum(soya_fields)
                    total_ddgs = sum(ddgs_fields)
                    total_maize = item.Oil1Act or 0
                    total_mbm = item.Oil2Act or 0
                    total_mdoc = item.PremixWt1 or 0
                    total_oil = item.PremixWt2 or 0

                    # Set values
                    recipe = recipe_data_dict.get(item.RecipeID)
                    if recipe:
                        set_soya_fields = [getattr(recipe, f'Bin{i}SetWt') or 0 for i in range(1, 17)]
                        set_ddgs_fields = [getattr(recipe, f'Man{i}SetWt') or 0 for i in range(1, 21)]
                        set_total_soya = sum(set_soya_fields)
                        set_total_ddgs = sum(set_ddgs_fields)
                        set_total_maize = recipe.Oil1SetWt or 0
                        set_total_mbm = recipe.Oil2SetWt or 0
                        set_total_mdoc = recipe.Premix1Set or 0
                        set_total_oil = recipe.Premix2Set or 0

                        def calc_error(actual, set_val):
                            error_kg = round(actual - set_val, 2)
                            error_pct = round((error_kg / set_val) * 100, 2) if set_val else 0
                            return error_kg, error_pct

                        # Attach values to item
                        item.recipe_name = recipe.recipename
                        item.set_total_soya = set_total_soya
                        item.total_soya = total_soya
                        item.error_soya, item.error_soya_pct = calc_error(total_soya, set_total_soya)

                        item.set_total_ddgs = set_total_ddgs
                        item.total_ddgs = total_ddgs
                        item.error_ddgs, item.error_ddgs_pct = calc_error(total_ddgs, set_total_ddgs)

                        item.set_total_maize = set_total_maize
                        item.total_maize = total_maize
                        item.error_maize, item.error_maize_pct = calc_error(total_maize, set_total_maize)

                        item.set_total_mbm = set_total_mbm
                        item.total_mbm = total_mbm
                        item.error_mbm, item.error_mbm_pct = calc_error(total_mbm, set_total_mbm)

                        item.set_total_mdoc = set_total_mdoc
                        item.total_mdoc = total_mdoc
                        item.error_mdoc, item.error_mdoc_pct = calc_error(total_mdoc, set_total_mdoc)

                        item.set_total_oil = set_total_oil
                        item.total_oil = total_oil
                        item.error_oil, item.error_oil_pct = calc_error(total_oil, set_total_oil)

                        item.set_total_all = set_total_soya + set_total_ddgs + set_total_maize + set_total_mbm + set_total_mdoc + set_total_oil
                        item.total_all = total_soya + total_ddgs + total_maize + total_mbm + total_mdoc + total_oil
                        item.error_total, item.error_total_pct = calc_error(item.total_all, item.set_total_all)

                        batch_actual.append(item)

        except Exception as e:
            print("Error:", e)

    return render(request, 'daily-recipe-report.html', {
        'plant_name': plant_name,
        'plants': plants,
        'recipe_ids': recipe_ids,
        'batch_actual': batch_actual,
        'start_date': start_date,
        'is_plant_owner': request.user.designation == 'plant_owner',
    })

@login_required
def daily_consumption(request):
    # Initialize variables
    plants = []
    batch_data = []
    recipe_ids = []
    plant_name = None
    start_date = None

    # Actual totals
    total_soya = total_ddgs = total_maize = total_mbm = total_mdoc = total_oil = 0

    # Set totals
    set_total_soya = set_total_ddgs = set_total_maize = set_total_mbm = set_total_mdoc = set_total_oil = 0

    # Errors
    error_soya = error_ddgs = error_maize = error_mbm = error_mdoc = error_oil = 0
    error_soya_pct = error_ddgs_pct = error_maize_pct = error_mbm_pct = error_mdoc_pct = error_oil_pct = 0
    set_total_all = total_all = error_total = error_total_pct = 0

    # Filter plants by user role
    if request.user.is_superuser:
        plants = Plant.objects.all()
    elif request.user.designation == 'manufacture':
        child_ids = request.session.get('child_ids', [])
        plants = Plant.objects.filter(plant_owner_id__in=child_ids)
    elif request.user.designation == 'plant_owner':
        plant = Plant.objects.filter(plant_owner_id=request.user.id).first()
        if plant:
            plants = [plant]

    if request.method == "POST":
        start_date = request.POST.get('start_date')
        plant_id = request.POST.get('plant_id')

        try:
            if plant_id and start_date:
                plant_name = Plant.objects.filter(plant_id=plant_id).first()

                # Fetch batch data between 00:00 and 23:59 of that date
                batch_data = BatchData.objects.filter(
                    plant_id=plant_id,
                    stdate = start_date
                )

                recipe_ids = batch_data.values_list('RecipeID', flat=True).distinct()
                recipe_data_dict = {
                    recipe.RecipeID: recipe for recipe in Recipemain.objects.filter(RecipeID__in=recipe_ids)
                }

                for item in batch_data:
                    # Actual weights
                    soya_fields = [getattr(item, f'Bin{i}Act') or 0 for i in range(1, 17)]
                    ddgs_fields = [getattr(item, f'ManWt{i}') or 0 for i in range(1, 17)]
                    total_soya += sum(soya_fields)
                    total_ddgs += sum(ddgs_fields)
                    total_maize += item.Oil1Act or 0
                    total_mbm += item.Oil2Act or 0
                    total_mdoc += item.PremixWt1 or 0
                    total_oil += item.PremixWt2 or 0

                    # Set weights from recipe
                    recipe = recipe_data_dict.get(item.RecipeID)
                    if recipe:
                        set_soya_fields = [getattr(recipe, f'Bin{i}SetWt') or 0 for i in range(1, 17)]
                        set_ddgs_fields = [getattr(recipe, f'Man{i}SetWt') or 0 for i in range(1, 21)]
                        set_total_soya += sum(set_soya_fields)
                        set_total_ddgs += sum(set_ddgs_fields)
                        set_total_maize += recipe.Oil1SetWt or 0
                        set_total_mbm += recipe.Oil2SetWt or 0
                        set_total_mdoc += recipe.Premix1Set or 0
                        set_total_oil += recipe.Premix2Set or 0

                # Error calculations
                def calc_error_pct(actual, expected):
                    return ((actual - expected) / expected * 100) if expected else 0

                error_soya = total_soya - set_total_soya
                error_ddgs = total_ddgs - set_total_ddgs
                error_maize = total_maize - set_total_maize
                error_mbm = total_mbm - set_total_mbm
                error_mdoc = total_mdoc - set_total_mdoc
                error_oil = total_oil - set_total_oil

                error_soya_pct = calc_error_pct(total_soya, set_total_soya)
                error_ddgs_pct = calc_error_pct(total_ddgs, set_total_ddgs)
                error_maize_pct = calc_error_pct(total_maize, set_total_maize)
                error_mbm_pct = calc_error_pct(total_mbm, set_total_mbm)
                error_mdoc_pct = calc_error_pct(total_mdoc, set_total_mdoc)
                error_oil_pct = calc_error_pct(total_oil, set_total_oil)

                # Totals
                set_total_all = sum([set_total_soya, set_total_ddgs, set_total_maize, set_total_mbm, set_total_mdoc, set_total_oil])
                total_all = sum([total_soya, total_ddgs, total_maize, total_mbm, total_mdoc, total_oil])
                error_total = total_all - set_total_all
                error_total_pct = calc_error_pct(total_all, set_total_all)

        except Exception as e:
            print("Error:", e)

    return render(request, 'daily-consumption-report.html', {
        'plants': plants,
        'plant_name': plant_name,
        'batch_data': batch_data,
        'start_date': start_date,
        'total_soya': total_soya,
        'total_ddgs': total_ddgs,
        'total_maize': total_maize,
        'total_mbm': total_mbm,
        'total_mdoc': total_mdoc,
        'total_oil': total_oil,
        'set_total_soya': set_total_soya,
        'set_total_ddgs': set_total_ddgs,
        'set_total_maize': set_total_maize,
        'set_total_mbm': set_total_mbm,
        'set_total_mdoc': set_total_mdoc,
        'set_total_oil': set_total_oil,
        'error_soya': error_soya,
        'error_ddgs': error_ddgs,
        'error_maize': error_maize,
        'error_mbm': error_mbm,
        'error_mdoc': error_mdoc,
        'error_oil': error_oil,
        'error_soya_pct': error_soya_pct,
        'error_ddgs_pct': error_ddgs_pct,
        'error_maize_pct': error_maize_pct,
        'error_mbm_pct': error_mbm_pct,
        'error_mdoc_pct': error_mdoc_pct,
        'error_oil_pct': error_oil_pct,
        'set_total_all': set_total_all,
        'total_all': total_all,
        'error_total': error_total,
        'error_total_pct': error_total_pct,
        'is_plant_owner': request.user.designation == 'plant_owner',
    })

@login_required
def daily_motor(request):
    plants = []
    recipe_ids = []
    motor_data = []
    plant_id = None
    start_date = None
    plant_name = None

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

    if request.method == "POST":
        start_date = request.POST.get('start_date')
        plant_id = request.POST.get('plant_id')

        try:
            if plant_id and start_date:
                plant_name = Plant.objects.filter(plant_id=plant_id).first()
                motor_data = MotorData.objects.filter(
                    plant_id=plant_id,
                    sdate=start_date
                )
        except Exception as e:
            print("Error:", e)

    return render(request, 'daily-motor-report.html', {
        'plant_name': plant_name,
        'plants': plants,
        'recipe_ids': recipe_ids,
        'motor_data': motor_data,
        'start_date': start_date,
        'is_plant_owner': request.user.designation == 'plant_owner',
    }) 

@login_required
def daily_bagging(request):
    plants = []
    recipe_ids = []
    bagging_data = []
    plant_id = None
    start_date = None
    plant_name = None

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

    if request.method == "POST":
        start_date = request.POST.get('start_date')
        plant_id = request.POST.get('plant_id')
        try:
            if plant_id and start_date:
                plant_name = Plant.objects.filter(plant_id=plant_id).first()
                bagging_data = BagData.objects.filter(
                    plant_id = plant_id,
                    sdate = start_date
                ) 
        except Exception as e:
            print("Error:", e)

    return render(request, 'daily-bagging-report.html', {
        'plant_name': plant_name,
        'plants': plants,
        'recipe_ids': recipe_ids,
        'bagging_data': bagging_data,
        'start_date': start_date,
        'is_plant_owner': request.user.designation == 'plant_owner',
    }) 

@login_required
def batch_shift(request):
    plants = []
    start_date = None
    batch_data = []
    recipe_ids = []
    batch_counts = []
    materialName = MaterialName.objects.all()
    plant_id = None
    shift = None
    plant_name=None

    # Get plants based on user role
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

    if request.method == "POST":
        start_date = request.POST.get('start_date')
        shift = request.POST.get('shift')
        plant_id = request.POST.get('plant_id')

        try:
            if plant_id and shift:
                # Get shift start time
                filter_kwargs = {
                    'plant_id': plant_id,
                    f'{shift}__isnull': False,
                }
                shift_data_qs = Plant.objects.filter(**filter_kwargs)

                if shift_data_qs.exists():
                    plant = shift_data_qs.first()
                    shift_start_time = getattr(plant, shift)

                    # Convert to datetime
                    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                    shift_start_dt = datetime.combine(start_date_obj, shift_start_time)
                    shift_end_dt = shift_start_dt + timedelta(hours=8)

                    # Step 1: Get all raw batch data by date
                    raw_batch_data = BatchData.objects.filter(
                        plant_id=plant_id,
                        stdate=start_date  # varchar match
                    )
                    plant_name = Plant.objects.filter(plant_id=request.POST.get('plant_id')).first()
                    # Step 2: Filter manually using parsed datetime
                    batch_data = []
                    for batch in raw_batch_data:
                        try:
                            full_datetime_str = f"{batch.stdate} {batch.stTime}"
                            batch_datetime = datetime.strptime(full_datetime_str, "%Y-%m-%d %H:%M:%S")

                            if shift_start_dt <= batch_datetime <= shift_end_dt:
                                batch_data.append(batch)
                        except Exception as e:
                            print(f"Skipping invalid datetime: {batch.stdate} {batch.stTime} | Error: {e}")

                    # Extract RecipeIDs
                    recipe_ids = list(set(b.RecipeID for b in batch_data if b.RecipeID))

                    # Get set weights from Recipemain
                    setWT = Recipemain.objects.filter(RecipeID__in=recipe_ids).annotate(
                        total_soya=Sum(
                            F('Bin1SetWt') + F('Bin2SetWt') + F('Bin3SetWt') + F('Bin4SetWt') +
                            F('Bin5SetWt') + F('Bin6SetWt') + F('Bin7SetWt') + F('Bin8SetWt') +
                            F('Bin9SetWt') + F('Bin10SetWt') + F('Bin11SetWt') + F('Bin12SetWt') +
                            F('Bin13SetWt') + F('Bin14SetWt') + F('Bin15SetWt') + F('Bin16SetWt')
                        ),
                        total_ddgs=Sum(
                            F('Man1SetWt') + F('Man2SetWt') + F('Man3SetWt') + F('Man4SetWt') +
                            F('Man5SetWt') + F('Man6SetWt') + F('Man7SetWt') + F('Man8SetWt') +
                            F('Man9SetWt') + F('Man10SetWt') + F('Man11SetWt') + F('Man12SetWt') +
                            F('Man13SetWt') + F('Man14SetWt') + F('Man15SetWt') + F('Man16SetWt')
                        ),
                        total_maize=F('Oil1SetWt'),
                        total_mbm=F('Oil2SetWt'),
                        total_mdoc=F('Premix1Set'),
                        total_oil1=F('Premix2Set'),
                    )

                    # Build batch count data
                    batch_counts = []
                    for rec in setWT:
                        related_batches = [b for b in batch_data if b.RecipeID == rec.RecipeID]
                        per_batch_data = []

                        for b in related_batches:
                            per_batch_data.append({
                                'BatchNum': b.BatchNum,
                                'stTime': b.stTime,
                                'total_soya': sum([
                                    b.Bin1Act, b.Bin2Act, b.Bin3Act, b.Bin4Act,
                                    b.Bin5Act, b.Bin6Act, b.Bin7Act, b.Bin8Act,
                                    b.Bin9Act, b.Bin10Act, b.Bin11Act, b.Bin12Act,
                                    b.Bin13Act, b.Bin14Act, b.Bin15Act, b.Bin16Act
                                ]),
                                'total_ddgs': sum([
                                    b.ManWt1, b.ManWt2, b.ManWt3, b.ManWt4,
                                    b.ManWt5, b.ManWt6, b.ManWt7, b.ManWt8,
                                    b.ManWt9, b.ManWt10, b.ManWt11, b.ManWt12,
                                    b.ManWt13, b.ManWt14, b.ManWt15, b.ManWt16
                                ]),
                                'Oil1SetWt': b.Oil1Act,
                                'Oil2SetWt': b.Oil2Act,
                                'Premix1Set': b.PremixWt1,
                                'Premix2Set': b.PremixWt2
                            })

                        batch_counts.append({
                            'RecipeID': rec.RecipeID,
                            'count': len(related_batches),
                            'total_soya': rec.total_soya,
                            'total_ddgs': rec.total_ddgs,
                            'Oil1SetWt': rec.total_maize,
                            'Oil2SetWt': rec.total_mbm,
                            'Premix1Set': rec.total_mdoc,
                            'Premix2Set': rec.total_oil1,
                            'actual_data': per_batch_data
                        })

        except Exception as e:
            print("Error:", e)

    return render(request, 'batch-shift-report.html', {
        'plants': plants,
        'batch_data': batch_data,
        'recipe_ids': recipe_ids,
        'batch_counts': batch_counts,
        'materialName': materialName,
        'start_date': start_date,
        'shift': shift,
        'plant_name':plant_name,
        'is_plant_owner': request.user.designation == 'plant_owner',
    })
     
@login_required
def recipe_shift(request):
    plants = []
    recipe_ids = []
    batch_data = []
    batch_actual = []
    plant_id = None
    start_date=None
    shift=None
    plant_name=None

    # Get plants based on user role
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
    if request.method == "POST":
        start_date = request.POST.get('start_date')
        shift = request.POST.get('shift')
        plant_id = request.POST.get('plant_id')

        try:
            if plant_id and shift:
                filter_kwargs = {
                    'plant_id': plant_id,
                    f'{shift}__isnull': False,
                }
                shift_data_qs = Plant.objects.filter(**filter_kwargs) 

                if shift_data_qs.exists():
                    plant = shift_data_qs.first()
                    shift_start_time = getattr(plant, shift) 
                    
                    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date() 
                    shift_start_dt = datetime.combine(start_date_obj, shift_start_time)
                    shift_end_dt = shift_start_dt + timedelta(hours=8)
                    raw_batch_data = BatchData.objects.filter(
                        plant_id=plant_id,
                        stdate=start_date  # varchar match
                    )
                    plant_name = Plant.objects.filter(plant_id=request.POST.get('plant_id')).first()
                    batch_data = []
                    for batch in raw_batch_data:
                        try:
                            full_datetime_str = f"{batch.stdate} {batch.stTime}"
                            batch_datetime = datetime.strptime(full_datetime_str, "%Y-%m-%d %H:%M:%S")

                            if shift_start_dt <= batch_datetime <= shift_end_dt:
                                batch_data.append(batch)
                        except Exception as e:
                            print(f"Skipping invalid datetime: {batch.stdate} {batch.stTime} | Error: {e}")

                    # Extract RecipeIDs
                recipe_ids = list(set(b.RecipeID for b in batch_data if b.RecipeID))
                recipe_data_dict = {
                    recipe.RecipeID: recipe for recipe in Recipemain.objects.filter(RecipeID__in=recipe_ids)
                }

                for item in batch_data:
                    # Calculate actuals
                    soya_fields = [getattr(item, f'Bin{i}Act') or 0 for i in range(1, 17)]
                    ddgs_fields = [getattr(item, f'ManWt{i}') or 0 for i in range(1, 17)]
                    total_soya = sum(soya_fields)
                    total_ddgs = sum(ddgs_fields)
                    total_maize = item.Oil1Act or 0
                    total_mbm = item.Oil2Act or 0
                    total_mdoc = item.PremixWt1 or 0
                    total_oil = item.PremixWt2 or 0

                    # Get set wt for this recipe
                    recipe = recipe_data_dict.get(item.RecipeID)
                    if recipe:
                        set_soya_fields = [getattr(recipe, f'Bin{i}SetWt') or 0 for i in range(1, 17)]
                        set_ddgs_fields = [getattr(recipe, f'Man{i}SetWt') or 0 for i in range(1, 21)]
                        set_total_soya = sum(set_soya_fields)
                        set_total_ddgs = sum(set_ddgs_fields)
                        set_total_maize = recipe.Oil1SetWt or 0
                        set_total_mbm = recipe.Oil2SetWt or 0
                        set_total_mdoc = recipe.Premix1Set or 0
                        set_total_oil = recipe.Premix2Set or 0

                        # Compute errors
                        def calc_error(actual, set_val):
                            error_kg = round(actual - set_val, 2)
                            error_pct = round((error_kg / set_val) * 100, 2) if set_val else 0
                            return error_kg, error_pct

                        item.recipe_name = recipe.recipename
                        item.set_total_soya = set_total_soya
                        item.total_soya = total_soya
                        item.error_soya, item.error_soya_pct = calc_error(total_soya, set_total_soya)

                        item.set_total_ddgs = set_total_ddgs
                        item.total_ddgs = total_ddgs
                        item.error_ddgs, item.error_ddgs_pct = calc_error(total_ddgs, set_total_ddgs)

                        item.set_total_maize = set_total_maize
                        item.total_maize = total_maize
                        item.error_maize, item.error_maize_pct = calc_error(total_maize, set_total_maize)

                        item.set_total_mbm = set_total_mbm
                        item.total_mbm = total_mbm
                        item.error_mbm, item.error_mbm_pct = calc_error(total_mbm, set_total_mbm)

                        item.set_total_mdoc = set_total_mdoc
                        item.total_mdoc = total_mdoc
                        item.error_mdoc, item.error_mdoc_pct = calc_error(total_mdoc, set_total_mdoc)

                        item.set_total_oil = set_total_oil
                        item.total_oil = total_oil
                        item.error_oil, item.error_oil_pct = calc_error(total_oil, set_total_oil)

                        item.set_total_all = set_total_soya + set_total_ddgs + set_total_maize + set_total_mbm + set_total_mdoc + set_total_oil
                        item.total_all = total_soya + total_ddgs + total_maize + total_mbm + total_mdoc + total_oil
                        item.error_total, item.error_total_pct = calc_error(item.total_all, item.set_total_all)

                        batch_actual.append(item)
                        

        except Exception as e:
            print("Error:", e)

    return render(request, 'recipe-shift-report.html', {
        'plant_name':plant_name,
        'plants': plants,
        'recipe_ids': recipe_ids,
        'batch_actual': batch_actual,
        'start_date': start_date,
        'shift':shift,
        'is_plant_owner': request.user.designation == 'plant_owner',
    })
    
@login_required
def consumption_shift(request):
    # Initialize all required variables
    plants = []
    batch_data = []
    recipe_ids = []
    plant_name=None
    # Form values
    start_date = None
    shift = None

    # Actual totals
    total_soya = total_ddgs = total_maize = total_mbm = total_mdoc = total_oil = 0

    # Set totals
    set_total_soya = set_total_ddgs = set_total_maize = set_total_mbm = set_total_mdoc = set_total_oil = 0

    # Errors
    error_soya = error_ddgs = error_maize = error_mbm = error_mdoc = error_oil = 0
    error_soya_pct = error_ddgs_pct = error_maize_pct = error_mbm_pct = error_mdoc_pct = error_oil_pct = 0
    set_total_all = total_all = error_total = error_total_pct = 0

    # Filter plants by user role
    if request.user.is_superuser:
        plants = Plant.objects.all()
    elif request.user.designation == 'manufacture':
        child_ids = request.session.get('child_ids', [])
        plants = Plant.objects.filter(plant_owner_id__in=child_ids)
    elif request.user.designation == 'plant_owner':
        plant = Plant.objects.filter(plant_owner_id=request.user.id).first()
        if plant:
            plants = [plant]

    if request.method == "POST":
        start_date = request.POST.get('start_date')
        shift = request.POST.get('shift')
        plant_id = request.POST.get('plant_id')

        try:
            if plant_id and shift:
                # Get shift time range
                filter_kwargs = {
                    'plant_id': plant_id,
                    f'{shift}__isnull': False,
                }
                shift_data_qs = Plant.objects.filter(**filter_kwargs)

                if shift_data_qs.exists():
                    plant = shift_data_qs.first()
                    shift_start_time = getattr(plant, shift)
                    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date() 
                    shift_start_dt = datetime.combine(start_date_obj, shift_start_time)
                    shift_end_dt = shift_start_dt + timedelta(hours=8)
                    raw_batch_data = BatchData.objects.filter(
                        plant_id=plant_id,
                        stdate=start_date  # varchar match
                    )
                    plant_name = Plant.objects.filter(plant_id=request.POST.get('plant_id')).first()
                    # Fetch batch data
                    batch_data = []
                    for batch in raw_batch_data:
                        try:
                            full_datetime_str = f"{batch.stdate} {batch.stTime}"
                            batch_datetime = datetime.strptime(full_datetime_str, "%Y-%m-%d %H:%M:%S")

                            if shift_start_dt <= batch_datetime <= shift_end_dt:
                                batch_data.append(batch)
                        except Exception as e:
                            print(f"Skipping invalid datetime: {batch.stdate} {batch.stTime} | Error: {e}")

                    # Extract RecipeIDs
                    recipe_ids = list(set(b.RecipeID for b in batch_data if b.RecipeID))
                    recipe_data_dict = {
                        recipe.RecipeID: recipe for recipe in Recipemain.objects.filter(RecipeID__in=recipe_ids)
                    }

                    # Process each batch record
                    for item in batch_data:
                        # Actual weights
                        soya_fields = [getattr(item, f'Bin{i}Act') or 0 for i in range(1, 17)]
                        ddgs_fields = [getattr(item, f'ManWt{i}') or 0 for i in range(1, 17)]
                        total_soya += sum(soya_fields)
                        total_ddgs += sum(ddgs_fields)
                        total_maize += item.Oil1Act or 0
                        total_mbm += item.Oil2Act or 0
                        total_mdoc += item.PremixWt1 or 0
                        total_oil += item.PremixWt2 or 0

                        # Set weights from recipe
                        recipe = recipe_data_dict.get(item.RecipeID)
                        if recipe:
                            set_soya_fields = [getattr(recipe, f'Bin{i}SetWt') or 0 for i in range(1, 17)]
                            set_ddgs_fields = [getattr(recipe, f'Man{i}SetWt') or 0 for i in range(1, 21)]
                            set_total_soya += sum(set_soya_fields)
                            set_total_ddgs += sum(set_ddgs_fields)
                            set_total_maize += recipe.Oil1SetWt or 0
                            set_total_mbm += recipe.Oil2SetWt or 0
                            set_total_mdoc += recipe.Premix1Set or 0
                            set_total_oil += recipe.Premix2Set or 0

                    # Error calculations
                    def calc_error_pct(actual, expected):
                        return ((actual - expected) / expected * 100) if expected else 0

                    error_soya = total_soya - set_total_soya
                    error_ddgs = total_ddgs - set_total_ddgs
                    error_maize = total_maize - set_total_maize
                    error_mbm = total_mbm - set_total_mbm
                    error_mdoc = total_mdoc - set_total_mdoc
                    error_oil = total_oil - set_total_oil

                    error_soya_pct = calc_error_pct(total_soya, set_total_soya)
                    error_ddgs_pct = calc_error_pct(total_ddgs, set_total_ddgs)
                    error_maize_pct = calc_error_pct(total_maize, set_total_maize)
                    error_mbm_pct = calc_error_pct(total_mbm, set_total_mbm)
                    error_mdoc_pct = calc_error_pct(total_mdoc, set_total_mdoc)
                    error_oil_pct = calc_error_pct(total_oil, set_total_oil)

                    # Totals
                    set_total_all = sum([set_total_soya, set_total_ddgs, set_total_maize, set_total_mbm, set_total_mdoc, set_total_oil])
                    total_all = sum([total_soya, total_ddgs, total_maize, total_mbm, total_mdoc, total_oil])
                    error_total = total_all - set_total_all
                    error_total_pct = calc_error_pct(total_all, set_total_all)

        except Exception as e:
            print("Error:", e)

    return render(request, 'consumption-shift-report.html', {
        'plants': plants,
        'plant_name':plant_name,
        'batch_data': batch_data,
        'start_date': start_date,
        'shift': shift,
        'total_soya': total_soya,
        'total_ddgs': total_ddgs,
        'total_maize': total_maize,
        'total_mbm': total_mbm,
        'total_mdoc': total_mdoc,
        'total_oil': total_oil,
        'set_total_soya': set_total_soya,
        'set_total_ddgs': set_total_ddgs,
        'set_total_maize': set_total_maize,
        'set_total_mbm': set_total_mbm,
        'set_total_mdoc': set_total_mdoc,
        'set_total_oil': set_total_oil,
        'error_soya': error_soya,
        'error_ddgs': error_ddgs,
        'error_maize': error_maize,
        'error_mbm': error_mbm,
        'error_mdoc': error_mdoc,
        'error_oil': error_oil,
        'error_soya_pct': error_soya_pct,
        'error_ddgs_pct': error_ddgs_pct,
        'error_maize_pct': error_maize_pct,
        'error_mbm_pct': error_mbm_pct,
        'error_mdoc_pct': error_mdoc_pct,
        'error_oil_pct': error_oil_pct,
        'set_total_all': set_total_all,
        'total_all': total_all,
        'error_total': error_total,
        'error_total_pct': error_total_pct,
        'is_plant_owner': request.user.designation == 'plant_owner',
    })

@login_required
def custom_batch(request):
    plants = []
    start_date=None
    end_date=None
    batch_data = []
    recipe_ids = []
    batch_counts = []
    materialName = MaterialName.objects.all()
    plant_id = None

   # Get plants based on user role
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
    if request.method == "POST":
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        plant_id = request.POST.get('plant_id')
        
        try:
            if plant_id and start_date and end_date:
                batch_data = BatchData.objects.filter(
                    plant_id=plant_id,
                    stdate__range=(start_date, end_date)
                )

                recipe_ids = batch_data.values_list('RecipeID', flat=True).distinct()

                recipe_ids = batch_data.values_list('RecipeID', flat=True).distinct()

                # Get set weights from Recipemain
                setWT = Recipemain.objects.filter(RecipeID__in=recipe_ids).annotate(
                    total_soya=Sum(
                        F('Bin1SetWt') + F('Bin2SetWt') + F('Bin3SetWt') + F('Bin4SetWt') +
                        F('Bin5SetWt') + F('Bin6SetWt') + F('Bin7SetWt') + F('Bin8SetWt') +
                        F('Bin9SetWt') + F('Bin10SetWt') + F('Bin11SetWt') + F('Bin12SetWt') +
                        F('Bin13SetWt') + F('Bin14SetWt') + F('Bin15SetWt') + F('Bin16SetWt')
                    ),
                    total_ddgs=Sum(
                        F('Man1SetWt') + F('Man2SetWt') + F('Man3SetWt') + F('Man4SetWt') +
                        F('Man5SetWt') + F('Man6SetWt') + F('Man7SetWt') + F('Man8SetWt') +
                        F('Man9SetWt') + F('Man10SetWt') + F('Man11SetWt') + F('Man12SetWt') +
                        F('Man13SetWt') + F('Man14SetWt') + F('Man15SetWt') + F('Man16SetWt')
                    ),
                    total_maize=F('Oil1SetWt'),
                    total_mbm=F('Oil2SetWt'),
                    total_mdoc=F('Premix1Set'),
                    total_oil1=F('Premix2Set'),
                )

                # Build final batch_counts structure for the template
                batch_counts = []
                for rec in setWT:
                    related_batches = batch_data.filter(RecipeID=rec.RecipeID)
                    per_batch_data = []

                    for b in related_batches:
                        per_batch_data.append({
                            'BatchNum': b.BatchNum,
                            'stTime': b.stTime,
                            'total_soya': (
                                b.Bin1Act + b.Bin2Act + b.Bin3Act + b.Bin4Act +
                                b.Bin5Act + b.Bin6Act + b.Bin7Act + b.Bin8Act +
                                b.Bin9Act + b.Bin10Act + b.Bin11Act + b.Bin12Act +
                                b.Bin13Act + b.Bin14Act + b.Bin15Act + b.Bin16Act
                            ),
                            'total_ddgs': (
                                b.ManWt1 + b.ManWt2 + b.ManWt3 + b.ManWt4 +
                                b.ManWt5 + b.ManWt6 + b.ManWt7 + b.ManWt8 +
                                b.ManWt9 + b.ManWt10 + b.ManWt11 + b.ManWt12 +
                                b.ManWt13 + b.ManWt14 + b.ManWt15 + b.ManWt16
                            ),
                            'Oil1SetWt': b.Oil1Act,
                            'Oil2SetWt': b.Oil2Act,
                            'Premix1Set': b.PremixWt1,
                            'Premix2Set': b.PremixWt2
                        })

                    batch_counts.append({
                        'RecipeID': rec.RecipeID,
                        'count': related_batches.count(),
                        'total_soya': rec.total_soya,
                        'total_ddgs': rec.total_ddgs,
                        'Oil1SetWt': rec.total_maize,
                        'Oil2SetWt': rec.total_mbm,
                        'Premix1Set': rec.total_mdoc,
                        'Premix2Set': rec.total_oil1,
                        'actual_data': per_batch_data
                    })

        except Exception as e:
            print("Error:", e)

    return render(request, 'custom-batch-report.html', {
        'plants': plants,
        'batch_data': batch_data,
        'recipe_ids': recipe_ids,
        'batch_counts': batch_counts,
        'materialName': materialName,
        'start_date':start_date,
        'end_date':end_date,
        'is_plant_owner': request.user.designation == 'plant_owner',
    }) 

@login_required
def custom_recipe(request):
    plants = []
    recipe_ids = []
    batch_data = []
    batch_actual = []
    plant_id = None
    start_date=None
    end_date=None 
    plant_name=None

    # Get plants based on user role
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
    if request.method == "POST":
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        plant_id = request.POST.get('plant_id')
        try:
            if plant_id and start_date and end_date:
                plant_name = Plant.objects.filter(plant_id=request.POST.get('plant_id')).first()
                batch_data = BatchData.objects.filter(
                    plant_id=plant_id,
                    stdate__range=(start_date, end_date)
                )            

                recipe_ids = batch_data.values_list('RecipeID', flat=True).distinct()
                recipe_data_dict = {
                    recipe.RecipeID: recipe for recipe in Recipemain.objects.filter(RecipeID__in=recipe_ids)
                }

                for item in batch_data:
                    # Calculate actuals
                    soya_fields = [getattr(item, f'Bin{i}Act') or 0 for i in range(1, 17)]
                    ddgs_fields = [getattr(item, f'ManWt{i}') or 0 for i in range(1, 17)]
                    total_soya = sum(soya_fields)
                    total_ddgs = sum(ddgs_fields)
                    total_maize = item.Oil1Act or 0
                    total_mbm = item.Oil2Act or 0
                    total_mdoc = item.PremixWt1 or 0
                    total_oil = item.PremixWt2 or 0

                    # Get set wt for this recipe
                    recipe = recipe_data_dict.get(item.RecipeID)
                    if recipe:
                        set_soya_fields = [getattr(recipe, f'Bin{i}SetWt') or 0 for i in range(1, 17)]
                        set_ddgs_fields = [getattr(recipe, f'Man{i}SetWt') or 0 for i in range(1, 21)]
                        set_total_soya = sum(set_soya_fields)
                        set_total_ddgs = sum(set_ddgs_fields)
                        set_total_maize = recipe.Oil1SetWt or 0
                        set_total_mbm = recipe.Oil2SetWt or 0
                        set_total_mdoc = recipe.Premix1Set or 0
                        set_total_oil = recipe.Premix2Set or 0

                        # Compute errors
                        def calc_error(actual, set_val):
                            error_kg = round(actual - set_val, 2)
                            error_pct = round((error_kg / set_val) * 100, 2) if set_val else 0
                            return error_kg, error_pct

                        item.recipe_name = recipe.recipename
                        item.set_total_soya = set_total_soya
                        item.total_soya = total_soya
                        item.error_soya, item.error_soya_pct = calc_error(total_soya, set_total_soya)

                        item.set_total_ddgs = set_total_ddgs
                        item.total_ddgs = total_ddgs
                        item.error_ddgs, item.error_ddgs_pct = calc_error(total_ddgs, set_total_ddgs)

                        item.set_total_maize = set_total_maize
                        item.total_maize = total_maize
                        item.error_maize, item.error_maize_pct = calc_error(total_maize, set_total_maize)

                        item.set_total_mbm = set_total_mbm
                        item.total_mbm = total_mbm
                        item.error_mbm, item.error_mbm_pct = calc_error(total_mbm, set_total_mbm)

                        item.set_total_mdoc = set_total_mdoc
                        item.total_mdoc = total_mdoc
                        item.error_mdoc, item.error_mdoc_pct = calc_error(total_mdoc, set_total_mdoc)

                        item.set_total_oil = set_total_oil
                        item.total_oil = total_oil
                        item.error_oil, item.error_oil_pct = calc_error(total_oil, set_total_oil)

                        item.set_total_all = set_total_soya + set_total_ddgs + set_total_maize + set_total_mbm + set_total_mdoc + set_total_oil
                        item.total_all = total_soya + total_ddgs + total_maize + total_mbm + total_mdoc + total_oil
                        item.error_total, item.error_total_pct = calc_error(item.total_all, item.set_total_all)

                        batch_actual.append(item)
                        

        except Exception as e:
            print("Error:", e)

    return render(request, 'custom-recipe-report.html', {
        'plant_name':plant_name,
        'plants': plants,
        'recipe_ids': recipe_ids,
        'batch_actual': batch_actual,
        'start_date': start_date,
        'end_date': end_date,
        'is_plant_owner': request.user.designation == 'plant_owner',
    })  

@login_required
def custom_consumption(request):
    # Initialize all required variables
    plants = []
    batch_data = []
    recipe_ids = []
    plant_name=None
    # Form values
    start_date = None
    end_date = None

    # Actual totals
    total_soya = total_ddgs = total_maize = total_mbm = total_mdoc = total_oil = 0

    # Set totals
    set_total_soya = set_total_ddgs = set_total_maize = set_total_mbm = set_total_mdoc = set_total_oil = 0

    # Errors
    error_soya = error_ddgs = error_maize = error_mbm = error_mdoc = error_oil = 0
    error_soya_pct = error_ddgs_pct = error_maize_pct = error_mbm_pct = error_mdoc_pct = error_oil_pct = 0
    set_total_all = total_all = error_total = error_total_pct = 0

    # Filter plants by user role
    if request.user.is_superuser:
        plants = Plant.objects.all()
    elif request.user.designation == 'manufacture':
        child_ids = request.session.get('child_ids', [])
        plants = Plant.objects.filter(plant_owner_id__in=child_ids)
    elif request.user.designation == 'plant_owner':
        plant = Plant.objects.filter(plant_owner_id=request.user.id).first()
        if plant:
            plants = [plant]

    if request.method == "POST":
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        plant_id = request.POST.get('plant_id')

        try:
                if plant_id and start_date and end_date:
                    plant_name = Plant.objects.filter(plant_id=request.POST.get('plant_id')).first()
                    batch_data = BatchData.objects.filter(
                        plant_id=plant_id,
                        stdate__range=(start_date, end_date)
                    )
                    
                    recipe_ids = batch_data.values_list('RecipeID', flat=True).distinct()
                    recipe_data_dict = {
                        recipe.RecipeID: recipe for recipe in Recipemain.objects.filter(RecipeID__in=recipe_ids)
                    }

                    # Process each batch record
                    for item in batch_data:
                        # Actual weights
                        soya_fields = [getattr(item, f'Bin{i}Act') or 0 for i in range(1, 17)]
                        ddgs_fields = [getattr(item, f'ManWt{i}') or 0 for i in range(1, 17)]
                        total_soya += sum(soya_fields)
                        total_ddgs += sum(ddgs_fields)
                        total_maize += item.Oil1Act or 0
                        total_mbm += item.Oil2Act or 0
                        total_mdoc += item.PremixWt1 or 0
                        total_oil += item.PremixWt2 or 0

                        # Set weights from recipe
                        recipe = recipe_data_dict.get(item.RecipeID)
                        if recipe:
                            set_soya_fields = [getattr(recipe, f'Bin{i}SetWt') or 0 for i in range(1, 17)]
                            set_ddgs_fields = [getattr(recipe, f'Man{i}SetWt') or 0 for i in range(1, 21)]
                            set_total_soya += sum(set_soya_fields)
                            set_total_ddgs += sum(set_ddgs_fields)
                            set_total_maize += recipe.Oil1SetWt or 0
                            set_total_mbm += recipe.Oil2SetWt or 0
                            set_total_mdoc += recipe.Premix1Set or 0
                            set_total_oil += recipe.Premix2Set or 0

                    # Error calculations
                    def calc_error_pct(actual, expected):
                        return ((actual - expected) / expected * 100) if expected else 0

                    error_soya = total_soya - set_total_soya
                    error_ddgs = total_ddgs - set_total_ddgs
                    error_maize = total_maize - set_total_maize
                    error_mbm = total_mbm - set_total_mbm
                    error_mdoc = total_mdoc - set_total_mdoc
                    error_oil = total_oil - set_total_oil

                    error_soya_pct = calc_error_pct(total_soya, set_total_soya)
                    error_ddgs_pct = calc_error_pct(total_ddgs, set_total_ddgs)
                    error_maize_pct = calc_error_pct(total_maize, set_total_maize)
                    error_mbm_pct = calc_error_pct(total_mbm, set_total_mbm)
                    error_mdoc_pct = calc_error_pct(total_mdoc, set_total_mdoc)
                    error_oil_pct = calc_error_pct(total_oil, set_total_oil)

                    # Totals
                    set_total_all = sum([set_total_soya, set_total_ddgs, set_total_maize, set_total_mbm, set_total_mdoc, set_total_oil])
                    total_all = sum([total_soya, total_ddgs, total_maize, total_mbm, total_mdoc, total_oil])
                    error_total = total_all - set_total_all
                    error_total_pct = calc_error_pct(total_all, set_total_all)

        except Exception as e:
            print("Error:", e)

    return render(request, 'custom-consumption-report.html', {
        'plants': plants,
        'plant_name':plant_name,
        'batch_data': batch_data,
        'start_date': start_date,
        'end_date': end_date,
        'total_soya': total_soya,
        'total_ddgs': total_ddgs,
        'total_maize': total_maize,
        'total_mbm': total_mbm,
        'total_mdoc': total_mdoc,
        'total_oil': total_oil,
        'set_total_soya': set_total_soya,
        'set_total_ddgs': set_total_ddgs,
        'set_total_maize': set_total_maize,
        'set_total_mbm': set_total_mbm,
        'set_total_mdoc': set_total_mdoc,
        'set_total_oil': set_total_oil,
        'error_soya': error_soya,
        'error_ddgs': error_ddgs,
        'error_maize': error_maize,
        'error_mbm': error_mbm,
        'error_mdoc': error_mdoc,
        'error_oil': error_oil,
        'error_soya_pct': error_soya_pct,
        'error_ddgs_pct': error_ddgs_pct,
        'error_maize_pct': error_maize_pct,
        'error_mbm_pct': error_mbm_pct,
        'error_mdoc_pct': error_mdoc_pct,
        'error_oil_pct': error_oil_pct,
        'set_total_all': set_total_all,
        'total_all': total_all,
        'error_total': error_total,
        'error_total_pct': error_total_pct,
        'is_plant_owner': request.user.designation == 'plant_owner',
    })    
    
@login_required
def custom_motor(request):
    plants = []
    recipe_ids = []
    motor_data = []
    plant_id = None
    start_date = None
    end_date = None 
    plant_name = None

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

    if request.method == "POST":
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        plant_id = request.POST.get('plant_id')

        try:
            if plant_id and start_date and end_date:
                plant_name = Plant.objects.filter(plant_id=plant_id).first()
                motor_data = MotorData.objects.filter(
                    plant_id=plant_id,
                    sdate__range=[start_date, end_date]
                ) 
        except Exception as e:
            print("Error:", e)

    return render(request, 'custom-motor-report.html', {
        'plant_name': plant_name,
        'plants': plants,
        'recipe_ids': recipe_ids,
        'motor_data': motor_data,
        'start_date': start_date,
        'end_date': end_date,
        'is_plant_owner': request.user.designation == 'plant_owner',
    })  
    
@login_required
def custom_baging(request):
    plants = []
    recipe_ids = []
    bagging_data = []
    plant_id = None
    start_date = None
    end_date = None 
    plant_name = None

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

    if request.method == "POST":
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        plant_id = request.POST.get('plant_id')
        print(start_date)
        try:
            if plant_id and start_date and end_date:
                plant_name = Plant.objects.filter(plant_id=plant_id).first()
                bagging_data = BagData.objects.filter(
                    plant_id=plant_id,
                    sdate__range=[start_date, end_date]
                ) 
                print(bagging_data)
        except Exception as e:
            print("Error:", e)

    return render(request, 'custom-bagging-report.html', {
        'plant_name': plant_name,
        'plants': plants,
        'recipe_ids': recipe_ids,
        'bagging_data': bagging_data,
        'start_date': start_date,
        'end_date': end_date,
        'is_plant_owner': request.user.designation == 'plant_owner',
    })  
    
@login_required
def summary_reports(request):
    plants = Plant.objects.all()   
    plant = None
    start_date = end_date = None
    batch_data = BatchData.objects.none()
    start_date = finish_date = None
    from_date_str = to_date_str = None
    unique_recipe_data = None
    shift = request.POST.get('shift')
    plant_id = request.POST.get('plant_id')
    hammer_stats = pellet_stats = {}
    motor_data = []
    plant_name=None
    
     # Get plants based on user role
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
    if request.method == "POST":
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        plant_id = request.POST.get('plant_id')    

    try:
            if plant_id and start_date and end_date:
                plant_name = Plant.objects.filter(plant_id=request.POST.get('plant_id')).first()
                batch_data = BatchData.objects.filter(
                    plant_id=plant_id,
                    stdate__range=(start_date, end_date)
                )  

                # Calculate recipe weight
                recipe_weight_expr = ExpressionWrapper(
                    F('Bin1SetWt') + F('Bin2SetWt') + F('Bin3SetWt') +
                    F('Bin4SetWt') + F('Bin5SetWt') + F('Bin6SetWt') +
                    F('Bin7SetWt') + F('Bin8SetWt') + F('Bin9SetWt') +
                    F('Bin10SetWt') + F('Bin11SetWt') + F('Bin12SetWt') +
                    F('Bin13SetWt') + F('Bin14SetWt') + F('Bin15SetWt') + F('Bin16SetWt') +
                    F('Oil1SetWt') + F('Oil2SetWt') + F('MedSetWt') +
                    F('MolassesSetWt') + F('Premix1Set') + F('Premix2Set') +
                    F('Man1SetWt') + F('Man2SetWt') + F('Man3SetWt') +
                    F('Man4SetWt') + F('Man5SetWt') + F('Man6SetWt') +
                    F('Man7SetWt') + F('Man8SetWt') + F('Man9SetWt') +
                    F('Man10SetWt') + F('Man11SetWt') + F('Man12SetWt'),
                    output_field=FloatField()
                )

                recipe_subquery = Recipemain.objects.filter(RecipeID=OuterRef('RecipeID')).annotate(
                    total_weight=recipe_weight_expr
                ).values('total_weight')[:1]

                unique_recipe_data = batch_data.values('RecipeID') \
                    .annotate(
                        First_RecipeName=Min('RecipeName'),
                        Last_RecipeName=Max('RecipeName'),
                        batch_count=Count('RecipeID'),
                        start_time=Min('stTime'),
                        end_time=Min('endTime'),
                        total_recipe_weight=Subquery(recipe_subquery)
                    ).order_by('RecipeID')

                for item in unique_recipe_data:
                    st_time = item['start_time']
                    end_time = item['end_time']
                    if isinstance(st_time, str):
                        st_time = datetime.strptime(st_time, '%H:%M:%S')
                    if isinstance(end_time, str):
                        end_time = datetime.strptime(end_time, '%H:%M:%S')
                    if st_time and end_time:
                        time_diff = end_time - st_time
                        if time_diff.total_seconds() < 0:
                            time_diff += timedelta(days=1)
                        total_seconds = int(time_diff.total_seconds())
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        seconds = total_seconds % 60
                        item['total_time'] = f'{hours:02}:{minutes:02}:{seconds:02}'
                    else:
                        item['total_time'] = '00:00:00'

                # Handle motor data
                date_list = batch_data.values_list('stdate').distinct()
                motor_data_raw = MotorData.objects.filter(
                    plant_id=plant_id,
                    sdate__in=date_list
                ).order_by('sdate', 'sTime')
                for row in motor_data_raw:
                    dt = parse_datetime(row.sdate, row.sTime)
                    if dt:
                        row._datetime = dt
                        motor_data.append(row)

                start_time = motor_data[0]._datetime if motor_data else None
                end_time = motor_data[-1]._datetime if motor_data else None
                runtime_minutes = safe_round((end_time - start_time).total_seconds() / 60) if start_time and end_time else None

                hammer = [m for m in motor_data if m.rvfrpm > 0]
                hammer_avg = sum(m.rvfrpm for m in hammer) / len(hammer) if hammer else 0
                hammer_load = sum(m.hammercurrent for m in hammer) / len(hammer) if hammer else 0
                hammer_stats = {
                    'hammer_avg': safe_round(hammer_avg),
                    'hammer_efficiency': safe_round((hammer_avg / 1800) * 100) if hammer_avg else None,
                    'avg_load': safe_round(hammer_load),
                    'start_time': start_time,
                    'end_time': end_time,
                    'runtime_minutes': runtime_minutes,
                    'hammer_count': len(hammer)
                }

                pellet = [m for m in motor_data if m.feederRPM > 0]
                pellet_avg = sum(m.rvfrpm for m in pellet) / len(pellet) if pellet else 0
                pellet_load = sum(m.pelletcurrent for m in pellet) / len(pellet) if pellet else 0
                pellet_stats = {
                    'pellet_avg': safe_round(pellet_avg),
                    'pellet_efficiency': safe_round((pellet_avg / 1500) * 100) if pellet_avg else None,
                    'avg_load': safe_round(pellet_load),
                    'start_time': start_time,
                    'end_time': end_time,
                    'runtime_minutes': runtime_minutes,
                    'pellet_count': len(pellet)
                }

                start_date = start_time.date() if start_time else None
                finish_date = end_time.date() if end_time else None

    except Exception as e:
        print("Error:", e)

    return render(request, 'summary-report.html', {
        'plant': plant,
        'plants': plants,
        'unique_recipe_data': unique_recipe_data,
        'start_date': start_date,
        'end_date': end_date,
        'hammer_stats': hammer_stats,
        'pellet_stats': pellet_stats,
        'from_datetime': from_date_str,
        'to_datetime': to_date_str,
        'plant_name':plant_name,
    })
    
    