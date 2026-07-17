from fastapi import FastAPI
from fastapi.routing import APIRoute

app = FastAPI()
from orgmind.easywiki.routes import router as easywiki_router
app.include_router(easywiki_router)

routes = [r for r in app.routes]
print("Total routes:", len(routes))
for r in routes:
    name = type(r).__name__
    if hasattr(r, 'path'):
        if 'easywiki' in r.path:
            print(f"  {r.path} [{','.join(r.methods)}]")
    elif hasattr(r, 'routes'):
        print(f"  Mount: {r.path if hasattr(r,'path') else 'nested'}")
        for sr in r.routes:
            if hasattr(sr, 'path'):
                print(f"    {sr.path} [{','.join(sr.methods) if hasattr(sr,'methods') else ''}]")
