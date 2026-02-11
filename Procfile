web: gunicorn wsgi:app
release: python -c "from app import create_app; from app.models import db; app = create_app(); app.app_context().push(); db.create_all()"
