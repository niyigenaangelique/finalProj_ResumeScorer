from hr_main import app
from starlette.routing import Route, Mount

print("Registered Routes (HR Portal):")
for route in app.routes:
    if isinstance(route, Route):
        print(f"ROUTE: {route.path} [{route.methods}]")
    elif isinstance(route, Mount):
        print(f"MOUNT: {route.path}")
