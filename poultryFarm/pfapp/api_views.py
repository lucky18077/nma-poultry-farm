from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Plant,BagData
from django.http import JsonResponse
from .serializers import RecipemainSerializer,BatchDataSerializer,MotorDataSerializer,MaterialNameSerializer,BinNameSerializer,BagDataInsertSerializer
from rest_framework import status
from datetime import datetime

# ******api view********

@api_view(['GET'])
def plant_list_api(request):
    plants = Plant.objects.all().values('plant_id', 'plant_name')
    return JsonResponse(list(plants), safe=False)

@api_view(['POST'])
def insert_batchdata(request):
    try:
        # Get headers
        plant_header_id = request.headers.get('Plant-ID') or request.headers.get('plant_id')
        plant_key = request.headers.get('plant_key')

        # Validate presence of plant_id and plant_key
        if not plant_header_id:
            return Response({'status': 'error', 'message': 'Plant ID not found in header'}, status=status.HTTP_400_BAD_REQUEST)
        if not plant_key:
            return Response({'status': 'error', 'message': 'Plant key not found in header'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plant = Plant.objects.get(
                plant_id=plant_header_id,
                plant_status=0,           
                plant_key=plant_key       
            )
        except Plant.DoesNotExist:
            return Response({'status': 'error', 'message': 'Plant ID, Status or Key not valid'}, status=status.HTTP_403_FORBIDDEN)

        if isinstance(request.data, dict) and 'data' in request.data:
            batch = request.data['data']
        else:
            return Response({'status': 'error', 'message': 'Missing data list'}, status=status.HTTP_400_BAD_REQUEST)

        for bch in batch:
            bch['plant_id'] = plant_header_id  # assign plant_id from header
            serializer = BatchDataSerializer(data=bch)
            if serializer.is_valid():
                serializer.save()
            else:
                return Response({'status': 'error', 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 'success', 'message': 'All Batch Data inserted successfully'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['POST'])
def insert_recipe(request):
    try:
        # Get headers
        plant_header_id = request.headers.get('Plant-ID') or request.headers.get('plant_id')
        plant_key = request.headers.get('plant_key')

        # Validate presence of plant_id and plant_key
        if not plant_header_id:
            return Response({'status': 'error', 'message': 'Plant ID not found in header'}, status=status.HTTP_400_BAD_REQUEST)
        if not plant_key:
            return Response({'status': 'error', 'message': 'Plant key not found in header'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plant = Plant.objects.get(
                plant_id=plant_header_id,
                plant_status=0,           
                plant_key=plant_key       
            )
        except Plant.DoesNotExist:
            return Response({'status': 'error', 'message': 'Plant ID, Status or Key not valid'}, status=status.HTTP_403_FORBIDDEN)

        if isinstance(request.data, dict) and 'data' in request.data:
            recipes = request.data['data']
        else:
            return Response({'status': 'error', 'message': 'Missing data list'}, status=status.HTTP_400_BAD_REQUEST)

        for recipe in recipes:
            recipe['plant_id'] = plant_header_id  # assign plant_id from header
            serializer = RecipemainSerializer(data=recipe)
            if serializer.is_valid():
                serializer.save()
            else:
                return Response({'status': 'error', 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 'success', 'message': 'All recipes inserted successfully'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  
  
 # new   
@api_view(['POST'])
def insert_motordata(request):
    try:
        # Get headers
        plant_header_id = request.headers.get('Plant-ID') or request.headers.get('plant_id')
        plant_key = request.headers.get('plant_key')

        # Validate presence of plant_id and plant_key
        if not plant_header_id:
            return Response({'status': 'error', 'message': 'Plant ID not found in header'}, status=status.HTTP_400_BAD_REQUEST)
        if not plant_key:
            return Response({'status': 'error', 'message': 'Plant key not found in header'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plant = Plant.objects.get(
                plant_id=plant_header_id,
                plant_status=0,           
                plant_key=plant_key       
            )
        except Plant.DoesNotExist:
            return Response({'status': 'error', 'message': 'Plant ID, Status or Key not valid'}, status=status.HTTP_403_FORBIDDEN)

        if isinstance(request.data, dict) and 'data' in request.data:
            motors = request.data['data']
        else:
            return Response({'status': 'error', 'message': 'Missing data list'}, status=status.HTTP_400_BAD_REQUEST)

        for motor in motors:
            motor['plant_id'] = plant_header_id  # assign plant_id from header
            serializer = MotorDataSerializer(data=motor)
            if serializer.is_valid():
                serializer.save()
            else:
                return Response({'status': 'error', 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 'success', 'message': 'All Motor Data inserted successfully'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def insert_materialname(request):
    try:
        # Get headers
        plant_header_id = request.headers.get('Plant-ID') or request.headers.get('plant_id')
        plant_key = request.headers.get('plant_key')

        # Validate presence of plant_id and plant_key
        if not plant_header_id:
            return Response({'status': 'error', 'message': 'Plant ID not found in header'}, status=status.HTTP_400_BAD_REQUEST)
        if not plant_key:
            return Response({'status': 'error', 'message': 'Plant key not found in header'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plant = Plant.objects.get(
                plant_id=plant_header_id,
                plant_status=0,           
                plant_key=plant_key       
            )
        except Plant.DoesNotExist:
            return Response({'status': 'error', 'message': 'Plant ID, Status or Key not valid'}, status=status.HTTP_403_FORBIDDEN)

        if isinstance(request.data, dict) and 'data' in request.data:
            recipes = request.data['data']
        else:
            return Response({'status': 'error', 'message': 'Missing data list'}, status=status.HTTP_400_BAD_REQUEST)

        for recipe in recipes:
            recipe['plant_id'] = plant_header_id  # assign plant_id from header
            serializer = MaterialNameSerializer(data=recipe)
            if serializer.is_valid():
                serializer.save()
            else:
                return Response({'status': 'error', 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 'success', 'message': 'All recipes inserted successfully'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
@api_view(['POST'])
def insert_binname(request):
    try:
        # Get headers
        plant_header_id = request.headers.get('Plant-ID') or request.headers.get('plant_id')
        plant_key = request.headers.get('plant_key')

        # Validate presence of plant_id and plant_key
        if not plant_header_id:
            return Response({'status': 'error', 'message': 'Plant ID not found in header'}, status=status.HTTP_400_BAD_REQUEST)
        if not plant_key:
            return Response({'status': 'error', 'message': 'Plant key not found in header'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plant = Plant.objects.get(
                plant_id=plant_header_id,
                plant_status=0,           
                plant_key=plant_key       
            )
        except Plant.DoesNotExist:
            return Response({'status': 'error', 'message': 'Plant ID, Status or Key not valid'}, status=status.HTTP_403_FORBIDDEN)

        if isinstance(request.data, dict) and 'data' in request.data:
            recipes = request.data['data']
        else:
            return Response({'status': 'error', 'message': 'Missing data list'}, status=status.HTTP_400_BAD_REQUEST)

        for recipe in recipes:
            recipe['plant_id'] = plant_header_id  # assign plant_id from header
            serializer = BinNameSerializer(data=recipe)
            if serializer.is_valid():
                serializer.save()
            else:
                return Response({'status': 'error', 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 'success', 'message': 'All Binname inserted successfully'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  
    
@api_view(['POST'])
def insert_bagdata(request):   
    try:
        # Get headers
        plant_header_id = request.headers.get('Plant-ID') or request.headers.get('plant_id')
        plant_key = request.headers.get('plant_key')

        # Validate presence of plant_id and plant_key
        if not plant_header_id:
            return Response({'status': 'error', 'message': 'Plant ID not found in header'}, status=status.HTTP_400_BAD_REQUEST)
        if not plant_key:
            return Response({'status': 'error', 'message': 'Plant key not found in header'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plant = Plant.objects.get(
                plant_id=plant_header_id,
                plant_status=0,           
                plant_key=plant_key       
            )
        except Plant.DoesNotExist:
            return Response({'status': 'error', 'message': 'Plant ID, Status or Key not valid'}, status=status.HTTP_403_FORBIDDEN)

        if isinstance(request.data, dict) and 'data' in request.data:
            bags = request.data['data']
        else:
            return Response({'status': 'error', 'message': 'Missing data list'}, status=status.HTTP_400_BAD_REQUEST)

        for bag in bags:
            bag['plant_id'] = plant_header_id  # assign plant_id from header
            serializer = BagDataInsertSerializer(data=bag)
            if serializer.is_valid():
                serializer.save()
            else:
                return Response({'status': 'error', 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 'success', 'message': 'All BagData inserted successfully'}, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)     