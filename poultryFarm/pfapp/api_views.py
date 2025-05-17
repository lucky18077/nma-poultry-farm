from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Plant,BatchData
from django.http import JsonResponse
from .serializers import RecipemainSerializer
from rest_framework import status

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
            serializer = RecipemainSerializer(data=data_list, many=True)
        else:
            data = request.data.copy()
            data['plant'] = plant.id
            serializer = RecipemainSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'success', 'message': 'Batch data inserted successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'status': 'error', 'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)