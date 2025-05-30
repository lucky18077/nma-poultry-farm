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
import string
from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Min, Max,Count,F, ExpressionWrapper, FloatField,OuterRef, Subquery,Sum
from django.db.models.functions import Cast
from django.contrib.auth import get_user_model
from django.utils.timezone import make_aware
from django.utils.dateparse import parse_datetime
from django.db.models import Q
User = get_user_model()
import os
from datetime import date
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.forms.models import model_to_dict

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
                user.password

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
        plant_status = request.POST.get('plant_status')
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
            plant.plant_status = plant_status
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
             
            def generate_unique_plant_key():
                charset = string.ascii_letters + string.digits + string.punctuation
                while True:
                    generated_plant_key = ''.join(random.choices(charset, k=25))
                    if not Plant.objects.filter(plant_key=generated_plant_key).exists():
                        return generated_plant_key  
                    
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
                plant_key=generate_unique_plant_key(),
                plant_name=plant_name,
                plant_status=plant_status,
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
    select_date = date.today().isoformat()
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
        'select_date':select_date,
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
    start_date = date.today().isoformat()
    plant_id = None
    plant_name = None
    batch_data = []
    filtered_data = []
    material_name_list = []

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
                plant_name = Plant.objects.filter(plant_id=plant_id).first()
                batch_data = BatchData.objects.filter(plant_id=plant_id, stdate=start_date)

                # Count batches per RecipeID
                batch_counts = batch_data.values('RecipeID').annotate(count=Count('RecipeID'))
                batch_count_dict = {item['RecipeID']: item['count'] for item in batch_counts}
                recipe_ids = batch_data.values_list('RecipeID', flat=True).distinct()

                recipes = Recipemain.objects.filter(RecipeID__in=recipe_ids)
                bin_data = BinName.objects.filter(recipeID__in=recipe_ids)

                # Map RecipeID to materials with SetWt > 0
                recipe_material_map = {}
                all_mat_ids = set()

                for bin_row in bin_data:
                    recipe_id = bin_row.recipeID
                    recipe_material_map[recipe_id] = []

                    recipe = next((r for r in recipes if r.RecipeID == recipe_id), None)
                    if not recipe:
                        continue
                    rec_dict = model_to_dict(recipe)
                    bin_dict = model_to_dict(bin_row)

                    fields_bins = [f'bin{i}' for i in range(1, 17)]
                    fields_man = [f'man{i}' for i in range(1, 21)]
                    fields_oil = ['oil1', 'oil2']
                    fields_prem_meds = ['medicine', 'premix1', 'premix2']

                    # Process bins
                    for i, field in enumerate(fields_bins, 1):
                        mat_id = bin_dict.get(field)
                        if mat_id is not None:
                            setwt = rec_dict.get(f'Bin{i}SetWt')
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)
                    # Process man
                    for i, field in enumerate(fields_man, 1):
                        mat_id = bin_dict.get(field)
                        if mat_id is not None:
                            setwt = rec_dict.get(f'Man{i}SetWt', 0)
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                    # Process oils
                    for oil in fields_oil:
                        mat_id = bin_dict.get(oil)
                        if mat_id is not None:
                            setwt = rec_dict.get(f'{oil.capitalize()}SetWt', 0)
                            if setwt:
                                recipe_material_map[recipe_id].append((oil, mat_id))
                                all_mat_ids.add(mat_id)

                    # Process premixes and medicine
                    for field in fields_prem_meds:
                        mat_id = bin_dict.get(field)
                        if mat_id is not None:
                            if field == 'medicine':
                                setwt = rec_dict.get('MedSetWt', 0)
                            else:
                                setwt = rec_dict.get(f'{field.capitalize()}Set', 0)
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                materials = MaterialName.objects.filter(MatID__in=all_mat_ids)
                material_dict = {m.MatID: m.MatName for m in materials}

                # Order materials without duplicates (by first appearance in any recipe)
                seen = set()
                material_name_list = []
                material_order = []
                for mats in recipe_material_map.values():
                    for _, mat_id in mats:
                        if mat_id not in seen:
                            seen.add(mat_id)
                            material_name_list.append(material_dict.get(mat_id, f"MatID {mat_id}"))
                            material_order.append(mat_id)

                bin_data_dict = {row.recipeID: model_to_dict(row) for row in bin_data}
                for recipe in recipes:
                    rec_dict = model_to_dict(recipe)
                    bin_row = bin_data_dict.get(recipe.RecipeID, {})
                    material_wt_map = {}

                    for i in range(1, 17):
                        mat_id = bin_row.get(f'bin{i}')
                        if mat_id is not None:
                            wt = rec_dict.get(f'Bin{i}SetWt', 0)
                            if wt > 0:
                                material_wt_map[mat_id] = wt
                    for i in range(1, 21):
                        mat_id = bin_row.get(f'man{i}')
                        if mat_id and mat_id != 0:
                            wt = rec_dict.get(f'Man{i}SetWt', 0)
                            if wt > 0:
                                material_wt_map[mat_id] = wt

                    for oil in ['oil1', 'oil2']:
                        mat_id = bin_row.get(oil)
                        if mat_id and mat_id != 0:
                            wt = rec_dict.get(f'{oil.capitalize()}SetWt', 0)
                            if wt > 0:
                                material_wt_map[mat_id] = wt

                    for prem in ['premix1', 'premix2']:
                        mat_id = bin_row.get(prem)
                        if mat_id and mat_id != 0:
                            wt = rec_dict.get(f'{prem.capitalize()}Set', 0)
                            if wt > 0:
                                material_wt_map[mat_id] = wt

                    med = bin_row.get('medicine')
                    if med and med != 0:
                        wt = rec_dict.get('MedSetWt', 0)
                        if wt > 0:
                            material_wt_map[med] = wt

                    row_data = [material_wt_map.get(mat_id, 0.0) for mat_id in material_order]

                    # Actual batches for this recipe
                    recipe_batches = batch_data.filter(RecipeID=recipe.RecipeID)

                    actual_batches = []

                    for batch in recipe_batches:
                        batch_dict = model_to_dict(batch)
                        bin_row = bin_data_dict.get(batch.RecipeID, {})
                        actual_map = {}

                        for i in range(1, 17):
                            mat_id = bin_row.get(f'bin{i}')
                            if mat_id is not None:
                                val = batch_dict.get(f'Bin{i}Act')
                                if val is not None and not (val == 0):
                                    actual_map[mat_id] = val

                        for i in range(1, 21):
                            mat_id = bin_row.get(f'man{i}')
                            if mat_id :
                                val = batch_dict.get(f'ManWt{i}')
                                if val is not None and not (val == 0):
                                    actual_map[mat_id] = val

                        for oil in ['oil1', 'oil2']:
                            mat_id = bin_row.get(oil)
                            if mat_id :
                                val = batch_dict.get(f'{oil.capitalize()}Act', 0)
                                actual_map[mat_id] = val

                        premix1_id = bin_row.get('premix1')
                        if premix1_id :
                            val = getattr(batch, 'PremixWt1', 0)
                            actual_map[premix1_id] = val

                        premix2_id = bin_row.get('premix2')
                        if premix2_id :
                            val = getattr(batch, 'PremixWt2', 0)
                            actual_map[premix2_id] = val

                        medicine_id = bin_row.get('medicine')
                        if medicine_id :
                            val = getattr(batch, 'MedicineWt', 0)
                            actual_map[medicine_id] = val

                        row_actual = [actual_map.get(mat_id, 0.0) for mat_id in material_order]
                        print(row_actual)
                        actual_batches.append({
                            'batch_no': batch.BatchNum,
                            'start_time': batch.stTime,
                            'values': row_actual,
                        })
                    filtered_data.append({
                        "RecipeID": recipe.RecipeID,
                        "RecipeName": recipe.recipename,
                        "SetWt": rec_dict.get('SetWt'),
                        "ActWt": rec_dict.get('ActWt'),
                        "BatchCount": batch_count_dict.get(recipe.RecipeID, 0),
                        "Materials": row_data,
                        "ActualBatches": actual_batches,
                    })

        except Exception as e:
            print(f"Error in daily_batch: {e}")

    return render(request, 'daily-batch-report.html', {
        'plants': plants,
        'start_date': start_date,
        'plant_id': plant_id,
        'plant_name': plant_name,
        'batch_data': batch_data,
        'filtered_data': filtered_data,
        'material_name_list': material_name_list,
    })

