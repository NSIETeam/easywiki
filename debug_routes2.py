from fastapi import FastAPI
from fastapi.routing import APIRoute, Mount

app = FastAPI()
from orgmind.easywiki.routes import router as easywiki_router
app.include_router(easywiki_router)

print("=== All routes ===")
for i, r in enumerate(app.routes):
    print(f"[{i}] Type: {type(r).__name__}")
    if hasattr(r, 'path'):
        methods = ','.join(r.methods) if hasattr(r, 'methods') else 'N/A'
        print(f"    path={r.path}, methods={methods}")
    if hasattr(r, 'routes'):
        print(f"    Nested routes: {len(r.routes)}")
        for j, sr in enumerate(r.routes):
            if hasattr(sr, 'path'):
                methods = ','.join(sr.methods) if hasattr(sr, 'methods') else 'N/A'
                print(f"    [{j}] path={sr.path}, methods={methods}")
    print()

# Also check openapi
print("=== openapi paths ===")
openapi = app.openapi()
for path, methods in openapi.get("paths", {}).items():
    if "easywiki" in path.lower():
        print(f"  {path}: {list(methods.keys())}")
