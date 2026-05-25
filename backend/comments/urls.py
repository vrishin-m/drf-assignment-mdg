from rest_framework.routers import DefaultRouter
from .views import CommentViewSet


router = DefaultRouter()

router.register(
    r"studios/(?P<slug>[^/.]+)/projects/(?P<project_id>[^/.]+)/tasks/(?P<task_id>[^/.]+)/comments",
    CommentViewSet,
    basename="comment"
)

urlpatterns = router.urls