@login_required
def daily_recipe(request):
    plants = []
    recipe_ids = []
    batch_data = []
    batch_actual = []
    plant_id = None
    start_date = date.today().isoformat()
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
                batch_data = BatchData.objects.filter(
                    plant_id=plant_id,
                    stdate=start_date
                )
                batch_counts = batch_data.values('RecipeID').annotate(count=Count('RecipeID'))
                batch_count_dict = {item['RecipeID']: item['count'] for item in batch_counts}
                recipe_ids = batch_data.values_list('RecipeID', flat=True).distinct()
                recipes = Recipemain.objects.filter(RecipeID__in=recipe_ids)
                bin_data = BinName.objects.filter(recipeID__in=recipe_ids)

                recipe_material_map = {}
                all_mat_ids = set()

                for bin_row in bin_data:
                    recipe_id = bin_row.recipeID
                    recipe_material_map[recipe_id] = []
                    recipe = next((r for r in recipes if r.RecipeID == recipe_id), None)
                    if not recipe:
                        continue
                    rec_dict = model_to_dict(recipe)
                    bin_dict = model_to_dict(bin_row)

                    fields_bins = [f'bin{i}' for i in range(1, 17)]
                    fields_man = [f'man{i}' for i in range(1, 21)]
                    fields_oil = ['oil1', 'oil2']
                    fields_prem_meds = ['medicine', 'premix1', 'premix2']
                    for i, field in enumerate(fields_bins, 1):
                        mat_id = bin_dict.get(field)
                        if mat_id is not None:
                            setwt = rec_dict.get(f'Bin{i}SetWt')
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                    for i, field in enumerate(fields_man, 1):
                        mat_id = bin_dict.get(field)
                        if mat_id:
                            setwt = rec_dict.get(f'Man{i}SetWt', 0)
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                    for oil in fields_oil:
                        mat_id = bin_dict.get(oil)
                        if mat_id:
                            setwt = rec_dict.get(f'{oil.capitalize()}SetWt', 0)
                            if setwt:
                                recipe_material_map[recipe_id].append((oil, mat_id))
                                all_mat_ids.add(mat_id)

                    for field in fields_prem_meds:
                        mat_id = bin_dict.get(field)
                        if mat_id :
                            if field == 'medicine':
                                setwt = rec_dict.get('MedSetWt', 0)
                            else:
                                setwt = rec_dict.get(f'{field.capitalize()}Set', 0)
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                materials = MaterialName.objects.filter(MatID__in=all_mat_ids)

                for recipe_id in recipe_ids:
                    recipe = next((r for r in recipes if r.RecipeID == recipe_id), None)
                    bin_row = next((b for b in bin_data if b.recipeID == recipe_id), None)
                    if not recipe or not bin_row:
                        continue
                    rec_dict = model_to_dict(recipe)
                    bin_dict = model_to_dict(bin_row)
                    recipe_batches = batch_data.filter(RecipeID=recipe_id)
                    set_total = 0
                    actual_total = 0
                    material_rows = []

                    batch_count = batch_count_dict.get(recipe_id, 0)

                    for bin_name, mat_id in recipe_material_map[recipe_id]:
                        if 'bin' in bin_name:
                            index = bin_name.replace('bin', '')
                            set_key = f'Bin{index}SetWt'
                            act_key = f'Bin{index}Act'
                        elif 'man' in bin_name:
                            index = bin_name.replace('man', '')
                            set_key = f'Man{index}SetWt'
                            act_key = f'ManWt{index}'
                        elif bin_name in ['oil1', 'oil2']:
                            set_key = f'{bin_name.capitalize()}SetWt'
                            act_key = f'{bin_name.capitalize()}Act'
                        elif bin_name == 'medicine':
                            set_key = 'MedSetWt'
                            act_key = 'MedicineWt'
                        elif bin_name == 'molasses':
                            set_key = 'MolassesSet'
                            act_key = 'MolassesWt'
                        elif bin_name == 'premix1':
                            set_key = 'Premix1Set'
                            act_key = 'PremixWt1'
                        elif bin_name == 'premix2':
                            set_key = 'Premix2Set'
                            act_key = 'PremixWt2'

                        original_set_wt = rec_dict.get(set_key, 0) or 0
                        set_wt = original_set_wt * batch_count

                        act_sum = 0
                        for b in recipe_batches:
                            b_dict = model_to_dict(b)
                            act_sum += b_dict.get(act_key, 0) or 0

                        mat_name = next((m.MatName for m in materials if m.MatID == mat_id), f"MatID {mat_id}")
                        error = act_sum - set_wt
                        error_pct = (error / set_wt * 100) if set_wt else 0

                        material_rows.append({
                            'bin': bin_name,
                            'material': mat_name,
                            'set_wt': set_wt,
                            'actual_wt': act_sum,
                            'error': error,
                            'error_pct': error_pct
                        })

                        set_total += set_wt
                        actual_total += act_sum
                    error_total = set_total - actual_total
                    error_total_pct = (error_total / set_total * 100) if set_total else 0

                    batch_actual.append({
                        'RecipeID': recipe_id,
                        'RecipeName': recipe.recipename,
                        'materials': material_rows,
                        'set_total_all': set_total,
                        'BatchCount': batch_count,
                        'total_all': actual_total,
                        'error_total': error_total,
                        'error_total_pct': error_total_pct
                    })

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
    plants = []
    plant_name = None
    start_date = date.today().isoformat()
    total_material_data = {}    
    
    if request.user.is_superuser:
        plants = Plant.objects.all()
    elif request.user.designation == 'manufacture':
        child_ids = request.session.get('child_ids', [])
        plants = Plant.objects.filter(plant_owner_id__in=child_ids)
    elif request.user.designation == 'plant_owner':
        plant = Plant.objects.filter(plant_owner_id=request.user.id).first()
        if plant:
            plants = [plant]

    # If form submitted
    if request.method == "POST":
        start_date = request.POST.get('start_date')
        plant_id = request.POST.get('plant_id')

        try:
            if plant_id and start_date:
                plant_name = Plant.objects.filter(plant_id=plant_id).first()
                batch_data = BatchData.objects.filter(plant_id=plant_id, stdate=start_date)

                recipe_ids = batch_data.values_list('RecipeID', flat=True).distinct()
                recipes = Recipemain.objects.filter(RecipeID__in=recipe_ids)
                bin_data = BinName.objects.filter(recipeID__in=recipe_ids)

                recipe_material_map = {}
                all_mat_ids = set()

                for bin_row in bin_data:
                    recipe_id = bin_row.recipeID
                    recipe_material_map.setdefault(recipe_id, [])
                    recipe = next((r for r in recipes if r.RecipeID == recipe_id), None)
                    if not recipe:
                        continue

                    rec_dict = model_to_dict(recipe)
                    bin_dict = model_to_dict(bin_row)

                    fields_bins = [f'bin{i}' for i in range(1, 17)]
                    fields_man = [f'man{i}' for i in range(1, 21)]
                    fields_oil = ['oil1', 'oil2']
                    fields_prem_meds = ['medicine', 'premix1', 'premix2']

                    # Collect materials from bins
                    for i, field in enumerate(fields_bins, 1):
                        mat_id = bin_dict.get(field)
                        if mat_id is not None:
                            setwt = rec_dict.get(f'Bin{i}SetWt')
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                    # Collect materials from manual bins
                    for i, field in enumerate(fields_man, 1):
                        mat_id = bin_dict.get(field)
                        if mat_id:
                            setwt = rec_dict.get(f'Man{i}SetWt')
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                    # Collect materials from oils
                    for field in fields_oil:
                        mat_id = bin_dict.get(field)
                        if mat_id:
                            setwt = rec_dict.get(f'{field.capitalize()}SetWt')
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                    # Collect materials from premix and medicine
                    for field in fields_prem_meds:
                        mat_id = bin_dict.get(field)
                        if mat_id:
                            if field == 'medicine':
                                setwt = rec_dict.get('MedSetWt')
                            else:
                                setwt = rec_dict.get(f'{field.capitalize()}Set')
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                materials = MaterialName.objects.filter(MatID__in=all_mat_ids)
                material_map = {m.MatID: m.MatName for m in materials}

                for recipe_id in recipe_ids:
                    recipe = next((r for r in recipes if r.RecipeID == recipe_id), None)
                    bin_row = next((b for b in bin_data if b.recipeID == recipe_id), None)
                    if not recipe or not bin_row:
                        continue

                    rec_dict = model_to_dict(recipe)
                    recipe_batches = batch_data.filter(RecipeID=recipe_id)

                    for bin_name, mat_id in recipe_material_map.get(recipe_id, []): 
                        if 'bin' in bin_name:
                            index = bin_name.replace('bin', '')
                            set_key = f'Bin{index}SetWt'
                            act_key = f'Bin{index}Act'
                        elif 'man' in bin_name:
                            index = bin_name.replace('man', '')
                            set_key = f'Man{index}SetWt'
                            act_key = f'ManWt{index}'
                        elif bin_name in ['oil1', 'oil2']:
                            set_key = f'{bin_name.capitalize()}SetWt'
                            act_key = f'{bin_name.capitalize()}Act'
                        elif bin_name == 'medicine':
                            set_key = 'MedSetWt'
                            act_key = 'MedicineWt'
                        elif bin_name == 'premix1':
                            set_key = 'Premix1Set'
                            act_key = 'PremixWt1'
                        elif bin_name == 'premix2':
                            set_key = 'Premix2Set'
                            act_key = 'PremixWt2'
                        else:
                            continue

                        # Get set weight per batch
                        set_wt_single = rec_dict.get(set_key) or 0
                        batch_count = recipe_batches.count()
                        set_wt = set_wt_single * batch_count

                        # Sum actual weights from all batches
                        act_sum = sum(model_to_dict(b).get(act_key) or 0 for b in recipe_batches)

                        if mat_id not in total_material_data:
                            total_material_data[mat_id] = {
                                'material': material_map.get(mat_id, f'MatID {mat_id}'),
                                'set_total': 0,
                                'actual_total': 0,
                                'error_total': 0,
                                'error_pct': 0,
                            }

                        total_material_data[mat_id]['set_total'] += set_wt
                        total_material_data[mat_id]['actual_total'] += act_sum
                        error = act_sum - set_wt
                        total_material_data[mat_id]['error_total'] += error

                # Calculate error % for each material
                for mat_id, data in total_material_data.items():
                    if data['set_total'] > 0:
                        data['error_pct'] = (data['error_total'] / data['set_total']) * 100
                    else:
                        data['error_pct'] = 0

        except Exception as e:
            print("Error in daily_consumption:", e) 
    total_set = sum(row['set_total'] for row in total_material_data.values())
    total_actual = sum(row['actual_total'] for row in total_material_data.values())
    total_error = total_actual - total_set
    total_error_pct = (total_error / total_set * 100) if total_set else 0

    return render(request, 'daily-consumption-report.html', {
        'plants': plants,
        'plant_name': plant_name,
        'start_date': start_date,
        'is_plant_owner': request.user.designation == 'plant_owner',
        'total_material_data': total_material_data,
        'total_set': total_set,
        'total_actual': total_actual,
        'total_error': total_error,
        'total_error_pct': total_error_pct
    })
    
