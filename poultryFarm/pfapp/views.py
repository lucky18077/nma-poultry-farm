from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.db import connection
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

    if request.method == 'GET': 
        selected_datetime_str = request.GET.get('select_date')  or date.today().strftime('%Y-%m-%d')
        # Only get plant_id from POST for non-plant-owner
        if request.user.designation != 'plant_owner':
            plant_id = request.GET.get('plant_id')

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

    if request.method == 'GET':
        from_date_str = request.GET.get('from_datetime') or date.today().strftime('%Y-%m-%d')
        to_date_str = request.GET.get('to_datetime') or date.today().strftime('%Y-%m-%d')

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
    batch_data = []
    filtered_data = []
    plant_name = None

    # Fetch plants based on user role
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

    if request.method == "GET":
        start_date = request.GET.get('start_date') or date.today().strftime('%Y-%m-%d')
        plant_id = request.GET.get('plant_id')

        if plant_id and start_date:
            plant_name = Plant.objects.filter(plant_id=plant_id).first()
            batch_data = BatchData.objects.filter(plant_id=plant_id, stdate=start_date)
            grouped = batch_data.values('RecipeID').annotate(count=Count('RecipeID'))

            # Fields and correct mappings
            field_map = {
                **{f'Bin{i}': ('Bin' + str(i) + 'SetWt', 'Bin' + str(i) + 'Act') for i in range(1, 17)},
                **{f'Man{i}': ('Man' + str(i) + 'SetWt', 'Man' + 'Wt' + str(i)) for i in range(1, 21)},
                **{f'Oil{i}': ('Oil' + str(i) + 'SetWt', 'Oil' + str(i) + 'Act') for i in range(1, 3)},
                'Medicine': ('MedSetWt', 'MedicineWt'),
                'Molasses': ('MolassesSetWt', 'MolassesAct'),
                'Premix1': ('Premix1Set', 'Premix1Act'),
                'Premix2': ('Premix2Set', 'Premix2Act'),
            }
            for item in grouped:
                recipe_id = item['RecipeID']
                count = item['count']
                batches = batch_data.filter(RecipeID=recipe_id).values('BatchID', 'stTime')
                actual_batches = []
                material_names = []
                set_weights = []
                actual_fields = []
                with connection.cursor() as cursor:
                    # Get recipe name
                    cursor.execute("SELECT RecipeName FROM recipemain WHERE RecipeID = %s", [recipe_id])
                    recipe_name_result = cursor.fetchone()
                    recipe_name = recipe_name_result[0] if recipe_name_result else 'Unknown'

                    # Loop over fields and extract valid material info
                    for field_key, (set_field, actual_field) in field_map.items():
                        try:
                            cursor.execute(f"""
                                SELECT m.MatName, r.{set_field}
                                FROM binname b
                                JOIN materialname m ON m.MatID = b.{field_key}
                                JOIN recipemain r ON r.RecipeID = b.RecipeID
                                WHERE b.RecipeID = %s AND r.{set_field} > 0
                            """, [recipe_id])
                            result = cursor.fetchone()
                            if result:
                                material_names.append(result[0])
                                set_weights.append(float(result[1]))
                                actual_fields.append(actual_field)
                        except Exception:
                            continue

                # For each batch, get actual values
                for batch in batches:
                    batch_row = batch_data.filter(BatchID=batch['BatchID']).first()
                    if batch_row:
                        actual_values = []
                        for field in actual_fields:
                            value = getattr(batch_row, field, None)
                            actual_values.append(float(value) if value else 0)
                        actual_batches.append({
                            'batch_no': batch['BatchID'],
                            'start_time': batch['stTime'],
                            'actual_values': actual_values
                        })

                # Final data append
                filtered_data.append({
                    'RecipeName': recipe_name,
                    'BatchCount': count,
                    'MaterialNames': material_names,
                    'Materials': set_weights,
                    'ActualBatches': actual_batches
                })

    return render(request, 'daily-batch-report.html', {
        'plants': plants,
        'plant_id': plant_id,
        'start_date': start_date,
        'filtered_data': filtered_data,
        'plant_name':plant_name,
        'is_plant_owner': request.user.designation == 'plant_owner',
    })
    
