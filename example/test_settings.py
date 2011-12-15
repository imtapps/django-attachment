from settings import *

SOUTH_TESTS_MIGRATE = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test_db',
    }
}


PROJECT_APPS = ('attachments', )

try:
    import django_jenkins

    INSTALLED_APPS = INSTALLED_APPS + ('django_jenkins',)
    JENKINS_TASKS = (
        'django_jenkins.tasks.django_tests',
        'django_jenkins.tasks.run_pylint',
        'django_jenkins.tasks.run_pep8',
        'django_jenkins.tasks.run_pyflakes',
        'django_jenkins.tasks.with_coverage',
    )

except ImportError:
    pass