import git
import os

def sync_db():
    repo = git.Repo('.')
    repo.git.add('data/arbeitsmedizin.db')
    repo.git.commit('-m', 'Automatisches Datenbank-Backup')
    origin = repo.remote(name='origin')
    origin.push()
