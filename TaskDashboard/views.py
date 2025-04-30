from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import User, Project, Task
from .serializer import (
    UserSignupSerializer,
    UserAuthenticationSerializer,
    UserProfileSerializer, 
    UserPermissionsSerializer, 
    ActivitySerializer, 
    WorkflowSerializer,
    ActivityAssignmentSerializer
)
from .permission import (
    AdminOrReadAccess, 
    SupervisorOnlyAccess, 
    CoordinatorOrHigherAccess, 
    WorkflowAccessControl, 
    ActivityUpdateControl
)


class AccountRegistrationView(APIView):
    """
    Account Registration Endpoint
    
    Allows new users to create an account in the system.
    
    Request body fields:
    * first_name - User's first name
    * last_name - User's last name
    * email - Email address for authentication
    * password - Secure password for the account
    """
    serializer_class = UserSignupSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        """
        Create new user account
        
        Processes registration data and creates a new account.
        
        Request format:
        {
            "first_name": "string",
            "last_name": "string",
            "email": "user@example.com",
            "password": "string"
        }
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'success': True,
            'message': 'Registration completed successfully',
            'user': serializer.data
        }, status=status.HTTP_201_CREATED)
    

class AccountLoginView(APIView):
    """
    Account Login Endpoint
    
    Authenticates users and provides JWT tokens for accessing protected endpoints.
    
    Request body fields:
    * email - Registered email address
    * password - Account password
    """
    serializer_class = UserAuthenticationSerializer
    permission_classes = (AllowAny,)
    
    def post(self, request):
        """
        Authenticate user
        
        Verifies credentials and returns authentication tokens.
        
        Request format:
        {
            "email": "user@example.com",
            "password": "string"
        }
        
        Tokens should be included in API requests as:
        Authorization: JWT <access_token>
        """
        serializer = self.serializer_class(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        
        if valid:
            status_code = status.HTTP_200_OK
            response_data = {
                'success': True,
                'status_code': status_code,
                'message': 'Authentication successful',
                'access': serializer.data['access'],
                'refresh': serializer.data['refresh'],
                'authenticatedUser': {
                    'email': serializer.data['email'],
                    'role': serializer.data['role']
                }
            }
            return Response(response_data, status=status_code)


class AccountListView(APIView):
    """
    Account Directory Endpoint
    
    Provides a list of all user accounts in the system.
    Restricted to admin accounts (role=1).
    Requires JWT authentication.
    
    No request body needed - authentication via token.
    
    Authentication:
    1. Obtain token from /login/ endpoint
    2. Include header: Authorization: JWT your_token_here
    """
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """
        Retrieve all accounts
        
        Returns account listing for authenticated admins.
        No request body required.
        """
        user = request.user

        if user.role != User.ADMIN:
            return Response({
                'success': False,
                'status_code': status.HTTP_403_FORBIDDEN,
                'message': 'Access denied: admin privileges required'
            }, status=status.HTTP_403_FORBIDDEN)
        
        users = User.objects.all()
        serializer = self.serializer_class(users, many=True)
        response = {
            'success': True,
            'status_code': status.HTTP_200_OK,
            'message': 'Account listing retrieved successfully',
            'users': serializer.data
        }
        return Response(response, status=status.HTTP_200_OK)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="project",
            description="Filter by project ID",
            required=False,
            type=OpenApiTypes.INT
        ),
        OpenApiParameter(
            name="status",
            description="Filter by task status (e.g., 'To-Do', 'In Progress', 'Completed')",
            required=False,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="priority",
            description="Filter by task priority (e.g., 'Low', 'Medium', 'High')",
            required=False,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="due_date",
            description="Filter by due date (format: YYYY-MM-DD)",
            required=False,
            type=OpenApiTypes.DATE
        ),
        OpenApiParameter(
            name="page",
            description="Page number for pagination",
            required=False,
            type=OpenApiTypes.INT
        ),
    ]
)
class ActivityListCreateView(generics.ListCreateAPIView):
    """
    Activity Management Endpoint
    
    - List: Returns activities filtered by user role
      * Filter by project: ?project=<id>
      * Filter by status: ?status=<status>
      * Filter by priority: ?priority=<priority>
    """
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.all().order_by('-created_at')
    
    def get_queryset(self):
        """Filter activities based on user role."""
        queryset = super().get_queryset()
        user = self.request.user
        
        # Apply filters if provided in query params
        project_id = self.request.query_params.get('project')
        status = self.request.query_params.get('status')
        priority = self.request.query_params.get('priority')
        due_date = self.request.query_params.get('due_date')
        
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if status:
            queryset = queryset.filter(status=status)
        if priority:
            queryset = queryset.filter(priority=priority)
        if due_date:
            queryset = queryset.filter(end_date=due_date)
        
        # Role-based filtering
        if user.role == User.ADMIN:
            # Admins can see all activities
            return queryset
        elif user.role == User.PROJECT_MANAGER:
            # Project Managers can see all activities
            return queryset
        else:  # DEVELOPER
            # Developers can only see activities assigned to them
            return queryset.filter(assigned_to=user)
    
    def perform_create(self, serializer):
        """Save the activity with validation."""
        # Validate that the user has permission to create an activity for this project
        project_id = self.request.data.get('project')
        
        if project_id:
            try:
                project = Project.objects.get(id=project_id)
                # Allow creation to proceed
                serializer.save()
            except Project.DoesNotExist:
                raise PermissionDenied("The specified project does not exist")
        else:
            # If no project specified, just create the task
            serializer.save()


class ActivityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Activity Detail Endpoint
    
    - Retrieve: Returns activity details (if user has permission)
    - Update: 
        - Admins can update anything
        - Project Managers can update all activities
        - Developers can only update status of their assigned activities
    - Delete: Only admins and project managers can delete activities
    """
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated, ActivityUpdateControl]
    
    def get_queryset(self):
        """Filter activities based on user role."""
        user = self.request.user
        
        if user.role == User.ADMIN:
            # Admins can see all activities
            return Task.objects.all()
        elif user.role == User.PROJECT_MANAGER:
            # Project Managers can see all activities
            return Task.objects.all()
        else:  # DEVELOPER
            # Developers can only see activities assigned to them
            return Task.objects.filter(assigned_to=user)
    
    def update(self, request, *args, **kwargs):
        """Update activity with appropriate role-based restrictions."""
        user = request.user
        instance = self.get_object()
        
        # Developers can only update status of their assigned tasks
        if user.role == User.DEVELOPER:
            if request.method == 'PUT':  # Full update not allowed for developers
                return Response({
                    "detail": "Method not allowed. Use PATCH to update only the status."
                }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
            
            # For PATCH, ensure they're only updating status
            if set(request.data.keys()) - {'status'}:
                return Response({
                    "detail": "You can only update the status field."
                }, status=status.HTTP_403_FORBIDDEN)
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete activity with permission check."""
        user = request.user
        
        # Only admins and project managers can delete activities
        if user.role not in [User.ADMIN, User.PROJECT_MANAGER]:
            return Response({
                "detail": "You do not have permission to delete activities."
            }, status=status.HTTP_403_FORBIDDEN)
        
        return super().destroy(request, *args, **kwargs)


# Project CRUD Views
@extend_schema(
    parameters=[
        OpenApiParameter(
            name="title",
            description="Filter by title",
            required=False,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="created_by",
            description="Filter by creator ID",
            required=False,
            type=OpenApiTypes.INT
        ),
        OpenApiParameter(
            name="start_date",
            description="Filter by start date (format: YYYY-MM-DD)",
            required=False,
            type=OpenApiTypes.DATE
        ),
        OpenApiParameter(
            name="end_date",
            description="Filter by end date (format: YYYY-MM-DD)",
            required=False,
            type=OpenApiTypes.DATE
        ),
        OpenApiParameter(
            name="page",
            description="Page number for pagination",
            required=False,
            type=OpenApiTypes.INT
        ),
    ]
)
class WorkflowListCreateView(generics.ListCreateAPIView):
    """
    Workflow Management Endpoint
    
    - List: Returns a list of all workflows (filtered by role)
      * Filter by title with ?title=<title>
      * Filter by created_by with ?created_by=<user_id>
      * Filter by start_date with ?start_date=<YYYY-MM-DD>
      * Filter by end_date with ?end_date=<YYYY-MM-DD>
    - Create: Creates a new workflow (admin only)
    
    Request body for Create:
    {
        "title": "Workflow Title",
        "description": "Workflow Description",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31"
    }
    """
    serializer_class = WorkflowSerializer
    permission_classes = [IsAuthenticated, WorkflowAccessControl]
    queryset = Project.objects.all().order_by('-created_at')
    
    def perform_create(self, serializer):
        """Save the current user as the workflow creator."""
        serializer.save(created_by=self.request.user)
    
    def get_queryset(self):
        """Filter workflows based on user role."""
        queryset = super().get_queryset()
        
        # Apply filters from query params
        title = self.request.query_params.get('title')
        created_by = self.request.query_params.get('created_by')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        # Apply filters if provided
        if title:
            queryset = queryset.filter(title__icontains=title)
        if created_by:
            queryset = queryset.filter(created_by_id=created_by)
        if start_date:
            queryset = queryset.filter(start_date=start_date)
        if end_date:
            queryset = queryset.filter(end_date=end_date)
        
        user = self.request.user
        
        # Role-based filtering
        if user.role == User.ADMIN:
            # Admins can see all workflows
            return queryset
        elif user.role == User.PROJECT_MANAGER:
            # Project Managers can see all workflows
            return queryset
        else:  # DEVELOPER
            # Developers can only see workflows where they have assigned activities
            return queryset.filter(tasks__assigned_to=user).distinct()


class WorkflowDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Workflow Detail Endpoint
    
    - Retrieve: Returns workflow details (if user has permission)
    - Update: Only admins can update workflows
    - Delete: Only admins can delete workflows
    """
    serializer_class = WorkflowSerializer
    permission_classes = [IsAuthenticated, WorkflowAccessControl]
    
    def get_queryset(self):
        """Filter workflows based on user role."""
        user = self.request.user
        
        if user.role == User.ADMIN:
            # Admins can see all workflows
            return Project.objects.all()
        elif user.role == User.PROJECT_MANAGER:
            # Project Managers can see all workflows
            return Project.objects.all()
        else:  # DEVELOPER
            # Developers can only see workflows where they have assigned activities
            return Project.objects.filter(tasks__assigned_to=user).distinct()


# User Role Management View (Admin only)
class AccountPermissionsView(generics.UpdateAPIView):
    """
    Account Permissions Management Endpoint
    
    Allows admins to update user roles and account status.
    Restricted to admin accounts (role=1).
    
    Request format:
    {
        "role": 2,  # 1=Admin, 2=Project Manager, 3=Developer
        "is_active": true
    }
    """
    queryset = User.objects.all()
    serializer_class = UserPermissionsSerializer
    permission_classes = [IsAuthenticated, SupervisorOnlyAccess]
    lookup_field = 'email'
    
    def update(self, request, *args, **kwargs):
        """Update user role with validation."""
        # Prevent users from changing their own role
        target_email = kwargs.get('email')
        if target_email == request.user.email:
            return Response({
                "detail": "You cannot modify your own role and permissions."
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Process the update
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        
        # Save the changes
        new_role = serializer.validated_data.get('role')
        is_active = serializer.validated_data.get('is_active', instance.is_active)
        
        if new_role == instance.role and is_active == instance.is_active:
            return Response({
                "detail": "No changes detected."
            }, status=status.HTTP_200_OK)
        
        # Perform the update
        serializer.save()
        
        return Response({
            "success": True,
            "message": f"User {instance.email} updated successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)


# Task Assignment View (Project Manager & Admin only)
class ActivityAssignmentView(generics.UpdateAPIView):
    """
    Activity Assignment Endpoint
    
    Allows project managers and admins to assign activities to developers.
    
    Request format using developer ID:
    {
        "assigned_to": 5,  # User ID of a developer
        "status": "In Progress",  # Optional status update
        "priority": "High"  # Optional priority update
    }
    
    OR assign by email (recommended):
    {
        "developer_email_assign": "developer@company.com",  # Email of the developer
        "status": "In Progress",  # Optional status update
        "priority": "High"  # Optional priority update
    }
    """
    queryset = Task.objects.all()
    serializer_class = ActivityAssignmentSerializer
    permission_classes = [IsAuthenticated, CoordinatorOrHigherAccess]
    
    def get_queryset(self):
        """Filter activities based on user role."""
        user = self.request.user
        
        if user.role == User.ADMIN:
            # Admins can see all activities
            return Task.objects.all()
        elif user.role == User.PROJECT_MANAGER:
            # Project Managers can see all activities
            return Task.objects.all()
        else:  # DEVELOPER
            # Developers can only see activities assigned to them
            return Task.objects.filter(assigned_to=user)
    
    def update(self, request, *args, **kwargs):
        """Assign an activity to a developer."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Validate that the user is authorized to assign this activity
        user = request.user
        if user.role not in [User.ADMIN, User.PROJECT_MANAGER]:
            return Response({
                "detail": "You do not have permission to assign activities."
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Save the assignment
        self.perform_update(serializer)
        
        # Get the assigned user's name for the response
        assigned_user = None
        if 'assigned_to' in serializer.validated_data:
            assigned_user = serializer.validated_data['assigned_to']
        elif instance.assigned_to:
            assigned_user = instance.assigned_to
            
        # Format the response
        response_data = {
            "success": True,
            "message": "Activity assignment successful",
            "activity": {
                "id": instance.id,
                "title": instance.title,
                "status": instance.status,
                "priority": instance.priority,
            }
        }
        
        if assigned_user:
            response_data["activity"]["assigned_to"] = {
                "email": assigned_user.email,
                "name": f"{assigned_user.first_name} {assigned_user.last_name}"
            }
            
        return Response(response_data, status=status.HTTP_200_OK)
