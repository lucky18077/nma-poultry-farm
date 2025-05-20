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
        plant_header_id = request.headers.get('Plant-ID') or request.headers.get('plant_id')
        print('Received Plant ID:', plant_header_id)

        if not plant_header_id:
            return Response({'status': 'error', 'message': 'Plant ID not found in Header'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plant = Plant.objects.get(plant_id=plant_header_id)
        except Plant.DoesNotExist:
            return Response({'status': 'error', 'message': 'Plant ID not Match'}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(request.data, list):
            data_list = []
            for item in request.data:
                item['plant'] = plant.id
                data_list.append(item)
            serializer = BatchDataSerializer(data=data_list, many=True)
        else:
            data = request.data.copy()
            data['plant'] = plant.id
            serializer = BatchDataSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'message': 'Batch data inserted successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'status': 'error', 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['POST'])
def insert_recipe(request):
    try:
        plant_header_id = request.headers.get('Plant-ID') or request.headers.get('plant_id')
        print('Received Plant ID:', plant_header_id)

        if not plant_header_id:
            return Response({'status': 'error', 'message': 'Plant ID not found in Header'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plant = Plant.objects.get(plant_id=plant_header_id)
        except Plant.DoesNotExist:
            return Response({'status': 'error', 'message': 'Plant ID not Match'}, status=status.HTTP_400_BAD_REQUEST)

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
        plant_header_id = request.headers.get('Plant-ID') or request.headers.get('plant_id')
        print('Received Plant ID:', plant_header_id)

        if not plant_header_id:
            return Response({'status': 'error', 'message': 'Plant ID not found in Header'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plant = Plant.objects.get(plant_id=plant_header_id)
        except Plant.DoesNotExist:
            return Response({'status': 'error', 'message': 'Plant ID not Match'}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        serializer = MotorDataSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'message': 'Motor data inserted successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'status': 'error', 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
    
@api_view(['POST'])
def insert_materialname(request):
    try:
        plant_header_id = request.headers.get('Plant-ID') or request.headers.get('plant_id')
        print('Received Plant ID:', plant_header_id)

        if not plant_header_id:
            return Response({'status': 'error', 'message': 'Plant ID not found in Header'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plant = Plant.objects.get(plant_id=plant_header_id)
        except Plant.DoesNotExist:
            return Response({'status': 'error', 'message': 'Plant ID not Match'}, status=status.HTTP_400_BAD_REQUEST)

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
        plant_header_id = request.headers.get('Plant-ID') or request.headers.get('plant_id')
        print('Received Plant ID:', plant_header_id)

        if not plant_header_id:
            return Response({'status': 'error', 'message': 'Plant ID not found in Header'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plant = Plant.objects.get(plant_id=plant_header_id)
        except Plant.DoesNotExist:
            return Response({'status': 'error', 'message': 'Plant ID not Match'}, status=status.HTTP_400_BAD_REQUEST)

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
        plant_header_id = request.headers.get('Plant-ID') or request.headers.get('plant_id')
        print('Received Plant ID:', plant_header_id)

        if not plant_header_id:
            return Response({'status': 'error', 'message': 'Plant ID not found in Header'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plant = Plant.objects.get(plant_id=plant_header_id)
        except Plant.DoesNotExist:
            return Response({'status': 'error', 'message': 'Plant ID not Match'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = BagDataInsertSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'status': 'error', 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        # Insert manually using model
        BagData.objects.create(
            sdate=validated_data['sdate'],
            sTime=validated_data['sTime'],
            bagcount=validated_data['bagcount'],
            plant=plant
        )

        return Response({'status': 'success', 'message': 'Bag data inserted successfully'}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)     