@login_required
def daily_motor(request):
    plants = []
    recipe_ids = []
    motor_data = []
    plant_id = None
    start_date = date.today().isoformat()
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
    start_date = date.today().isoformat()
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
    start_date = date.today().isoformat()
    plant_id = None
    shift = None
    plant_name = None
    batch_data = []   
    filtered_data = []
    material_name_list = []

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
        shift = request.POST.get('shift')

        try:
            if plant_id and start_date:
                plant_name = Plant.objects.filter(plant_id=plant_id).first()

                if shift:
                    filter_kwargs = {
                        'plant_id': plant_id,
                        f'{shift}__isnull': False,
                    }
                    shift_data_qs = Plant.objects.filter(**filter_kwargs)
                    if shift_data_qs.exists():
                        plant_shift = shift_data_qs.first()
                        shift_start_time = getattr(plant_shift, shift)

                        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                        shift_start_dt = datetime.combine(start_date_obj, shift_start_time)
                        shift_end_dt = shift_start_dt + timedelta(hours=8)  

                        # Get all batch data for the date and plant
                        raw_batch_data = BatchData.objects.filter(
                            plant_id=plant_id,
                            stdate=start_date
                        )

                        # Filter batch_data by shift time range
                        batch_data_list = []
                        for batch in raw_batch_data:
                            try:
                                full_datetime_str = f"{batch.stdate} {batch.stTime}"
                                batch_datetime = datetime.strptime(full_datetime_str, "%Y-%m-%d %H:%M:%S")
                                if shift_start_dt <= batch_datetime <= shift_end_dt:
                                    batch_data_list.append(batch.BatchID)
                            except Exception as e:
                                print(f"Skipping invalid datetime: {batch.stdate} {batch.stTime} | Error: {e}")

                        # Now fetch batch_data queryset filtered by these IDs
                        batch_data = BatchData.objects.filter(BatchID__in=batch_data_list)
                    else:
                        # No shift info, get all batch data for the date and plant
                        batch_data = BatchData.objects.filter(plant_id=plant_id, stdate=start_date)
                else:
                    # No shift filtering, get all batch data for the date and plant
                    batch_data = BatchData.objects.filter(plant_id=plant_id, stdate=start_date)

                # Count batches per RecipeID
                batch_counts = batch_data.values('RecipeID').annotate(count=Count('RecipeID'))
                batch_count_dict = {item['RecipeID']: item['count'] for item in batch_counts}
                recipe_ids = batch_data.values_list('RecipeID', flat=True).distinct()

                recipes = Recipemain.objects.filter(RecipeID__in=recipe_ids)
                bin_data = BinName.objects.filter(recipeID__in=recipe_ids)

                # Map RecipeID to materials with SetWt > 0
                recipe_material_map = {}
                all_mat_ids = set()

                for bin_row in bin_data:
                    recipe_id = bin_row.recipeID
                    recipe_material_map[recipe_id] = []

                    recipe = next((r for r in recipes if r.RecipeID == recipe_id), None)
                    if not recipe:
                        continue
                    rec_dict = model_to_dict(recipe)
                    bin_dict = model_to_dict(bin_row)

                    fields_bins = [f'bin{i}' for i in range(1, 17)]
                    fields_man = [f'man{i}' for i in range(1, 21)]
                    fields_oil = ['oil1', 'oil2']
                    fields_prem_meds = ['medicine', 'premix1', 'premix2']

                    for i, field in enumerate(fields_bins, 1):
                        mat_id = bin_dict.get(field)
                        if mat_id is not None:
                            setwt = rec_dict.get(f'Bin{i}SetWt')
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                    for i, field in enumerate(fields_man, 1):
                        mat_id = bin_dict.get(field)
                        if mat_id is not None:
                            setwt = rec_dict.get(f'Man{i}SetWt', 0)
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                    for oil in fields_oil:
                        mat_id = bin_dict.get(oil)
                        if mat_id is not None:
                            setwt = rec_dict.get(f'{oil.capitalize()}SetWt', 0)
                            if setwt:
                                recipe_material_map[recipe_id].append((oil, mat_id))
                                all_mat_ids.add(mat_id)

                    for field in fields_prem_meds:
                        mat_id = bin_dict.get(field)
                        if mat_id is not None:
                            if field == 'medicine':
                                setwt = rec_dict.get('MedSetWt', 0)
                            else:
                                setwt = rec_dict.get(f'{field.capitalize()}Set', 0)
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                materials = MaterialName.objects.filter(MatID__in=all_mat_ids)
                material_dict = {m.MatID: m.MatName for m in materials}

                seen = set()
                material_name_list = []
                material_order = []
                for mats in recipe_material_map.values():
                    for _, mat_id in mats:
                        if mat_id not in seen:
                            seen.add(mat_id)
                            material_name_list.append(material_dict.get(mat_id, f"MatID {mat_id}"))
                            material_order.append(mat_id)

                bin_data_dict = {row.recipeID: model_to_dict(row) for row in bin_data}

                for recipe in recipes:
                    rec_dict = model_to_dict(recipe)
                    bin_row = bin_data_dict.get(recipe.RecipeID, {})
                    material_wt_map = {}

                    for i in range(1, 17):
                        mat_id = bin_row.get(f'bin{i}')
                        if mat_id is not None:
                            wt = rec_dict.get(f'Bin{i}SetWt', 0)
                            if wt > 0:
                                material_wt_map[mat_id] = wt

                    for i in range(1, 21):
                        mat_id = bin_row.get(f'man{i}')
                        if mat_id and mat_id != 0:
                            wt = rec_dict.get(f'Man{i}SetWt', 0)
                            if wt > 0:
                                material_wt_map[mat_id] = wt

                    for oil in ['oil1', 'oil2']:
                        mat_id = bin_row.get(oil)
                        if mat_id and mat_id != 0:
                            wt = rec_dict.get(f'{oil.capitalize()}SetWt', 0)
                            if wt > 0:
                                material_wt_map[mat_id] = wt

                    for prem in ['premix1', 'premix2']:
                        mat_id = bin_row.get(prem)
                        if mat_id and mat_id != 0:
                            wt = rec_dict.get(f'{prem.capitalize()}Set', 0)
                            if wt > 0:
                                material_wt_map[mat_id] = wt

                    med = bin_row.get('medicine')
                    if med and med != 0:
                        wt = rec_dict.get('MedSetWt', 0)
                        if wt > 0:
                            material_wt_map[med] = wt

                    row_data = [material_wt_map.get(mat_id, 0.0) for mat_id in material_order]

                    # Actual batches for this recipe
                    recipe_batches = batch_data.filter(RecipeID=recipe.RecipeID)

                    actual_batches = []

                    for batch in recipe_batches:
                        batch_dict = model_to_dict(batch)
                        bin_row = bin_data_dict.get(batch.RecipeID, {})
                        actual_map = {}

                        for i in range(1, 17):
                            mat_id = bin_row.get(f'bin{i}')
                            if mat_id is not None:
                                val = batch_dict.get(f'Bin{i}Act')
                                if val is not None and val != 0:
                                    actual_map[mat_id] = val

                        for i in range(1, 21):
                            mat_id = bin_row.get(f'man{i}')
                            if mat_id:
                                val = batch_dict.get(f'ManWt{i}')
                                if val is not None and val != 0:
                                    actual_map[mat_id] = val

                        for oil in ['oil1', 'oil2']:
                            mat_id = bin_row.get(oil)
                            if mat_id:
                                val = batch_dict.get(f'{oil.capitalize()}Act', 0)
                                actual_map[mat_id] = val

                        premix1_id = bin_row.get('premix1')
                        if premix1_id:
                            val = getattr(batch, 'PremixWt1', 0)
                            actual_map[premix1_id] = val

                        premix2_id = bin_row.get('premix2')
                        if premix2_id:
                            val = getattr(batch, 'PremixWt2', 0)
                            actual_map[premix2_id] = val

                        medicine_id = bin_row.get('medicine')
                        if medicine_id:
                            val = getattr(batch, 'MedicineWt', 0)
                            actual_map[medicine_id] = val

                        row_actual = [actual_map.get(mat_id, 0.0) for mat_id in material_order]
                        actual_batches.append({
                            'batch_no': batch.BatchNum,
                            'start_time': batch.stTime,
                            'values': row_actual,
                        })

                    filtered_data.append({
                        "RecipeID": recipe.RecipeID,
                        "RecipeName": recipe.recipename,
                        "SetWt": rec_dict.get('SetWt'),
                        "ActWt": rec_dict.get('ActWt'),
                        "BatchCount": batch_count_dict.get(recipe.RecipeID, 0),
                        "Materials": row_data,
                        "ActualBatches": actual_batches,
                    })

        except Exception as e:
            print(f"Error in batch_shift: {e}")

    return render(request, 'batch-shift-report.html', {
        'plants': plants,
        'start_date': start_date,
        'plant_id': plant_id,
        'shift': shift,
        'plant_name': plant_name,
        'batch_data': batch_data,
        'filtered_data': filtered_data,
        'material_name_list': material_name_list,
    })

     
