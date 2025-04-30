from rest_framework.permissions import SAFE_METHODS, BasePermission


class AdminOrReadAccess(BasePermission):
    """
    Access control allowing read operations for everyone,
    but restricting write operations to admin-level users only.
    """
    def has_permission(self, request, view):
        # Grant access for read-only requests
        if request.method in SAFE_METHODS:
            return True
        # Only permit write operations to administrative users
        return request.user and request.user.is_authenticated and request.user.is_staff


class SupervisorOnlyAccess(BasePermission):
    """
    Access control restricting all operations to admin-level users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 1  # ADMIN role


class CoordinatorOrHigherAccess(BasePermission):
    """
    Access control limiting operations to project managers and admins.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in [1, 2]  # ADMIN or PROJECT_MANAGER
        )


class WorkflowAccessControl(BasePermission):
    """
    Access rules for projects:
    * Admins have complete administrative control
    * Project Managers can view but not modify
    * Developers can view certain projects
    """
    def has_permission(self, request, view):
        # All authenticated users can view projects
        if request.method in SAFE_METHODS:
            return True
        
        # Only admins can create/update/delete projects
        return request.user.role == 1


class ActivityUpdateControl(BasePermission):
    """
    Permission framework for task modifications:
    * Admins have universal access
    * Project Managers can manage all tasks
    * Developers can only update status of their assigned tasks
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Admins have complete control
        if user.role == 1:
            return True
            
        # Project Managers can manage all tasks
        if user.role == 2:
            return True
            
        # Developers can only update their assigned tasks, limited to status changes
        if user.role == 3 and obj.assigned_to == user:
            # For developers, only allow partial updates to status field
            if request.method == 'PATCH':
                # Restrict to status field only
                if set(request.data.keys()).issubset({'status'}):
                    return True
            return False
            
        return False
