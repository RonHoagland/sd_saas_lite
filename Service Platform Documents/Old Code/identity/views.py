from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Min, Prefetch, Value, CharField
from django.db.models.functions import Concat
from .models import Role, UserRole

from core.utils import apply_sorting

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def user_list_view(request):
    users = User.objects.all().prefetch_related('user_roles__role').select_related('profile')
    
    # Annotation for sorting by role (picks the first role name alphabetically)
    # Annotation for full name sorting
    users = users.annotate(
        primary_role=Min('user_roles__role__name'),
        full_name=Concat('first_name', Value(' '), 'last_name', output_field=CharField())
    )
    
    # Sorting
    users, sort_field, sort_dir = apply_sorting(
        users, 
        request, 
        allowed_fields=['username', 'email', 'is_active', 'primary_role', 'full_name', 'profile__position'], 
        default_sort='username', 
        default_dir='asc'
    )
    
    return render(request, "identity/user_list.html", {
        "users": users,
        "current_sort": sort_field,
        "current_dir": sort_dir
    })



@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def role_list_view(request):
    roles = Role.objects.all()
    return render(request, "identity/role_list.html", {"roles": roles})

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def role_create_view(request):
    # STRICT ROLE MANAGEMENT: Disable Creation
    return HttpResponseForbidden("Role creation is disabled in this version. Only system roles are allowed.")


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def role_delete_confirm_view(request, user_id, role_id):
    """
    Confirmation page view for role deletion.
    GET: Show confirmation page.
    POST: Delete role and redirect.
    """
    try:
        user_obj = get_object_or_404(User, pk=user_id)
        role_obj = get_object_or_404(Role, pk=role_id)
        
        if request.method == "POST":
            UserRole.objects.filter(user=user_obj, role=role_obj).delete()
            messages.success(request, f"Role '{role_obj.name}' removed from {user_obj.username}.")
            return redirect('user_detail', pk=user_id)
            
        return render(request, "identity/role_delete_confirm.html", {
            "target_user": user_obj,
            "role": role_obj
        })
        
    except Exception as e:
        messages.error(request, f"Error preparing removal: {e}")
        return redirect('user_detail', pk=user_id)

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def role_delete_view(request, pk):
    # STRICT ROLE MANAGEMENT: Disable Deletion
    return HttpResponseForbidden("Role deletion is disabled in this version.")


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def user_delete_view(request, pk):
    """
    Delete a user with smart audit checking.
    
    Allows deletion if user only has login records (Session).
    Blocks deletion if user has transaction history or other protected records.
    """
    from django.db.models import ProtectedError
    from audit.models import UserTransaction
    
    try:
        user_obj = get_object_or_404(User, pk=pk)
        
        # Self-Check
        if user_obj.id == request.user.id:
            messages.error(request, "You cannot delete your own account.")
            return redirect('user_list')
        
        # Smart Audit Check: Block if user has transaction history
        has_transactions = UserTransaction.objects.filter(user=user_obj).exists()
        
        if has_transactions:
            messages.error(
                request, 
                f"Cannot delete user '{user_obj.username}' because they have transaction history (created or deleted records). "
                "Users with action history must be preserved for audit integrity."
            )
            return redirect('user_list')
            
        if request.method == "POST":
            try:
                username = user_obj.username
                
                # --- AUDIT LOG (Manual, since User is not a BaseModel) ---
                try:
                    import uuid
                    from audit.models import UserTransaction, Session
                    
                    session = Session.objects.filter(
                        user=request.user, ended_at__isnull=True
                    ).order_by('-started_at').first()
                    
                    if session:
                        # Convert integer PK to a deterministic UUID for entity_id
                        entity_uuid = uuid.uuid5(uuid.NAMESPACE_OID, f"auth.User:{user_obj.pk}")
                        
                        UserTransaction.objects.create(
                            session=session,
                            user=request.user,
                            event_type='delete',
                            entity_type='User',
                            entity_id=entity_uuid,
                            summary=f"Deleted user '{username}' (ID: {user_obj.pk})"
                        )
                except Exception:
                    pass  # Don't block deletion if audit logging fails
                
                # Sessions will CASCADE delete automatically
                # Other protected relationships will still raise ProtectedError
                user_obj.delete()
                messages.success(request, f"User '{username}' deleted successfully.")
                return redirect('user_list')
            except ProtectedError as e:
                # Catch any other protected relationships (e.g., created_by fields)
                messages.error(
                    request, 
                    f"Cannot delete user '{user_obj.username}' because they are linked to other records. "
                    "This user may have created files, roles, or other entities that reference them."
                )
                return redirect('user_list')
            except Exception as e:
                messages.error(request, f"Error deleting user: {e}")
                return redirect('user_list')
            
        return render(request, "identity/user_delete_confirm.html", {"target_user": user_obj})
        
    except Exception as e:
        messages.error(request, f"Error preparing user deletion: {e}")
        return redirect('user_list')

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def user_create_view(request):
    from .forms import UserForm, UserProfileForm
    from .models import UserProfile
    
    if request.method == "POST":
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            try:
                # Create user first (password handled by form.save())
                user = user_form.save(commit=False)
                user.save()
                
                # Check if profile already exists (via signal) or create new
                if hasattr(user, 'profile'):
                    profile = user.profile
                else:
                    profile = UserProfile(user=user)
                
                # Update profile fields
                profile_data = profile_form.cleaned_data
                for key, value in profile_data.items():
                    setattr(profile, key, value)
                
                profile.created_by = request.user
                profile.updated_by = request.user
                profile.save()
                
                # Save Role
                role = user_form.cleaned_data.get('role')
                if role:
                    UserRole.objects.create(
                         user=user, 
                         role=role,
                         created_by=request.user,
                         updated_by=request.user
                    )

                # --- AUDIT LOG (Manual, since User is not a BaseModel) ---
                try:
                    import uuid
                    from audit.models import UserTransaction, Session
                    
                    session = Session.objects.filter(
                        user=request.user, ended_at__isnull=True
                    ).order_by('-started_at').first()
                    
                    if session:
                        entity_uuid = uuid.uuid5(uuid.NAMESPACE_OID, f"auth.User:{user.pk}")
                        
                        UserTransaction.objects.create(
                            session=session,
                            user=request.user,
                            event_type='create',
                            entity_type='User',
                            entity_id=entity_uuid,
                            summary=f"Created user '{user.username}' (ID: {user.pk})"
                        )
                except Exception:
                    pass  # Don't block creation if audit logging fails

                messages.success(request, f"User '{user.username}' created successfully.")
                return redirect('user_detail', pk=user.pk)
            except Exception as e:
                messages.error(request, f"Error creating user: {e}")
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()
        
    return render(request, "identity/user_form.html", {
        "user_form": user_form,
        "profile_form": profile_form,
        "is_edit": False
    })


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def user_edit_view(request, pk):
    from .forms import UserForm, UserProfileForm
    from .models import UserProfile
    
    user_obj = get_object_or_404(User, pk=pk)
    
    # Ensure profile exists
    if not hasattr(user_obj, 'profile'):
        UserProfile.objects.create(user=user_obj, created_by=request.user, updated_by=request.user)
        user_obj.refresh_from_db()
        
    if request.method == "POST":
        user_form = UserForm(request.POST, instance=user_obj)
        profile_form = UserProfileForm(request.POST, instance=user_obj.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            try:
                user_form.save()
                
                profile = profile_form.save(commit=False)
                profile.updated_by = request.user
                profile.save()
                
                # Save Role
                role = user_form.cleaned_data.get('role')
                if role:
                    # Remove existing roles (Single Role Policy)
                    UserRole.objects.filter(user=user_obj).delete()
                    # Assign new role
                    UserRole.objects.create(
                         user=user_obj, 
                         role=role,
                         created_by=request.user,
                         updated_by=request.user
                    )
                
                messages.success(request, f"User '{user_obj.username}' updated successfully.")
                return redirect('user_detail', pk=user_obj.pk)
            except Exception as e:
                messages.error(request, f"Error updating user: {e}")
    else:
        user_form = UserForm(instance=user_obj)
        profile_form = UserProfileForm(instance=user_obj.profile)
        
    return render(request, "identity/user_form.html", {
        "form": user_form, # logic in template uses form.instance
        "user_form": user_form,
        "profile_form": profile_form,
        "is_edit": True
    })

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def user_detail_view(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    
    if request.method == "POST":
        action = request.POST.get('action')
        
        if action == 'toggle_active':
            try:
                user_obj.is_active = not user_obj.is_active
                user_obj.save()
                status_msg = "activated" if user_obj.is_active else "deactivated"
                messages.success(request, f"User {user_obj.username} {status_msg}.")
            except ValidationError as e:
                messages.error(request, f"Cannot change status: {e.message}")
            except Exception as e:
                messages.error(request, f"Error updating status: {e}")
        
        return redirect('user_detail', pk=pk)
            
    return render(request, "identity/user_detail.html", {
        "user_obj": user_obj
    })

@login_required
def my_profile_view(request):
    """
    Self-service profile editing for the logged-in user.
    """
    from .forms import UserForm, UserProfileForm
    from .models import UserProfile
    
    user_obj = request.user
    
    # Ensure profile exists
    if not hasattr(user_obj, 'profile'):
        UserProfile.objects.create(user=user_obj, created_by=user_obj, updated_by=user_obj)
        user_obj.refresh_from_db()

    if request.method == "POST":
        # Using UserForm but we might want to restrict fields (e.g. username) depending on policy
        # For now, allowing full edit is fine for small teams.
        user_form = UserForm(request.POST, instance=user_obj)
        profile_form = UserProfileForm(request.POST, instance=user_obj.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            try:
                user_form.save()
                
                profile = profile_form.save(commit=False)
                profile.updated_by = request.user
                profile.save()
                
                messages.success(request, "Your profile has been updated.")
                return redirect('my_profile')
            except Exception as e:
                messages.error(request, f"Error updating profile: {e}")
    else:
        user_form = UserForm(instance=user_obj)
        profile_form = UserProfileForm(instance=user_obj.profile)
    
    # Hide role field for self-service if not admin? 
    # Actually UserForm includes role field which we added. A regular user should not change their own role.
    # We should disable it in the form or template.
    if not request.user.is_staff and not request.user.is_superuser:
        if 'role' in user_form.fields:
            user_form.fields['role'].disabled = True

    return render(request, "identity/my_profile.html", {
        "user_form": user_form,
        "profile_form": profile_form
    })

@login_required
def user_export_view(request):
    """
    Export list of users to CSV.
    """
    from core.utils import generate_csv_response
    
    # Check permissions (Admin only? Or Workers too?)
    # Usually export is sensitive. Let's restrict to Staff/Superuser for now.
    if not request.user.is_staff and not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("You do not have permission to export user data.")
    
    queryset = User.objects.select_related('profile').all().order_by('username')
    
    # Define mapping: (Header, Attribute Path)
    field_mapping = [
        ('Username', 'username'),
        ('Email', 'email'),
        ('First Name', 'first_name'),
        ('Last Name', 'last_name'),
        ('Active', 'is_active'),
        ('Position', 'profile.position'),
        ('Phone', 'profile.phone_number'),
        ('Date Joined', 'date_joined'),
        ('Last Login', 'last_login'),
    ]
    
    return generate_csv_response(queryset, "users_export.csv", field_mapping)