@login_required
def recipe_shift(request):
    plants = []
    recipe_ids = []
    batch_data = []
    batch_actual = []
    plant_id = None
    start_date = date.today().isoformat()
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
        plant_id = request.POST.get('plant_id')
        shift = request.POST.get('shift')

        try:
            if plant_id and start_date:
                plant_name = Plant.objects.filter(plant_id=plant_id).first()

                if shift:
                    filter_kwargs = {
                        'plant_id': plant_id,
                        f'{shift}__isnull': False,
                    }
                    shift_data_qs = Plant.objects.filter(**filter_kwargs)
                    if shift_data_qs.exists():
                        plant_shift = shift_data_qs.first()
                        shift_start_time = getattr(plant_shift, shift)

                        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                        shift_start_dt = datetime.combine(start_date_obj, shift_start_time)
                        shift_end_dt = shift_start_dt + timedelta(hours=8)  

                        # Get all batch data for the date and plant
                        raw_batch_data = BatchData.objects.filter(
                            plant_id=plant_id,
                            stdate=start_date
                        )

                        # Filter batch_data by shift time range
                        batch_data_list = []
                        for batch in raw_batch_data:
                            try:
                                full_datetime_str = f"{batch.stdate} {batch.stTime}"
                                batch_datetime = datetime.strptime(full_datetime_str, "%Y-%m-%d %H:%M:%S")
                                if shift_start_dt <= batch_datetime <= shift_end_dt:
                                    batch_data_list.append(batch.BatchID)
                            except Exception as e:
                                print(f"Skipping invalid datetime: {batch.stdate} {batch.stTime} | Error: {e}")

                        # Now fetch batch_data queryset filtered by these IDs
                        batch_data = BatchData.objects.filter(BatchID__in=batch_data_list)
                    else:
                        # No shift info, get all batch data for the date and plant
                        batch_data = BatchData.objects.filter(plant_id=plant_id, stdate=start_date)
                else:
                    # No shift filtering, get all batch data for the date and plant
                    batch_data = BatchData.objects.filter(plant_id=plant_id, stdate=start_date)

                batch_counts = batch_data.values('RecipeID').annotate(count=Count('RecipeID'))
                batch_count_dict = {item['RecipeID']: item['count'] for item in batch_counts}
                recipe_ids = batch_data.values_list('RecipeID', flat=True).distinct()
                recipes = Recipemain.objects.filter(RecipeID__in=recipe_ids)
                bin_data = BinName.objects.filter(recipeID__in=recipe_ids)

                recipe_material_map = {}
                all_mat_ids = set()

                for bin_row in bin_data:
                    recipe_id = bin_row.recipeID
                    recipe_material_map[recipe_id] = []
                    recipe = next((r for r in recipes if r.RecipeID == recipe_id), None)
                    if not recipe:
                        continue
                    rec_dict = model_to_dict(recipe)
                    bin_dict = model_to_dict(bin_row)

                    fields_bins = [f'bin{i}' for i in range(1, 17)]
                    fields_man = [f'man{i}' for i in range(1, 21)]
                    fields_oil = ['oil1', 'oil2']
                    fields_prem_meds = ['medicine', 'premix1', 'premix2']
                    for i, field in enumerate(fields_bins, 1):
                        mat_id = bin_dict.get(field)
                        if mat_id is not None:
                            setwt = rec_dict.get(f'Bin{i}SetWt')
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                    for i, field in enumerate(fields_man, 1):
                        mat_id = bin_dict.get(field)
                        if mat_id:
                            setwt = rec_dict.get(f'Man{i}SetWt', 0)
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                    for oil in fields_oil:
                        mat_id = bin_dict.get(oil)
                        if mat_id:
                            setwt = rec_dict.get(f'{oil.capitalize()}SetWt', 0)
                            if setwt:
                                recipe_material_map[recipe_id].append((oil, mat_id))
                                all_mat_ids.add(mat_id)

                    for field in fields_prem_meds:
                        mat_id = bin_dict.get(field)
                        if mat_id :
                            if field == 'medicine':
                                setwt = rec_dict.get('MedSetWt', 0)
                            else:
                                setwt = rec_dict.get(f'{field.capitalize()}Set', 0)
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                materials = MaterialName.objects.filter(MatID__in=all_mat_ids)

                for recipe_id in recipe_ids:
                    recipe = next((r for r in recipes if r.RecipeID == recipe_id), None)
                    bin_row = next((b for b in bin_data if b.recipeID == recipe_id), None)
                    if not recipe or not bin_row:
                        continue
                    rec_dict = model_to_dict(recipe)
                    bin_dict = model_to_dict(bin_row)
                    recipe_batches = batch_data.filter(RecipeID=recipe_id)
                    set_total = 0
                    actual_total = 0
                    material_rows = []

                    batch_count = batch_count_dict.get(recipe_id, 0)

                    for bin_name, mat_id in recipe_material_map[recipe_id]:
                        if 'bin' in bin_name:
                            index = bin_name.replace('bin', '')
                            set_key = f'Bin{index}SetWt'
                            act_key = f'Bin{index}Act'
                        elif 'man' in bin_name:
                            index = bin_name.replace('man', '')
                            set_key = f'Man{index}SetWt'
                            act_key = f'ManWt{index}'
                        elif bin_name in ['oil1', 'oil2']:
                            set_key = f'{bin_name.capitalize()}SetWt'
                            act_key = f'{bin_name.capitalize()}Act'
                        elif bin_name == 'medicine':
                            set_key = 'MedSetWt'
                            act_key = 'MedicineWt'
                        elif bin_name == 'molasses':
                            set_key = 'MolassesSet'
                            act_key = 'MolassesWt'
                        elif bin_name == 'premix1':
                            set_key = 'Premix1Set'
                            act_key = 'PremixWt1'
                        elif bin_name == 'premix2':
                            set_key = 'Premix2Set'
                            act_key = 'PremixWt2'

                        original_set_wt = rec_dict.get(set_key, 0) or 0
                        set_wt = original_set_wt * batch_count

                        act_sum = 0
                        for b in recipe_batches:
                            b_dict = model_to_dict(b)
                            act_sum += b_dict.get(act_key, 0) or 0

                        mat_name = next((m.MatName for m in materials if m.MatID == mat_id), f"MatID {mat_id}")
                        error = act_sum - set_wt
                        error_pct = (error / set_wt * 100) if set_wt else 0

                        material_rows.append({
                            'bin': bin_name,
                            'material': mat_name,
                            'set_wt': set_wt,
                            'actual_wt': act_sum,
                            'error': error,
                            'error_pct': error_pct
                        })

                        set_total += set_wt
                        actual_total += act_sum
                    error_total = set_total - actual_total
                    error_total_pct = (error_total / set_total * 100) if set_total else 0

                    batch_actual.append({
                        'RecipeID': recipe_id,
                        'RecipeName': recipe.recipename,
                        'materials': material_rows,
                        'set_total_all': set_total,
                        'BatchCount': batch_count,
                        'total_all': actual_total,
                        'error_total': error_total,
                        'error_total_pct': error_total_pct
                    })

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
    total_material_data={}
    # Form values
    start_date = date.today().isoformat()
    shift = None

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
        shift = request.POST.get('shift')

        try:
            if plant_id and start_date:
                plant_name = Plant.objects.filter(plant_id=plant_id).first()

                if shift:
                    filter_kwargs = {
                        'plant_id': plant_id,
                        f'{shift}__isnull': False,
                    }
                    shift_data_qs = Plant.objects.filter(**filter_kwargs)
                    if shift_data_qs.exists():
                        plant_shift = shift_data_qs.first()
                        shift_start_time = getattr(plant_shift, shift)

                        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                        shift_start_dt = datetime.combine(start_date_obj, shift_start_time)
                        shift_end_dt = shift_start_dt + timedelta(hours=8)  

                        # Get all batch data for the date and plant
                        raw_batch_data = BatchData.objects.filter(
                            plant_id=plant_id,
                            stdate=start_date
                        )

                        # Filter batch_data by shift time range
                        batch_data_list = []
                        for batch in raw_batch_data:
                            try:
                                full_datetime_str = f"{batch.stdate} {batch.stTime}"
                                batch_datetime = datetime.strptime(full_datetime_str, "%Y-%m-%d %H:%M:%S")
                                if shift_start_dt <= batch_datetime <= shift_end_dt:
                                    batch_data_list.append(batch.BatchID)
                            except Exception as e:
                                print(f"Skipping invalid datetime: {batch.stdate} {batch.stTime} | Error: {e}")

                        # Now fetch batch_data queryset filtered by these IDs
                        batch_data = BatchData.objects.filter(BatchID__in=batch_data_list)
                    else:
                        # No shift info, get all batch data for the date and plant
                        batch_data = BatchData.objects.filter(plant_id=plant_id, stdate=start_date)
                else:
                    # No shift filtering, get all batch data for the date and plant
                    batch_data = BatchData.objects.filter(plant_id=plant_id, stdate=start_date)
                recipe_ids = batch_data.values_list('RecipeID', flat=True).distinct()
                recipes = Recipemain.objects.filter(RecipeID__in=recipe_ids)
                bin_data = BinName.objects.filter(recipeID__in=recipe_ids)

                recipe_material_map = {}
                all_mat_ids = set()

                for bin_row in bin_data:
                    recipe_id = bin_row.recipeID
                    recipe_material_map.setdefault(recipe_id, [])
                    recipe = next((r for r in recipes if r.RecipeID == recipe_id), None)
                    if not recipe:
                        continue

                    rec_dict = model_to_dict(recipe)
                    bin_dict = model_to_dict(bin_row)

                    fields_bins = [f'bin{i}' for i in range(1, 17)]
                    fields_man = [f'man{i}' for i in range(1, 21)]
                    fields_oil = ['oil1', 'oil2']
                    fields_prem_meds = ['medicine', 'premix1', 'premix2']

                    # Collect materials from bins
                    for i, field in enumerate(fields_bins, 1):
                        mat_id = bin_dict.get(field)
                        if mat_id is not None:
                            setwt = rec_dict.get(f'Bin{i}SetWt')
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                    # Collect materials from manual bins
                    for i, field in enumerate(fields_man, 1):
                        mat_id = bin_dict.get(field)
                        if mat_id:
                            setwt = rec_dict.get(f'Man{i}SetWt')
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                    # Collect materials from oils
                    for field in fields_oil:
                        mat_id = bin_dict.get(field)
                        if mat_id:
                            setwt = rec_dict.get(f'{field.capitalize()}SetWt')
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                    # Collect materials from premix and medicine
                    for field in fields_prem_meds:
                        mat_id = bin_dict.get(field)
                        if mat_id:
                            if field == 'medicine':
                                setwt = rec_dict.get('MedSetWt')
                            else:
                                setwt = rec_dict.get(f'{field.capitalize()}Set')
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                materials = MaterialName.objects.filter(MatID__in=all_mat_ids)
                material_map = {m.MatID: m.MatName for m in materials}

                for recipe_id in recipe_ids:
                    recipe = next((r for r in recipes if r.RecipeID == recipe_id), None)
                    bin_row = next((b for b in bin_data if b.recipeID == recipe_id), None)
                    if not recipe or not bin_row:
                        continue

                    rec_dict = model_to_dict(recipe)
                    recipe_batches = batch_data.filter(RecipeID=recipe_id)

                    for bin_name, mat_id in recipe_material_map.get(recipe_id, []): 
                        if 'bin' in bin_name:
                            index = bin_name.replace('bin', '')
                            set_key = f'Bin{index}SetWt'
                            act_key = f'Bin{index}Act'
                        elif 'man' in bin_name:
                            index = bin_name.replace('man', '')
                            set_key = f'Man{index}SetWt'
                            act_key = f'ManWt{index}'
                        elif bin_name in ['oil1', 'oil2']:
                            set_key = f'{bin_name.capitalize()}SetWt'
                            act_key = f'{bin_name.capitalize()}Act'
                        elif bin_name == 'medicine':
                            set_key = 'MedSetWt'
                            act_key = 'MedicineWt'
                        elif bin_name == 'premix1':
                            set_key = 'Premix1Set'
                            act_key = 'PremixWt1'
                        elif bin_name == 'premix2':
                            set_key = 'Premix2Set'
                            act_key = 'PremixWt2'
                        else:
                            continue

                        # Get set weight per batch
                        set_wt_single = rec_dict.get(set_key) or 0
                        batch_count = recipe_batches.count()
                        set_wt = set_wt_single * batch_count

                        # Sum actual weights from all batches
                        act_sum = sum(model_to_dict(b).get(act_key) or 0 for b in recipe_batches)

                        if mat_id not in total_material_data:
                            total_material_data[mat_id] = {
                                'material': material_map.get(mat_id, f'MatID {mat_id}'),
                                'set_total': 0,
                                'actual_total': 0,
                                'error_total': 0,
                                'error_pct': 0,
                            }

                        total_material_data[mat_id]['set_total'] += set_wt
                        total_material_data[mat_id]['actual_total'] += act_sum
                        error = act_sum - set_wt
                        total_material_data[mat_id]['error_total'] += error

                # Calculate error % for each material
                for mat_id, data in total_material_data.items():
                    if data['set_total'] > 0:
                        data['error_pct'] = (data['error_total'] / data['set_total']) * 100
                    else:
                        data['error_pct'] = 0

        except Exception as e:
            print("Error in daily_consumption:", e) 
    total_set = sum(row['set_total'] for row in total_material_data.values())
    total_actual = sum(row['actual_total'] for row in total_material_data.values())
    total_error = total_actual - total_set
    total_error_pct = (total_error / total_set * 100) if total_set else 0    

    return render(request, 'consumption-shift-report.html', {
        'plants': plants,
        'plant_name':plant_name,
        'batch_data': batch_data,
        'start_date': start_date,
        'shift': shift,
        'total_material_data': total_material_data,
        'total_set': total_set,
        'total_actual': total_actual,
        'total_error': total_error,
        'total_error_pct': total_error_pct,
        'is_plant_owner': request.user.designation == 'plant_owner',
    })