@login_required
def daily_recipe(request):
    plants = []
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

    if request.method == "GET":
        start_date = request.GET.get('start_date') or date.today().strftime('%Y-%m-%d')
        plant_id = request.GET.get('plant_id')

        if plant_id and start_date:
            plant_name = Plant.objects.filter(plant_id=plant_id).first()
            batch_data = BatchData.objects.filter(plant_id=plant_id, stdate=start_date)
            grouped = batch_data.values('RecipeID').annotate(count=Count('RecipeID'))

            field_map = {
                **{f'Bin{i}': ('Bin' + str(i) + 'SetWt', 'Bin' + str(i) + 'Act') for i in range(1, 17)},
                **{f'Man{i}': ('Man' + str(i) + 'SetWt', 'Man' + 'Wt' + str(i)) for i in range(1, 21)},
                **{f'Oil{i}': ('Oil' + str(i) + 'SetWt', 'Oil' + str(i) + 'Act') for i in range(1, 3)},
                'Medicine': ('MedSetWt', 'MedicineWt'),
                'Molasses': ('MolassesSetWt', 'MolassesAct'),
                'Premix1': ('Premix1Set', 'Premix1Act'),
                'Premix2': ('Premix2Set', 'Premix2Act'),
            }

            for item in grouped:
                recipe_id = item['RecipeID']
                batch_count = item['count']
                material_rows = []
                set_total = 0
                actual_total = 0

                with connection.cursor() as cursor:
                    # Get Recipe Name
                    cursor.execute("SELECT RecipeName FROM recipemain WHERE RecipeID = %s", [recipe_id])
                    recipe_name_result = cursor.fetchone()
                    recipe_name = recipe_name_result[0] if recipe_name_result else 'Unknown'

                    for field_key, (set_field, actual_field) in field_map.items():
                        try:
                            # Get material name and set wt from recipemain
                            cursor.execute(f"""
                                SELECT m.MatName, r.{set_field}
                                FROM binname b
                                JOIN materialname m ON m.MatID = b.{field_key}
                                JOIN recipemain r ON r.RecipeID = b.RecipeID
                                WHERE b.RecipeID = %s AND r.{set_field} > 0
                            """, [recipe_id])
                            result = cursor.fetchone()
                            if not result:
                                continue

                            mat_name = result[0]
                            single_set_wt = float(result[1])
                            set_wt = single_set_wt * batch_count

                            # Sum actual wt
                            cursor.execute(f"""
                                SELECT SUM({actual_field}) FROM batchdata
                                WHERE plant_id = %s AND stdate = %s AND RecipeID = %s
                            """, [plant_id, start_date, recipe_id])
                            act_result = cursor.fetchone()
                            act_sum = float(act_result[0]) if act_result and act_result[0] else 0

                            error = act_sum - set_wt
                            error_pct = (error / set_wt * 100) if set_wt else 0

                            material_rows.append({
                                'bin': field_key,
                                'material': mat_name,
                                'set_wt': set_wt,
                                'actual_wt': act_sum,
                                'error': error,
                                'error_pct': error_pct
                            })

                            set_total += set_wt
                            actual_total += act_sum
                        except Exception:
                            continue

                error_total = set_total - actual_total
                error_total_pct = (error_total / set_total * 100) if set_total else 0

                batch_actual.append({
                    'RecipeID': recipe_id,
                    'RecipeName': recipe_name,
                    'BatchCount': batch_count,
                    'materials': material_rows,
                    'set_total_all': set_total,
                    'total_all': actual_total,
                    'error_total': error_total,
                    'error_total_pct': error_total_pct
                })

    return render(request, 'daily-recipe-report.html', {
        'plants': plants,
        'plant_id': plant_id,
        'plant_name': plant_name,
        'start_date': start_date,
        'batch_actual': batch_actual
    })

