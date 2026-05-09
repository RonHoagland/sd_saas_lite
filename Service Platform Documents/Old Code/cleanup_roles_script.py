from identity.models import Role

print("Starting role cleanup...")

# Define system keys
system_keys = ['administrator', 'worker', 'read_only']

# 1. Delete roles that are NOT in the allowed system keys list
# Exclude system roles
candidates = Role.objects.exclude(key__in=system_keys)

deleted_count = 0
for role in candidates:
    # Check assignments
    if role.assigned_users.exists():
        print(f"SKIPPING: Role '{role.name}' ({role.key}) has assigned users.")
    else:
        print(f"DELETING: Role '{role.name}' ({role.key})")
        role.delete()
        deleted_count += 1
        
print(f"Cleanup complete. Deleted {deleted_count} unused roles.")