@login_required
def shift_motor(request):
    plants = []
    recipe_ids = []
    motor_data = []
    plant_id = None
    start_date = date.today().isoformat()
    plant_name = None
    shift = None

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
                    raw_batch_data = MotorData.objects.filter(
                        plant_id=plant_id,
                        sdate=start_date  # varchar match
                    )
                    plant_name = Plant.objects.filter(plant_id=request.POST.get('plant_id')).first()
                    # Fetch batch data
                    motor_data = []
                    for batch in raw_batch_data:
                        try:
                            full_datetime_str = f"{batch.sdate} {batch.sTime}"
                            batch_datetime = datetime.strptime(full_datetime_str, "%Y-%m-%d %H:%M:%S")

                            if shift_start_dt <= batch_datetime <= shift_end_dt:
                                motor_data.append(batch)
                        except Exception as e:
                            print(f"Skipping invalid datetime: {batch.sdate} {batch.sTime} | Error: {e}")        
        
        except Exception as e:
            print("Error:", e)

    return render(request, 'shift-motor-report.html', {
        'plant_name': plant_name,
        'plants': plants,
        'recipe_ids': recipe_ids,
        'motor_data': motor_data,
        'start_date': start_date,
        'is_plant_owner': request.user.designation == 'plant_owner',
    }) 