@login_required
def daily_consumption(request):
    plants = []
    plant_name = None
    start_date = date.today().isoformat()
    total_material_data = {}
    grand_set_total = 0
    grand_actual_total = 0
    total_error = 0
    total_error_pct = 0

    try:
        if request.user.is_superuser:
            plants = Plant.objects.all()
        elif request.user.designation == 'manufacture':
            child_ids = request.session.get('child_ids', [])
            plants = Plant.objects.filter(plant_owner_id__in=child_ids)
        elif request.user.designation == 'plant_owner':
            plant = Plant.objects.filter(plant_owner_id=request.user.id).first()
            if plant:
                plants = [plant]

        if request.method == "GET":
            start_date = request.GET.get('start_date') or date.today().strftime('%Y-%m-%d')
            plant_id = request.GET.get('plant_id')

            if plant_id and start_date:
                plant_name = Plant.objects.filter(plant_id=plant_id).first()
                batch_data = BatchData.objects.filter(plant_id=plant_id, stdate=start_date)
                grouped = batch_data.values('RecipeID').annotate(count=Count('RecipeID'))

                field_map = {
                    **{f'Bin{i}': ('Bin' + str(i) + 'SetWt', 'Bin' + str(i) + 'Act') for i in range(1, 17)},
                    **{f'Man{i}': ('Man' + str(i) + 'SetWt', 'Man' + 'Wt' + str(i)) for i in range(1, 21)},
                    **{f'Oil{i}': ('Oil' + str(i) + 'SetWt', 'Oil' + str(i) + 'Act') for i in range(1, 3)},
                    'Medicine': ('MedSetWt', 'MedicineWt'),
                    'Molasses': ('MolassesSetWt', 'MolassesAct'),
                    'Premix1': ('Premix1Set', 'Premix1Act'),
                    'Premix2': ('Premix2Set', 'Premix2Act'),
                }

                for item in grouped:
                    recipe_id = item['RecipeID']
                    batch_count = item['count']

                    with connection.cursor() as cursor:
                        for field_key, (set_field, actual_field) in field_map.items():
                            try:
                                # Fetch material name and set weight
                                cursor.execute(f"""
                                    SELECT m.MatName, r.{set_field}
                                    FROM binname b
                                    JOIN materialname m ON m.MatID = b.{field_key}
                                    JOIN recipemain r ON r.RecipeID = b.RecipeID
                                    WHERE b.RecipeID = %s AND r.{set_field} > 0
                                """, [recipe_id])
                                result = cursor.fetchone()
                                if not result:
                                    continue

                                mat_name = result[0]
                                single_set_wt = float(result[1])
                                set_wt = single_set_wt * batch_count

                                # Fetch actual sum
                                cursor.execute(f"""
                                    SELECT SUM({actual_field}) FROM batchdata
                                    WHERE plant_id = %s AND stdate = %s AND RecipeID = %s
                                """, [plant_id, start_date, recipe_id])
                                act_result = cursor.fetchone()
                                act_sum = float(act_result[0]) if act_result and act_result[0] else 0

                                # Aggregate by material
                                if mat_name not in total_material_data:
                                    total_material_data[mat_name] = {
                                        'material': mat_name,
                                        'set_total': 0,
                                        'actual_total': 0,
                                    }

                                total_material_data[mat_name]['set_total'] += set_wt
                                total_material_data[mat_name]['actual_total'] += act_sum
                                grand_set_total += set_wt
                                grand_actual_total += act_sum

                            except Exception as e:
                                # Handle individual material errors
                                continue

                # Final totals
                for row in total_material_data.values():
                    row['error_total'] = row['actual_total'] - row['set_total']
                    row['error_pct'] = (row['error_total'] / row['set_total'] * 100) if row['set_total'] else 0

                total_error = grand_actual_total - grand_set_total
                total_error_pct = (total_error / grand_set_total * 100) if grand_set_total else 0

    except Exception as e:
        # Optional: Log error or display message
        print("Error in daily_consumption:", e)

    return render(request, 'daily-consumption-report.html', {
        'plants': plants,
        'plant_name': plant_name,
        'start_date': start_date,
        'total_material_data': total_material_data,
        'total_set': grand_set_total,
        'total_actual': grand_actual_total,
        'total_error': total_error,
        'total_error_pct': total_error_pct,
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

    if request.method == "GET":
        start_date = request.GET.get('start_date') or date.today().strftime('%Y-%m-%d')
        plant_id = request.GET.get('plant_id')

        try:
            if plant_id and start_date:
                plant_name = Plant.objects.filter(plant_id=plant_id).first()
                motor_data = MotorData.objects.filter(
                    plant_id=plant_id,
                    sdate=start_date
                ).filter(
                    Q(ScrewRPM__gt=0) |
                    Q(hammercurrent__gt=0) |
                    Q(rvfrpm__gt=0) |
                    Q(pelletcurrent__gt=0) |
                    Q(feederRPM__gt=0) |
                    Q(hygenizerRPM__gt=0) |
                    Q(crumblerfeederRPM__gt=0) |
                    Q(molassesRPM__gt=0) |
                    Q(blowerRPM__gt=0)
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

    if request.method == "GET":
        start_date = request.GET.get('start_date') or date.today().strftime('%Y-%m-%d')
        plant_id = request.GET.get('plant_id')
        try:
            if plant_id and start_date:
                plant_name = Plant.objects.filter(plant_id=plant_id).first()
                bagging_data = BagData.objects.filter(
                    plant_id=plant_id,
                    sdate=start_date
                ).filter(
                    Q(bagcount__gt=0) | Q(bagWT__gt=0)
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

    if request.method == "GET":
        start_date = request.GET.get('start_date') or date.today().strftime('%Y-%m-%d')
        plant_id = request.GET.get('plant_id')
        shift = request.GET.get('shift')

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

                        raw_batch_data = BatchData.objects.filter(
                            plant_id=plant_id,
                            stdate=start_date
                        )

                        batch_data_list = []
                        for batch in raw_batch_data:
                            try:
                                full_datetime_str = f"{batch.stdate} {batch.stTime}"
                                batch_datetime = datetime.strptime(full_datetime_str, "%Y-%m-%d %H:%M:%S")
                                if shift_start_dt <= batch_datetime <= shift_end_dt:
                                    batch_data_list.append(batch.BatchID)
                            except Exception as e:
                                print(f"Skipping invalid datetime: {batch.stdate} {batch.stTime} | Error: {e}")

                        batch_data = BatchData.objects.filter(BatchID__in=batch_data_list)
                    else:
                        batch_data = BatchData.objects.filter(plant_id=plant_id, stdate=start_date)
                else:
                    batch_data = BatchData.objects.filter(plant_id=plant_id, stdate=start_date)

                grouped = batch_data.values('RecipeID').annotate(count=Count('RecipeID'))

                field_map = {
                    **{f'Bin{i}': ('Bin' + str(i) + 'SetWt', 'Bin' + str(i) + 'Act') for i in range(1, 17)},
                    **{f'Man{i}': ('Man' + str(i) + 'SetWt', 'Man' + 'Wt' + str(i)) for i in range(1, 21)},
                    **{f'Oil{i}': ('Oil' + str(i) + 'SetWt', 'Oil' + str(i) + 'Act') for i in range(1, 3)},
                    'Medicine': ('MedSetWt', 'MedicineWt'),
                    'Molasses': ('MolassesSetWt', 'MolassesAct'),
                    'Premix1': ('Premix1Set', 'Premix1Act'),
                    'Premix2': ('Premix2Set', 'Premix2Act'),
                }

                for item in grouped:
                    recipe_id = item['RecipeID']
                    count = item['count']
                    batches = batch_data.filter(RecipeID=recipe_id).values('BatchID', 'stTime')
                    actual_batches = []
                    material_names = []
                    set_weights = []
                    actual_fields = []

                    with connection.cursor() as cursor:
                        cursor.execute("SELECT RecipeName FROM recipemain WHERE RecipeID = %s", [recipe_id])
                        recipe_name_result = cursor.fetchone()
                        recipe_name = recipe_name_result[0] if recipe_name_result else 'Unknown'

                        for field_key, (set_field, actual_field) in field_map.items():
                            try:
                                cursor.execute(f"""
                                    SELECT m.MatName, r.{set_field}
                                    FROM binname b
                                    JOIN materialname m ON m.MatID = b.{field_key}
                                    JOIN recipemain r ON r.RecipeID = b.RecipeID
                                    WHERE b.RecipeID = %s AND r.{set_field} > 0
                                """, [recipe_id])
                                result = cursor.fetchone()
                                if result:
                                    material_names.append(result[0])
                                    set_weights.append(float(result[1]))
                                    actual_fields.append(actual_field)
                            except Exception:
                                continue

                    for batch in batches:
                        batch_row = batch_data.filter(BatchID=batch['BatchID']).first()
                        if batch_row:
                            actual_values = []
                            for field in actual_fields:
                                value = getattr(batch_row, field, None)
                                actual_values.append(float(value) if value else 0)
                            actual_batches.append({
                                'batch_no': batch['BatchID'],
                                'start_time': batch['stTime'],
                                'actual_values': actual_values
                            })

                    # Prepare zipped materials for template
                    materials = list(zip(material_names, set_weights))

                    filtered_data.append({
                        'RecipeName': recipe_name,
                        'BatchCount': count,
                        'Materials': materials,
                        'ActualBatches': actual_batches
                    })

        except Exception as e:
            print(f"Error in batch_shift: {e}")

    return render(request, 'batch-shift-report.html', {
        'plants': plants,
        'start_date': start_date,
        'plant_id': plant_id,
        'shift': shift,
        'plant_name': plant_name,
        'filtered_data': filtered_data,
    })
     
@login_required
def recipe_shift(request):
    plants = []
    batch_data = []
    batch_actual = []
    plant_id = None
    shift = None
    start_date = date.today().isoformat()
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

    if request.method == "GET":
        start_date = request.GET.get('start_date') or date.today().strftime('%Y-%m-%d')
        plant_id = request.GET.get('plant_id')
        shift = request.GET.get('shift')

        if plant_id and start_date:
            plant_name = Plant.objects.filter(plant_id=plant_id).first()

            # Shift filtering
            if shift:
                shift_data = Plant.objects.filter(plant_id=plant_id, **{f'{shift}__isnull': False}).first()
                if shift_data:
                    shift_start_time = getattr(shift_data, shift)
                    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                    shift_start_dt = datetime.combine(start_date_obj, shift_start_time)
                    shift_end_dt = shift_start_dt + timedelta(hours=8)

                    raw_batch_data = BatchData.objects.filter(
                        plant_id=plant_id,
                        stdate=start_date
                    )

                    batch_ids_in_shift = []
                    for batch in raw_batch_data:
                        try:
                            full_datetime = f"{batch.stdate} {batch.stTime}"
                            batch_dt = datetime.strptime(full_datetime, "%Y-%m-%d %H:%M:%S")
                            if shift_start_dt <= batch_dt <= shift_end_dt:
                                batch_ids_in_shift.append(batch.BatchID)
                        except:
                            continue

                    batch_data = BatchData.objects.filter(BatchID__in=batch_ids_in_shift)
                else:
                    batch_data = BatchData.objects.filter(plant_id=plant_id, stdate=start_date)
            else:
                batch_data = BatchData.objects.filter(plant_id=plant_id, stdate=start_date)

            grouped = batch_data.values('RecipeID').annotate(count=Count('RecipeID'))

            field_map = {
                **{f'Bin{i}': ('Bin' + str(i) + 'SetWt', 'Bin' + str(i) + 'Act') for i in range(1, 17)},
                **{f'Man{i}': ('Man' + str(i) + 'SetWt', 'Man' + 'Wt' + str(i)) for i in range(1, 21)},
                **{f'Oil{i}': ('Oil' + str(i) + 'SetWt', 'Oil' + str(i) + 'Act') for i in range(1, 3)},
                'Medicine': ('MedSetWt', 'MedicineWt'),
                'Molasses': ('MolassesSetWt', 'MolassesAct'),
                'Premix1': ('Premix1Set', 'Premix1Act'),
                'Premix2': ('Premix2Set', 'Premix2Act'),
            }

            for item in grouped:
                recipe_id = item['RecipeID']
                batch_count = item['count']
                material_rows = []
                set_total = 0
                actual_total = 0

                with connection.cursor() as cursor:
                    # Get Recipe Name
                    cursor.execute("SELECT RecipeName FROM recipemain WHERE RecipeID = %s", [recipe_id])
                    recipe_name_result = cursor.fetchone()
                    recipe_name = recipe_name_result[0] if recipe_name_result else 'Unknown'

                    for field_key, (set_field, actual_field) in field_map.items():
                        try:
                            # Get material name and set wt from recipemain
                            cursor.execute(f"""
                                SELECT m.MatName, r.{set_field}
                                FROM binname b
                                JOIN materialname m ON m.MatID = b.{field_key}
                                JOIN recipemain r ON r.RecipeID = b.RecipeID
                                WHERE b.RecipeID = %s AND r.{set_field} > 0
                            """, [recipe_id])
                            result = cursor.fetchone()
                            if not result:
                                continue

                            mat_name = result[0]
                            single_set_wt = float(result[1])
                            set_wt = single_set_wt * batch_count

                            # Sum actual wt
                            cursor.execute(f"""
                                SELECT SUM({actual_field}) FROM batchdata
                                WHERE plant_id = %s AND stdate = %s AND RecipeID = %s
                            """, [plant_id, start_date, recipe_id])
                            act_result = cursor.fetchone()
                            act_sum = float(act_result[0]) if act_result and act_result[0] else 0

                            error = act_sum - set_wt
                            error_pct = (error / set_wt * 100) if set_wt else 0

                            material_rows.append({
                                'bin': field_key,
                                'material': mat_name,
                                'set_wt': set_wt,
                                'actual_wt': act_sum,
                                'error': error,
                                'error_pct': error_pct
                            })

                            set_total += set_wt
                            actual_total += act_sum
                        except Exception:
                            continue

                error_total = set_total - actual_total
                error_total_pct = (error_total / set_total * 100) if set_total else 0

                batch_actual.append({
                    'RecipeID': recipe_id,
                    'RecipeName': recipe_name,
                    'BatchCount': batch_count,
                    'materials': material_rows,
                    'set_total_all': set_total,
                    'total_all': actual_total,
                    'error_total': error_total,
                    'error_total_pct': error_total_pct
                })


    context = {
        'plants': plants,
        'batch_actual': batch_actual,
        'plant_id': plant_id,
        'start_date': start_date,
        'shift': shift,
        'plant_name': plant_name,
    }
    return render(request, 'recipe-shift-report.html', context)
    
@login_required
def consumption_shift(request):
    from django.db.models import Count
    from django.db import connection
    from datetime import datetime, timedelta, date
    from .models import Plant, BatchData

    plants = []
    batch_data = []
    total_material_data = {}
    plant_name = None

    start_date = date.today().isoformat()
    grand_set_total = 0
    grand_actual_total = 0

    total_set = 0
    total_actual = 0
    total_error = 0
    total_error_pct = 0

    if request.user.is_superuser:
        plants = Plant.objects.all()
    elif request.user.designation == 'manufacture':
        child_ids = request.session.get('child_ids', [])
        plants = Plant.objects.filter(plant_owner_id__in=child_ids)
    elif request.user.designation == 'plant_owner':
        plant = Plant.objects.filter(plant_owner_id=request.user.id).first()
        if plant:
            plants = [plant]

    if request.method == "GET":
        start_date = request.GET.get('start_date') or date.today().strftime('%Y-%m-%d')
        plant_id = request.GET.get('plant_id')
        shift = request.GET.get('shift')

        try:
            if plant_id and start_date:
                plant_name = Plant.objects.filter(plant_id=plant_id).first()
                batch_ids = []

                if shift:
                    shift_data = Plant.objects.filter(plant_id=plant_id).first()
                    if shift_data and hasattr(shift_data, shift):
                        shift_start_time = getattr(shift_data, shift)
                        shift_start_dt = datetime.combine(datetime.strptime(start_date, "%Y-%m-%d").date(), shift_start_time)
                        shift_end_dt = shift_start_dt + timedelta(hours=8)

                        raw_batches = BatchData.objects.filter(plant_id=plant_id, stdate=start_date)
                        for batch in raw_batches:
                            try:
                                dt_str = f"{batch.stdate} {batch.stTime}"
                                batch_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                                if shift_start_dt <= batch_dt <= shift_end_dt:
                                    batch_ids.append(batch.BatchID)
                            except Exception:
                                continue

                        batch_data = BatchData.objects.filter(BatchID__in=batch_ids)
                    else:
                        batch_data = BatchData.objects.none()
                else:
                    batch_data = BatchData.objects.filter(plant_id=plant_id, stdate=start_date)

                if batch_data.exists():
                    grouped = batch_data.values('RecipeID').annotate(count=Count('RecipeID'))

                    field_map = {
                        **{f'Bin{i}': (f'Bin{i}SetWt', f'Bin{i}Act') for i in range(1, 17)},
                        **{f'Man{i}': (f'Man{i}SetWt', f'ManWt{i}') for i in range(1, 21)},
                        **{f'Oil{i}': (f'Oil{i}SetWt', f'Oil{i}Act') for i in range(1, 3)},
                        'Medicine': ('MedSetWt', 'MedicineWt'),
                        'Molasses': ('MolassesSetWt', 'MolassesAct'),
                        'Premix1': ('Premix1Set', 'Premix1Act'),
                        'Premix2': ('Premix2Set', 'Premix2Act'),
                    }

                    for item in grouped:
                        recipe_id = item['RecipeID']
                        batch_count = item['count']

                        with connection.cursor() as cursor:
                            for field_key, (set_field, actual_field) in field_map.items():
                                try:
                                    cursor.execute(f"""
                                        SELECT m.MatName, r.{set_field}
                                        FROM binname b
                                        JOIN materialname m ON m.MatID = b.{field_key}
                                        JOIN recipemain r ON r.RecipeID = b.RecipeID
                                        WHERE b.RecipeID = %s AND r.{set_field} > 0
                                    """, [recipe_id])
                                    result = cursor.fetchone()
                                    if not result:
                                        continue

                                    mat_name = result[0]
                                    single_set_wt = float(result[1])
                                    set_wt = single_set_wt * batch_count

                                    cursor.execute(f"""
                                        SELECT SUM({actual_field}) FROM batchdata
                                        WHERE plant_id = %s AND stdate = %s AND RecipeID = %s
                                    """, [plant_id, start_date, recipe_id])
                                    act_result = cursor.fetchone()
                                    act_sum = float(act_result[0]) if act_result and act_result[0] else 0

                                    if mat_name not in total_material_data:
                                        total_material_data[mat_name] = {
                                            'material': mat_name,
                                            'set_total': 0,
                                            'actual_total': 0,
                                        }

                                    total_material_data[mat_name]['set_total'] += set_wt
                                    total_material_data[mat_name]['actual_total'] += act_sum
                                    grand_set_total += set_wt
                                    grand_actual_total += act_sum

                                except Exception:
                                    continue

                    # Finalize error calculation
                    for mat in total_material_data.values():
                        set_val = mat['set_total']
                        actual_val = mat['actual_total']
                        error_val = actual_val - set_val
                        error_pct_val = ((error_val / set_val) * 100) if set_val > 0 else 0

                        mat['error_total'] = error_val
                        mat['error_pct'] = error_pct_val

                        total_error += error_val
                        total_set += set_val
                        total_actual += actual_val

                    total_error_pct = (total_error / total_set * 100) if total_set > 0 else 0

        except Exception as e:
            print("Error in shift consumption view:", e)

    return render(request, 'consumption-shift-report.html', {
        'plants': plants,
        'batch_data': batch_data,
        'total_material_data': total_material_data,
        'plant_name': plant_name,
        'total_set': total_set,
        'total_actual': total_actual,
        'total_error': total_error,
        'total_error_pct': total_error_pct,
        'start_date': start_date,
        'selected_shift': shift,
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

    if request.method == "GET":
        start_date = request.GET.get('start_date') or date.today().strftime('%Y-%m-%d')
        shift = request.GET.get('shift')
        plant_id = request.GET.get('plant_id')
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
        'shift':shift,
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

    if request.method == "GET":
        start_date = request.GET.get('start_date') or date.today().strftime('%Y-%m-%d')
        shift = request.GET.get('shift')
        plant_id = request.GET.get('plant_id')
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
        'shift':shift,
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
    if request.method == "GET":
        start_date = request.GET.get('start_date') or date.today().strftime('%Y-%m-%d')
        end_date = request.GET.get('end_date') or date.today().strftime('%Y-%m-%d')
        plant_id = request.GET.get('plant_id')
        
        try:
            if plant_id and start_date and end_date:
                plant_name = Plant.objects.filter(plant_id=plant_id).first()
                batch_data = BatchData.objects.filter(
                    plant_id=plant_id,
                    stdate__range=(start_date, end_date)
                )
                grouped = batch_data.values('RecipeID').annotate(count=Count('RecipeID'))

                # Fields and correct mappings
                field_map = {
                    **{f'Bin{i}': ('Bin' + str(i) + 'SetWt', 'Bin' + str(i) + 'Act') for i in range(1, 17)},
                    **{f'Man{i}': ('Man' + str(i) + 'SetWt', 'Man' + 'Wt' + str(i)) for i in range(1, 21)},
                    **{f'Oil{i}': ('Oil' + str(i) + 'SetWt', 'Oil' + str(i) + 'Act') for i in range(1, 3)},
                    'Medicine': ('MedSetWt', 'MedicineWt'),
                    'Molasses': ('MolassesSetWt', 'MolassesAct'),
                    'Premix1': ('Premix1Set', 'Premix1Act'),
                    'Premix2': ('Premix2Set', 'Premix2Act'),
                }
                for item in grouped:
                    recipe_id = item['RecipeID']
                    count = item['count']
                    batches = batch_data.filter(RecipeID=recipe_id).values('BatchID', 'stTime')
                    actual_batches = []
                    material_names = []
                    set_weights = []
                    actual_fields = []
                    with connection.cursor() as cursor:
                        # Get recipe name
                        cursor.execute("SELECT RecipeName FROM recipemain WHERE RecipeID = %s", [recipe_id])
                        recipe_name_result = cursor.fetchone()
                        recipe_name = recipe_name_result[0] if recipe_name_result else 'Unknown'

                        # Loop over fields and extract valid material info
                        for field_key, (set_field, actual_field) in field_map.items():
                            try:
                                cursor.execute(f"""
                                    SELECT m.MatName, r.{set_field}
                                    FROM binname b
                                    JOIN materialname m ON m.MatID = b.{field_key}
                                    JOIN recipemain r ON r.RecipeID = b.RecipeID
                                    WHERE b.RecipeID = %s AND r.{set_field} > 0
                                """, [recipe_id])
                                result = cursor.fetchone()
                                if result:
                                    material_names.append(result[0])
                                    set_weights.append(float(result[1]))
                                    actual_fields.append(actual_field)
                            except Exception:
                                continue

                    # For each batch, get actual values
                    for batch in batches:
                        batch_row = batch_data.filter(BatchID=batch['BatchID']).first()
                        if batch_row:
                            actual_values = []
                            for field in actual_fields:
                                value = getattr(batch_row, field, None)
                                actual_values.append(float(value) if value else 0)
                            actual_batches.append({
                                'batch_no': batch['BatchID'],
                                'start_time': batch['stTime'],
                                'actual_values': actual_values
                            })

                    # Final data append
                    filtered_data.append({
                        'RecipeName': recipe_name,
                        'BatchCount': count,
                        'MaterialNames': material_names,
                        'Materials': set_weights,
                        'ActualBatches': actual_batches
                    })
        except Exception as e:
            print("Error:", e)        

    return render(request, 'custom-batch-report.html', {
        'plants': plants,
        'recipe_ids': recipe_ids,
        'plant_name': plant_name,
        'filtered_data': filtered_data,
        'plant_name':plant_name,
        'is_plant_owner': request.user.designation == 'plant_owner',
        'start_date':start_date,
        'end_date':end_date,
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
    if request.method == "GET":
        start_date = request.GET.get('start_date') or date.today().strftime('%Y-%m-%d')
        end_date = request.GET.get('end_date') or date.today().strftime('%Y-%m-%d')
        plant_id = request.GET.get('plant_id')
        try:
            if plant_id and start_date and end_date:
                plant_name = Plant.objects.filter(plant_id=request.POST.get('plant_id')).first()
                batch_data = BatchData.objects.filter(
                    plant_id=plant_id,
                    stdate__range=(start_date, end_date)
                )            
                grouped = batch_data.values('RecipeID').annotate(count=Count('RecipeID'))

                field_map = {
                    **{f'Bin{i}': ('Bin' + str(i) + 'SetWt', 'Bin' + str(i) + 'Act') for i in range(1, 17)},
                    **{f'Man{i}': ('Man' + str(i) + 'SetWt', 'Man' + 'Wt' + str(i)) for i in range(1, 21)},
                    **{f'Oil{i}': ('Oil' + str(i) + 'SetWt', 'Oil' + str(i) + 'Act') for i in range(1, 3)},
                    'Medicine': ('MedSetWt', 'MedicineWt'),
                    'Molasses': ('MolassesSetWt', 'MolassesAct'),
                    'Premix1': ('Premix1Set', 'Premix1Act'),
                    'Premix2': ('Premix2Set', 'Premix2Act'),
                }

                for item in grouped:
                    recipe_id = item['RecipeID']
                    batch_count = item['count']
                    material_rows = []
                    set_total = 0
                    actual_total = 0

                    with connection.cursor() as cursor:
                        # Get Recipe Name
                        cursor.execute("SELECT RecipeName FROM recipemain WHERE RecipeID = %s", [recipe_id])
                        recipe_name_result = cursor.fetchone()
                        recipe_name = recipe_name_result[0] if recipe_name_result else 'Unknown'

                        for field_key, (set_field, actual_field) in field_map.items():
                            try:
                                # Get material name and set wt from recipemain
                                cursor.execute(f"""
                                    SELECT m.MatName, r.{set_field}
                                    FROM binname b
                                    JOIN materialname m ON m.MatID = b.{field_key}
                                    JOIN recipemain r ON r.RecipeID = b.RecipeID
                                    WHERE b.RecipeID = %s AND r.{set_field} > 0
                                """, [recipe_id])
                                result = cursor.fetchone()
                                if not result:
                                    continue

                                mat_name = result[0]
                                single_set_wt = float(result[1])
                                set_wt = single_set_wt * batch_count

                                # Sum actual wt
                                cursor.execute(f"""
                                    SELECT SUM({actual_field}) FROM batchdata
                                    WHERE plant_id = %s AND stdate = %s AND RecipeID = %s
                                """, [plant_id, start_date, recipe_id])
                                act_result = cursor.fetchone()
                                act_sum = float(act_result[0]) if act_result and act_result[0] else 0

                                error = act_sum - set_wt
                                error_pct = (error / set_wt * 100) if set_wt else 0

                                material_rows.append({
                                    'bin': field_key,
                                    'material': mat_name,
                                    'set_wt': set_wt,
                                    'actual_wt': act_sum,
                                    'error': error,
                                    'error_pct': error_pct
                                })

                                set_total += set_wt
                                actual_total += act_sum
                            except Exception:
                                continue

                    error_total = set_total - actual_total
                    error_total_pct = (error_total / set_total * 100) if set_total else 0

                    batch_actual.append({
                        'RecipeID': recipe_id,
                        'RecipeName': recipe_name,
                        'BatchCount': batch_count,
                        'materials': material_rows,
                        'set_total_all': set_total,
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

    total_set = 0
    total_actual = 0
    total_error = 0
    total_error_pct = 0

    if request.user.is_superuser:
        plants = Plant.objects.all()
    elif request.user.designation == 'manufacture':
        child_ids = request.session.get('child_ids', [])
        plants = Plant.objects.filter(plant_owner_id__in=child_ids)
    elif request.user.designation == 'plant_owner':
        plant = Plant.objects.filter(plant_owner_id=request.user.id).first()
        if plant:
            plants = [plant]

    if request.method == "GET":
        start_date = request.GET.get('start_date') or date.today().strftime('%Y-%m-%d')
        end_date = request.GET.get('end_date') or date.today().strftime('%Y-%m-%d')
        plant_id = request.GET.get('plant_id')

        try:
            if plant_id and start_date and end_date:
                plant_name = Plant.objects.filter(plant_id=plant_id).first()
                batch_data = BatchData.objects.filter(
                    plant_id=plant_id,
                    stdate__range=(start_date, end_date)
                )
                grouped = batch_data.values('RecipeID').annotate(count=Count('RecipeID'))

                field_map = {
                    **{f'Bin{i}': ('Bin' + str(i) + 'SetWt', 'Bin' + str(i) + 'Act') for i in range(1, 17)},
                    **{f'Man{i}': ('Man' + str(i) + 'SetWt', 'Man' + 'Wt' + str(i)) for i in range(1, 21)},
                    **{f'Oil{i}': ('Oil' + str(i) + 'SetWt', 'Oil' + str(i) + 'Act') for i in range(1, 3)},
                    'Medicine': ('MedSetWt', 'MedicineWt'),
                    'Molasses': ('MolassesSetWt', 'MolassesAct'),
                    'Premix1': ('Premix1Set', 'Premix1Act'),
                    'Premix2': ('Premix2Set', 'Premix2Act'),
                }

                for item in grouped:
                    recipe_id = item['RecipeID']
                    batch_count = item['count']

                    with connection.cursor() as cursor:
                        for field_key, (set_field, actual_field) in field_map.items():
                            try:
                                cursor.execute(f"""
                                    SELECT m.MatName, r.{set_field}
                                    FROM binname b
                                    JOIN materialname m ON m.MatID = b.{field_key}
                                    JOIN recipemain r ON r.RecipeID = b.RecipeID
                                    WHERE b.RecipeID = %s AND r.{set_field} > 0
                                """, [recipe_id])
                                result = cursor.fetchone()
                                if not result:
                                    continue

                                mat_name = result[0]
                                single_set_wt = float(result[1])
                                set_wt = single_set_wt * batch_count

                                cursor.execute(f"""
                                    SELECT SUM({actual_field}) FROM batchdata
                                    WHERE plant_id = %s AND stdate BETWEEN %s AND %s AND RecipeID = %s
                                """, [plant_id, start_date, end_date, recipe_id])
                                act_result = cursor.fetchone()
                                act_sum = float(act_result[0]) if act_result and act_result[0] else 0

                                if mat_name not in total_material_data:
                                    total_material_data[mat_name] = {
                                        'material': mat_name,
                                        'set_total': 0,
                                        'actual_total': 0,
                                    }

                                total_material_data[mat_name]['set_total'] += set_wt
                                total_material_data[mat_name]['actual_total'] += act_sum

                            except Exception as e:
                                continue  # Optionally: log error

                # Final calculations
                for data in total_material_data.values():
                    data['error_total'] = data['actual_total'] - data['set_total']
                    data['error_pct'] = (data['error_total'] / data['set_total'] * 100) if data['set_total'] else 0
                    total_set += data['set_total']
                    total_actual += data['actual_total']
                    total_error += data['error_total']

                total_error_pct = (total_error / total_set * 100) if total_set else 0

        except Exception as e:
            pass  # Optionally log error

    return render(request, 'custom-consumption-report.html', {
        'plants': plants,
        'plant_name': plant_name,
        'total_material_data': total_material_data,
        'total_set': total_set,
        'total_actual': total_actual,
        'total_error': total_error,
        'total_error_pct': total_error_pct,
        'start_date': start_date,
        'end_date': end_date
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

    if request.method == "GET":
        start_date = request.GET.get('start_date') or date.today().strftime('%Y-%m-%d')
        end_date = request.GET.get('end_date') or date.today().strftime('%Y-%m-%d')
        plant_id = request.GET.get('plant_id')

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

    if request.method == "GET":
        start_date = request.GET.get('start_date') or date.today().strftime('%Y-%m-%d')
        end_date = request.GET.get('end_date') or date.today().strftime('%Y-%m-%d')
        plant_id = request.GET.get('plant_id')
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
    shift = request.GET.get('shift')
    plant_id = request.GET.get('plant_id')
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
    if request.method == "GET":
        start_date = request.GET.get('start_date') or date.today().strftime('%Y-%m-%d')
        end_date = request.GET.get('end_date') or date.today().strftime('%Y-%m-%d')
        plant_id = request.GET.get('plant_id')    

    try:
            if plant_id and start_date and end_date:
                plant_name = Plant.objects.filter(plant_id=request.GET.get('plant_id')).first()
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
    
    