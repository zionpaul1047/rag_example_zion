from app.main import app

for route in app.routes:
    path = getattr(route, "path", "")
    methods = getattr(route, "methods", "")

    if "rag-documents" in path:
        print(methods, path)