@login_required
def shift_bagging(request):
    plants = []
    recipe_ids = []
    bagging_data = []
    plant_id = None
    start_date = date.today().isoformat()
    plant_name = None
    shift = None

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
                    raw_batch_data = BagData.objects.filter(
                        plant_id=plant_id,
                        sdate=start_date  # varchar match
                    )
                    plant_name = Plant.objects.filter(plant_id=request.POST.get('plant_id')).first()
                    # Fetch batch data
                    bagging_data = []
                    for batch in raw_batch_data:
                        try:
                            full_datetime_str = f"{batch.sdate} {batch.sTime}"
                            batch_datetime = datetime.strptime(full_datetime_str, "%Y-%m-%d %H:%M:%S")

                            if shift_start_dt <= batch_datetime <= shift_end_dt:
                                bagging_data.append(batch)
                        except Exception as e:
                            print(f"Skipping invalid datetime: {batch.sdate} {batch.sTime} | Error: {e}")         
        except Exception as e:
            print("Error:", e)

    return render(request, 'shift-bagging-report.html', {
        'plant_name': plant_name,
        'plants': plants,
        'recipe_ids': recipe_ids,
        'bagging_data': bagging_data,
        'start_date': start_date,
        'is_plant_owner': request.user.designation == 'plant_owner',
    })

