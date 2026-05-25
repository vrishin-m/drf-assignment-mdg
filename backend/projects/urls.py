from django.urls import path

from .views import (
    AttachmentDeleteView,
    AttachmentListCreateView,
    ProjectDetailView,
    ProjectListCreateView,
    ProjectStatsView,
    TagDetailView,
    TagListCreateView,
    TaskDetailView,
    TaskListCreateView,
    TaskTransitionView,
    TaskVersionDetailView,
    TaskVersionListView,
)


urlpatterns = [
    path("studios/<slug:slug>/projects/", ProjectListCreateView.as_view(), name="project-list"),
    path("studios/<slug:slug>/projects/<uuid:id>/", ProjectDetailView.as_view(), name="project-detail"),
    path("studios/<slug:slug>/projects/<uuid:id>/stats/", ProjectStatsView.as_view(), name="project-stats"),
    path("studios/<slug:slug>/projects/<uuid:id>/tasks/", TaskListCreateView.as_view(), name="task-list"),
    path("studios/<slug:slug>/projects/<uuid:id>/tasks/<uuid:task_id>/", TaskDetailView.as_view(), name="task-detail"),
    path("studios/<slug:slug>/projects/<uuid:id>/tasks/<uuid:task_id>/transition/", TaskTransitionView.as_view(), name="task-transition"),
    path("studios/<slug:slug>/projects/<uuid:id>/tasks/<uuid:task_id>/versions/", TaskVersionListView.as_view(), name="task-version-list"),
    path("studios/<slug:slug>/projects/<uuid:id>/tasks/<uuid:task_id>/versions/<int:version_number>/", TaskVersionDetailView.as_view(), name="task-version-detail"),
    path("studios/<slug:slug>/projects/<uuid:id>/tasks/<uuid:task_id>/attachments/", AttachmentListCreateView.as_view(), name="attachment-list"),
    path("studios/<slug:slug>/projects/<uuid:id>/tasks/<uuid:task_id>/attachments/<uuid:att_id>/", AttachmentDeleteView.as_view(), name="attachment-detail"),
    path("studios/<slug:slug>/tags/", TagListCreateView.as_view(), name="tag-list"),
    path("studios/<slug:slug>/tags/<uuid:id>/", TagDetailView.as_view(), name="tag-detail"),
]
