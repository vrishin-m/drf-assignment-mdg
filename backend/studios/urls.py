from rest_framework.routers import DefaultRouter
from .views import StudioViewSet

router = DefaultRouter()
router.register(r'studios', StudioViewSet, basename='studio')

urlpatterns = router.urls