@login_required
def custom_batch(request):
    plants = []
    start_date= date.today().isoformat()
    end_date= date.today().isoformat()
    batch_data = []
    recipe_ids = []
    filtered_data = []
    material_name_list=[]
    plant_name=[]
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
                plant_name = Plant.objects.filter(plant_id=plant_id).first()
                batch_data = BatchData.objects.filter(
                    plant_id=plant_id,
                    stdate__range=(start_date, end_date)
                )

                 # Count batches per RecipeID
                batch_counts = batch_data.values('RecipeID').annotate(count=Count('RecipeID'))
                batch_count_dict = {item['RecipeID']: item['count'] for item in batch_counts}
                recipe_ids = batch_data.values_list('RecipeID', flat=True).distinct()

                recipes = Recipemain.objects.filter(RecipeID__in=recipe_ids)
                bin_data = BinName.objects.filter(recipeID__in=recipe_ids)

                # Map RecipeID to materials with SetWt > 0
                recipe_material_map = {}
                all_mat_ids = set()

                for bin_row in bin_data:
                    recipe_id = bin_row.recipeID
                    recipe_material_map[recipe_id] = []

                    recipe = next((r for r in recipes if r.RecipeID == recipe_id), None)
                    if not recipe:
                        continue
                    rec_dict = model_to_dict(recipe)
                    bin_dict = model_to_dict(bin_row)

                    fields_bins = [f'bin{i}' for i in range(1, 17)]
                    fields_man = [f'man{i}' for i in range(1, 21)]
                    fields_oil = ['oil1', 'oil2']
                    fields_prem_meds = ['medicine', 'premix1', 'premix2']

                    # Process bins
                    for i, field in enumerate(fields_bins, 1):
                        mat_id = bin_dict.get(field)
                        if mat_id is not None:
                            setwt = rec_dict.get(f'Bin{i}SetWt')
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)
                    # Process man
                    for i, field in enumerate(fields_man, 1):
                        mat_id = bin_dict.get(field)
                        if mat_id is not None:
                            setwt = rec_dict.get(f'Man{i}SetWt', 0)
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                    # Process oils
                    for oil in fields_oil:
                        mat_id = bin_dict.get(oil)
                        if mat_id is not None:
                            setwt = rec_dict.get(f'{oil.capitalize()}SetWt', 0)
                            if setwt:
                                recipe_material_map[recipe_id].append((oil, mat_id))
                                all_mat_ids.add(mat_id)

                    # Process premixes and medicine
                    for field in fields_prem_meds:
                        mat_id = bin_dict.get(field)
                        if mat_id is not None:
                            if field == 'medicine':
                                setwt = rec_dict.get('MedSetWt', 0)
                            else:
                                setwt = rec_dict.get(f'{field.capitalize()}Set', 0)
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                materials = MaterialName.objects.filter(MatID__in=all_mat_ids)
                material_dict = {m.MatID: m.MatName for m in materials}

                # Order materials without duplicates (by first appearance in any recipe)
                seen = set()
                material_name_list = []
                material_order = []
                for mats in recipe_material_map.values():
                    for _, mat_id in mats:
                        if mat_id not in seen:
                            seen.add(mat_id)
                            material_name_list.append(material_dict.get(mat_id, f"MatID {mat_id}"))
                            material_order.append(mat_id)

                bin_data_dict = {row.recipeID: model_to_dict(row) for row in bin_data}
                for recipe in recipes:
                    rec_dict = model_to_dict(recipe)
                    bin_row = bin_data_dict.get(recipe.RecipeID, {})
                    material_wt_map = {}

                    for i in range(1, 17):
                        mat_id = bin_row.get(f'bin{i}')
                        if mat_id is not None:
                            wt = rec_dict.get(f'Bin{i}SetWt', 0)
                            if wt > 0:
                                material_wt_map[mat_id] = wt
                    for i in range(1, 21):
                        mat_id = bin_row.get(f'man{i}')
                        if mat_id and mat_id != 0:
                            wt = rec_dict.get(f'Man{i}SetWt', 0)
                            if wt > 0:
                                material_wt_map[mat_id] = wt

                    for oil in ['oil1', 'oil2']:
                        mat_id = bin_row.get(oil)
                        if mat_id and mat_id != 0:
                            wt = rec_dict.get(f'{oil.capitalize()}SetWt', 0)
                            if wt > 0:
                                material_wt_map[mat_id] = wt

                    for prem in ['premix1', 'premix2']:
                        mat_id = bin_row.get(prem)
                        if mat_id and mat_id != 0:
                            wt = rec_dict.get(f'{prem.capitalize()}Set', 0)
                            if wt > 0:
                                material_wt_map[mat_id] = wt

                    med = bin_row.get('medicine')
                    if med and med != 0:
                        wt = rec_dict.get('MedSetWt', 0)
                        if wt > 0:
                            material_wt_map[med] = wt

                    row_data = [material_wt_map.get(mat_id, 0.0) for mat_id in material_order]

                    # Actual batches for this recipe
                    recipe_batches = batch_data.filter(RecipeID=recipe.RecipeID)

                    actual_batches = []

                    for batch in recipe_batches:
                        batch_dict = model_to_dict(batch)
                        bin_row = bin_data_dict.get(batch.RecipeID, {})
                        actual_map = {}

                        for i in range(1, 17):
                            mat_id = bin_row.get(f'bin{i}')
                            if mat_id is not None:
                                val = batch_dict.get(f'Bin{i}Act')
                                if val is not None and not (val == 0):
                                    actual_map[mat_id] = val

                        for i in range(1, 21):
                            mat_id = bin_row.get(f'man{i}')
                            if mat_id :
                                val = batch_dict.get(f'ManWt{i}', 0)
                                actual_map[mat_id] = val

                        for oil in ['oil1', 'oil2']:
                            mat_id = bin_row.get(oil)
                            if mat_id :
                                val = batch_dict.get(f'{oil.capitalize()}Act', 0)
                                actual_map[mat_id] = val

                        premix1_id = bin_row.get('premix1')
                        if premix1_id :
                            val = getattr(batch, 'PremixWt1', 0)
                            actual_map[premix1_id] = val

                        premix2_id = bin_row.get('premix2')
                        if premix2_id :
                            val = getattr(batch, 'PremixWt2', 0)
                            actual_map[premix2_id] = val

                        medicine_id = bin_row.get('medicine')
                        if medicine_id :
                            val = getattr(batch, 'MedicineWt', 0)
                            actual_map[medicine_id] = val

                        row_actual = [actual_map.get(mat_id, 0.0) for mat_id in material_order]
                        actual_batches.append({
                            'batch_no': batch.BatchNum,
                            'start_time': batch.stTime,
                            'values': row_actual,
                        })
                    filtered_data.append({
                        "RecipeID": recipe.RecipeID,
                        "RecipeName": recipe.recipename,
                        "SetWt": rec_dict.get('SetWt'),
                        "ActWt": rec_dict.get('ActWt'),
                        "BatchCount": batch_count_dict.get(recipe.RecipeID, 0),
                        "Materials": row_data,
                        "ActualBatches": actual_batches,
                    })

        except Exception as e:
            print("Error:", e)

    return render(request, 'custom-batch-report.html', {
        'plants': plants,
        'recipe_ids': recipe_ids,
        'plant_name': plant_name,
        'batch_data': batch_data,
        'filtered_data': filtered_data,
        'material_name_list': material_name_list,
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
    start_date= date.today().isoformat()
    end_date= date.today().isoformat() 
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
                batch_counts = batch_data.values('RecipeID').annotate(count=Count('RecipeID'))
                batch_count_dict = {item['RecipeID']: item['count'] for item in batch_counts}
                recipe_ids = batch_data.values_list('RecipeID', flat=True).distinct()
                recipes = Recipemain.objects.filter(RecipeID__in=recipe_ids)
                bin_data = BinName.objects.filter(recipeID__in=recipe_ids)

                recipe_material_map = {}
                all_mat_ids = set()

                for bin_row in bin_data:
                    recipe_id = bin_row.recipeID
                    recipe_material_map[recipe_id] = []
                    recipe = next((r for r in recipes if r.RecipeID == recipe_id), None)
                    if not recipe:
                        continue
                    rec_dict = model_to_dict(recipe)
                    bin_dict = model_to_dict(bin_row)

                    fields_bins = [f'bin{i}' for i in range(1, 17)]
                    fields_man = [f'man{i}' for i in range(1, 21)]
                    fields_oil = ['oil1', 'oil2']
                    fields_prem_meds = ['medicine', 'premix1', 'premix2']
                    for i, field in enumerate(fields_bins, 1):
                        mat_id = bin_dict.get(field)
                        if mat_id is not None:
                            setwt = rec_dict.get(f'Bin{i}SetWt')
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                    for i, field in enumerate(fields_man, 1):
                        mat_id = bin_dict.get(field)
                        if mat_id:
                            setwt = rec_dict.get(f'Man{i}SetWt', 0)
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                    for oil in fields_oil:
                        mat_id = bin_dict.get(oil)
                        if mat_id:
                            setwt = rec_dict.get(f'{oil.capitalize()}SetWt', 0)
                            if setwt:
                                recipe_material_map[recipe_id].append((oil, mat_id))
                                all_mat_ids.add(mat_id)

                    for field in fields_prem_meds:
                        mat_id = bin_dict.get(field)
                        if mat_id :
                            if field == 'medicine':
                                setwt = rec_dict.get('MedSetWt', 0)
                            else:
                                setwt = rec_dict.get(f'{field.capitalize()}Set', 0)
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                materials = MaterialName.objects.filter(MatID__in=all_mat_ids)

                for recipe_id in recipe_ids:
                    recipe = next((r for r in recipes if r.RecipeID == recipe_id), None)
                    bin_row = next((b for b in bin_data if b.recipeID == recipe_id), None)
                    if not recipe or not bin_row:
                        continue
                    rec_dict = model_to_dict(recipe)
                    bin_dict = model_to_dict(bin_row)
                    recipe_batches = batch_data.filter(RecipeID=recipe_id)
                    set_total = 0
                    actual_total = 0
                    material_rows = []

                    batch_count = batch_count_dict.get(recipe_id, 0)

                    for bin_name, mat_id in recipe_material_map[recipe_id]:
                        if 'bin' in bin_name:
                            index = bin_name.replace('bin', '')
                            set_key = f'Bin{index}SetWt'
                            act_key = f'Bin{index}Act'
                        elif 'man' in bin_name:
                            index = bin_name.replace('man', '')
                            set_key = f'Man{index}SetWt'
                            act_key = f'ManWt{index}'
                        elif bin_name in ['oil1', 'oil2']:
                            set_key = f'{bin_name.capitalize()}SetWt'
                            act_key = f'{bin_name.capitalize()}Act'
                        elif bin_name == 'medicine':
                            set_key = 'MedSetWt'
                            act_key = 'MedicineWt'
                        elif bin_name == 'molasses':
                            set_key = 'MolassesSet'
                            act_key = 'MolassesWt'
                        elif bin_name == 'premix1':
                            set_key = 'Premix1Set'
                            act_key = 'PremixWt1'
                        elif bin_name == 'premix2':
                            set_key = 'Premix2Set'
                            act_key = 'PremixWt2'

                        original_set_wt = rec_dict.get(set_key, 0) or 0
                        set_wt = original_set_wt * batch_count

                        act_sum = 0
                        for b in recipe_batches:
                            b_dict = model_to_dict(b)
                            act_sum += b_dict.get(act_key, 0) or 0

                        mat_name = next((m.MatName for m in materials if m.MatID == mat_id), f"MatID {mat_id}")
                        error = act_sum - set_wt
                        error_pct = (error / set_wt * 100) if set_wt else 0

                        material_rows.append({
                            'bin': bin_name,
                            'material': mat_name,
                            'set_wt': set_wt,
                            'actual_wt': act_sum,
                            'error': error,
                            'error_pct': error_pct
                        })

                        set_total += set_wt
                        actual_total += act_sum
                    error_total = set_total - actual_total
                    error_total_pct = (error_total / set_total * 100) if set_total else 0

                    batch_actual.append({
                        'RecipeID': recipe_id,
                        'RecipeName': recipe.recipename,
                        'materials': material_rows,
                        'set_total_all': set_total,
                        'BatchCount': batch_count,
                        'total_all': actual_total,
                        'error_total': error_total,
                        'error_total_pct': error_total_pct
                    })

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
    plants = []
    total_material_data = {}
    plant_name = None
    start_date = date.today().isoformat()
    end_date = date.today().isoformat()

    # These variables must always be defined
    total_set = 0
    total_actual = 0
    total_error = 0
    total_error_pct = 0

    # Access permissions
    if request.user.is_superuser:
        plants = Plant.objects.all()
    elif request.user.designation == 'manufacture':
        child_ids = request.session.get('child_ids', [])
        plants = Plant.objects.filter(plant_owner_id__in=child_ids)
    elif request.user.designation == 'plant_owner':
        plant = Plant.objects.filter(plant_owner_id=request.user.id).first()
        if plant:
            plants = [plant]

    # On POST request
    if request.method == "POST":
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        plant_id = request.POST.get('plant_id')

        try:
            if plant_id and start_date and end_date:
                plant_name = Plant.objects.filter(plant_id=plant_id).first()
                batch_data = BatchData.objects.filter(
                    plant_id=plant_id,
                    stdate__range=(start_date, end_date)
                )
                recipe_ids = batch_data.values_list('RecipeID', flat=True).distinct()
                recipes = Recipemain.objects.filter(RecipeID__in=recipe_ids)
                bin_data = BinName.objects.filter(recipeID__in=recipe_ids)

                recipe_material_map = {}
                all_mat_ids = set()

                for bin_row in bin_data:
                    recipe_id = bin_row.recipeID
                    recipe_material_map.setdefault(recipe_id, [])
                    recipe = next((r for r in recipes if r.RecipeID == recipe_id), None)
                    if not recipe:
                        continue

                    rec_dict = model_to_dict(recipe)
                    bin_dict = model_to_dict(bin_row)

                    fields_bins = [f'bin{i}' for i in range(1, 17)]
                    fields_man = [f'man{i}' for i in range(1, 21)]
                    fields_oil = ['oil1', 'oil2']
                    fields_prem_meds = ['medicine', 'premix1', 'premix2']

                    # Bin materials
                    for i, field in enumerate(fields_bins, 1):
                        mat_id = bin_dict.get(field)
                        if mat_id is not None:
                            setwt = rec_dict.get(f'Bin{i}SetWt')
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                    # Manual bins
                    for i, field in enumerate(fields_man, 1):
                        mat_id = bin_dict.get(field)
                        if mat_id:
                            setwt = rec_dict.get(f'Man{i}SetWt')
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                    # Oils
                    for field in fields_oil:
                        mat_id = bin_dict.get(field)
                        if mat_id:
                            setwt = rec_dict.get(f'{field.capitalize()}SetWt')
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                    # Premix & medicine
                    for field in fields_prem_meds:
                        mat_id = bin_dict.get(field)
                        if mat_id:
                            setwt = (
                                rec_dict.get('MedSetWt') if field == 'medicine'
                                else rec_dict.get(f'{field.capitalize()}Set')
                            )
                            if setwt:
                                recipe_material_map[recipe_id].append((field, mat_id))
                                all_mat_ids.add(mat_id)

                materials = MaterialName.objects.filter(MatID__in=all_mat_ids)
                material_map = {m.MatID: m.MatName for m in materials}

                for recipe_id in recipe_ids:
                    recipe = next((r for r in recipes if r.RecipeID == recipe_id), None)
                    bin_row = next((b for b in bin_data if b.recipeID == recipe_id), None)
                    if not recipe or not bin_row:
                        continue

                    rec_dict = model_to_dict(recipe)
                    recipe_batches = batch_data.filter(RecipeID=recipe_id)

                    for bin_name, mat_id in recipe_material_map.get(recipe_id, []):
                        if 'bin' in bin_name:
                            index = bin_name.replace('bin', '')
                            set_key = f'Bin{index}SetWt'
                            act_key = f'Bin{index}Act'
                        elif 'man' in bin_name:
                            index = bin_name.replace('man', '')
                            set_key = f'Man{index}SetWt'
                            act_key = f'ManWt{index}'
                        elif bin_name in ['oil1', 'oil2']:
                            set_key = f'{bin_name.capitalize()}SetWt'
                            act_key = f'{bin_name.capitalize()}Act'
                        elif bin_name == 'medicine':
                            set_key = 'MedSetWt'
                            act_key = 'MedicineWt'
                        elif bin_name == 'premix1':
                            set_key = 'Premix1Set'
                            act_key = 'PremixWt1'
                        elif bin_name == 'premix2':
                            set_key = 'Premix2Set'
                            act_key = 'PremixWt2'
                        else:
                            continue

                        set_wt_single = rec_dict.get(set_key) or 0
                        batch_count = recipe_batches.count()
                        set_wt = set_wt_single * batch_count
                        act_sum = sum(model_to_dict(b).get(act_key) or 0 for b in recipe_batches)

                        if mat_id not in total_material_data:
                            total_material_data[mat_id] = {
                                'material': material_map.get(mat_id, f'MatID {mat_id}'),
                                'set_total': 0,
                                'actual_total': 0,
                                'error_total': 0,
                                'error_pct': 0,
                            }

                        total_material_data[mat_id]['set_total'] += set_wt
                        total_material_data[mat_id]['actual_total'] += act_sum
                        total_material_data[mat_id]['error_total'] += act_sum - set_wt

                for mat_id, data in total_material_data.items():
                    if data['set_total'] > 0:
                        data['error_pct'] = (data['error_total'] / data['set_total']) * 100
                    else:
                        data['error_pct'] = 0

                total_set = sum(row['set_total'] for row in total_material_data.values())
                total_actual = sum(row['actual_total'] for row in total_material_data.values())
                total_error = total_actual - total_set
                total_error_pct = (total_error / total_set * 100) if total_set else 0

        except Exception as e:
            print("Error in daily_consumption:", e)

    return render(request, 'custom-consumption-report.html', {
        'plants': plants,
        'plant_name': plant_name,
        'total_material_data': total_material_data,
        'total_set': total_set,
        'total_actual': total_actual,
        'total_error': total_error,
        'total_error_pct': total_error_pct,
        'start_date': start_date,
        'end_date': end_date,
        'is_plant_owner': request.user.designation == 'plant_owner',
    })   
    
@login_required
def custom_motor(request):
    plants = []
    recipe_ids = []
    motor_data = []
    plant_id = None
    start_date = date.today().isoformat()
    end_date = date.today().isoformat() 
    plant_name = []

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
    start_date = date.today().isoformat()
    end_date = date.today().isoformat() 
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
    start_date = date.today().isoformat()
    end_date = date.today().isoformat()
    batch_data = BatchData.objects.none()
     
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
    
    