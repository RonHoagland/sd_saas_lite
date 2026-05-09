from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db import DatabaseError

class SchemaSafeSessionBackend(ModelBackend):
    """
    Session user rehydration backend that avoids full-row SELECT on users_user.
    This is a temporary guard for schema-drifted environments.
    """

    def get_user(self, user_id):
        user_model = get_user_model()
        try:
            user = (
                user_model.all_objects.only(
                    "id",
                    "email",
                    "password",
                    "tenant_id",
                    "is_active",
                    "is_staff",
                )
                .filter(pk=user_id)
                .first()
            )
            return user
        except DatabaseError:
            return None
