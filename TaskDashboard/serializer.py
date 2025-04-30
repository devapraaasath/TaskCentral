from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login

from .models import User, Task, Project


class UserSignupSerializer(serializers.ModelSerializer):
    """
    Handles new user registration with secure password management.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')  # Extract password separately
        user = User(**validated_data)
        user.set_password(password)  # Apply password hashing
        user.save()
        return user


class UserAuthenticationSerializer(serializers.Serializer):
    """
    Handles user authentication and JWT token generation.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)

    def create(self, validated_data):
        # Required by serializer interface but not used
        pass

    def update(self, instance, validated_data):
        # Required by serializer interface but not used
        pass

    def validate(self, data):
        email = data['email']
        password = data['password']
        user = authenticate(email=email, password=password)

        if user is None:
            raise serializers.ValidationError("Authentication failed: invalid credentials")

        try:
            refresh = RefreshToken.for_user(user)
            refresh_token = str(refresh)
            access_token = str(refresh.access_token)
            update_last_login(None, user)

            validation = {
                'access': access_token,
                'refresh': refresh_token,
                'email': user.email,
                'role': user.role,
            }

            return validation
        except Exception as e:
            raise serializers.ValidationError(f"Authentication error: {e}")


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Prepares user profile data for API responses.
    """
    role_display = serializers.SerializerMethodField(read_only=True)
    email = serializers.EmailField(read_only=True)
    role = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = User
        fields = (
            'email',
            'role',
            'role_display'
        )
        read_only_fields = ['email', 'role', 'role_display']
    
    def get_role_display(self, obj):
        return obj.get_role_display()


class UserPermissionsSerializer(serializers.ModelSerializer):
    """
    Manages user role and activation status updates.
    """
    class Meta:
        model = User
        fields = ['role', 'is_active']
        
    def validate_role(self, value):
        if value not in [User.ADMIN, User.PROJECT_MANAGER, User.DEVELOPER]:
            raise serializers.ValidationError("Invalid role selected")
        return value


class WorkflowSerializer(serializers.ModelSerializer):
    """
    Handles project data serialization and validation.
    """
    creator_email = serializers.EmailField(source='created_by.email', read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'description',
            'created_by',
            'creator_email',
            'start_date',
            'end_date',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'creator_email', 'created_by']


class ActivitySerializer(serializers.ModelSerializer):
    """
    Handles task data serialization with relationship management.
    """
    workflow_name = serializers.CharField(source='project.title', read_only=True)
    developer_email = serializers.EmailField(source='assigned_to.email', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'project',
            'workflow_name',
            'assigned_to',
            'developer_email',
            'status',
            'priority',
            'start_date',
            'end_date',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'workflow_name', 'developer_email']


class ActivityAssignmentSerializer(serializers.ModelSerializer):
    """
    Manages task assignment operations with input validation.
    """
    developer_email = serializers.EmailField(source='assigned_to.email', read_only=True)
    project_name = serializers.CharField(source='project.title', read_only=True)
    developer_fullname = serializers.SerializerMethodField(read_only=True)
    developer_email_assign = serializers.EmailField(write_only=True, required=False)
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'project',
            'project_name',
            'assigned_to',
            'developer_email',
            'developer_fullname',
            'developer_email_assign',
            'status',
            'priority'
        ]
        read_only_fields = [
            'id', 
            'title', 
            'project', 
            'project_name', 
            'developer_email', 
            'developer_fullname'
        ]
    
    def get_developer_fullname(self, obj):
        """Returns the full name of the assigned developer."""
        if obj.assigned_to:
            return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}"
        return None
    
    def validate(self, data):
        # Process developer_email_assign if provided
        if 'developer_email_assign' in data:
            email = data.pop('developer_email_assign')
            try:
                user = User.objects.get(email=email)
                if user.role != User.DEVELOPER:
                    raise serializers.ValidationError({"developer_email_assign": "This user must have a developer role"})
                data['assigned_to'] = user
            except User.DoesNotExist:
                raise serializers.ValidationError({"developer_email_assign": f"No user found with email {email}"})
        
        return data