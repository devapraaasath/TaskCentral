from django.urls import path
from rest_framework_simplejwt import views as jwt_views

from .views import (
    AccountRegistrationView, 
    AccountLoginView, 
    AccountListView, 
    ActivityListCreateView, 
    ActivityDetailView,
    WorkflowListCreateView, 
    WorkflowDetailView,
    AccountPermissionsView, 
    ActivityAssignmentView
)


urlpatterns = [
    # Authentication endpoints
    path('token/obtain/', jwt_views.TokenObtainPairView.as_view(), name='token_create'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', AccountRegistrationView.as_view(), name='register'),
    path('login/', AccountLoginView.as_view(), name='login'),
    
    # User management endpoints
    path('users/', AccountListView.as_view(), name='users'),
    path('users/<str:email>/role/', AccountPermissionsView.as_view(), name='user_role_update'),

    # Project endpoints
    path('projects/', WorkflowListCreateView.as_view(), name='project_list_create'),
    path('projects/<int:pk>/', WorkflowDetailView.as_view(), name='project_detail'),

    # Task endpoints - using the original URL names to match tests
    path('tasks/', ActivityListCreateView.as_view(), name='task_Create'),
    path('tasks/<int:pk>/', ActivityDetailView.as_view(), name='task_update'),
    path('tasks/<int:pk>/assign/', ActivityAssignmentView.as_view(), name='task_assignment')
]
