from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webscraper_project.settings')

app = Celery('tours',
             broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/0',
             include=['tours.tasks'])

# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
)



if __name__ == '__main__':
    app.start()