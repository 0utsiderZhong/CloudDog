"""backend URL Configuration

The `urlpatterns` list routes URLs to pages. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function pages
    1. Add an import:  from my_app import pages
    2. Add a URL to urlpatterns:  path('', pages.home, name='home')
Class-based pages
    1. Add an import:  from other_app.pages import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.documentation import include_docs_urls
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView, TokenVerifyView)

from cron.base_cron.views import DjangoJobViewSet, DjangoJobExecutionViewSet
from user.views import UserViewSet

router = DefaultRouter()
router.register(r'apsjob', DjangoJobViewSet)
router.register(r'apsexecjob', DjangoJobExecutionViewSet)
router.register(r'user', UserViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/', include(router.urls)),
    path('api/docs', include_docs_urls(title="RestFulAPI", description="RestFulAPI")),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path(r'', include('project.urls'), name='project'),
    path(r'', include('product.alibabacloud_product.urls'), name='alibaba_product'),
    path(r'', include('cron.alibabacloud_cron.urls'), name='ali_cron'),
    path(r'', include('cron.base_cron.urls'), name='base_cron'),
    path('', include('message.urls'), name='message')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
