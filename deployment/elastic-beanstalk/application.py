"""Elastic Beanstalk entrypoint for the MetaKB FastAPI application."""

from metakb.main import app

# Elastic Beanstalk's Python platform conventionally looks for
# an object named `application`.
application = app
