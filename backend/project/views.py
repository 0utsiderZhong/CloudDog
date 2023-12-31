from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes

from handler import APIResponse
from project.models import Project
from project.serializers import ProjectSerializer
from paginator import CustomPaginator
from .permissions import IsAdminUserOrReadOnly

import logging
import time

logger = logging.getLogger('clouddog')

PROJECT_SERIALIZER_FIELDS = ['id', 'cloud_platform', 'region', 'account', 'project_name', 'status', 'create_time', 'cron_toggle']


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_list(request):
    if request.method == 'GET':
        project_list = Project.objects.values(
            'id',
            'cloud_platform',
            'region',
            'account',
            'project_name',
            'status',
            'create_time',
            'cron_toggle'
        ).order_by('-id')

        paginator = CustomPaginator(request, project_list)
        data = paginator.get_page()
        total = paginator.count

        serializer = ProjectSerializer(data, many=True, fields=PROJECT_SERIALIZER_FIELDS)
        logger.info("{} call project list api".format(request.user.username))
        return APIResponse(code=0, msg='success', total=total, data=serializer.data)


# select * from project where project.project_name = project_name and cloud_platform = cloud_platform
# projectList = Project.objects.all().extra(tables=['project'], where=['project.project_name = project_name', 'cloud_platform = cloud_platform'])
@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def search(request):
    try:
        cloud_platform = request.GET.get('cloud_platform', None)
        project_name = request.GET.get('project_name', None)
        project_list = Project.objects.values(
            'id',
            'cloud_platform',
            'region',
            'account',
            'project_name',
            'status',
            'create_time',
            'cron_toggle'
        ).order_by('-id')
        if cloud_platform and cloud_platform != "All":
            project_list = project_list.filter(cloud_platform=cloud_platform)
        if project_name:
            project_list = project_list.filter(project_name__icontains=project_name)
        paginator = CustomPaginator(request, project_list)
        data = paginator.get_page()
        total = paginator.count
    except Project.DoesNotExist:
        return APIResponse(code=1, msg='no exist err')
    serializer = ProjectSerializer(data, many=True, fields=PROJECT_SERIALIZER_FIELDS)
    logger.info("{} call project search api with conditions cloud_platform: {}, project_name: {}".format(request.user.username, cloud_platform, project_name))
    return APIResponse(code=0, msg='request successfully', total=total, data=serializer.data)


@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminUserOrReadOnly])
def create_or_update(request):
    try:
        project = Project.objects.update_or_create(id=request.data['id'], defaults={
            'account': request.data['account'],
            'region': request.data['region'],
            'project_name': request.data['project_name'],
            'status': request.data['status'],
            'project_access_key': request.data['project_access_key'],
            'project_secret_key': request.data['project_secret_key'],
            'create_time': request.data['create_time']
        })
        logger.info("{} call project create_or_update api, request data: {}".format(request.user.username, request.data))
        return APIResponse(code=0, msg='operate project successfully', data=project)
    except Project.DoesNotExist:
        return APIResponse(code=1, msg='no exist error')


@api_view(['DELETE'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminUserOrReadOnly])
def delete(request):
    try:
        project_id = request.GET.get('id', None)
        delete_instance = Project.objects.get(id=project_id)
        logger.info("{}, delete projects {}".format(time.strftime('%X'), delete_instance))
        Project.objects.filter(id=project_id).delete()
    except Project.DoesNotExist:
        return APIResponse(code=1, msg='no exist error')
    logger.info("{} call project delete api, request data: {}".format(request.user.username, delete_instance))
    return APIResponse(code=0, msg='delete successfully')
