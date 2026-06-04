import os
from git import Repo

def sync_db():
    token = os.environ.get("GIT_TOKEN")
    repo = Repo('.')
    # Nutze das Token für den Remote-Zugriff
    repo.git.add('data/arbeitsmedizin.db')
    repo.git.commit('-m', 'Auto-Sync via App')
    # Hier setzen wir die URL mit Token zusammen
    origin = repo.remote(name='origin')
    origin.set_url(f"https://{token}@github.com/lebastiansiehl-collab/company.git")
    origin.push()
