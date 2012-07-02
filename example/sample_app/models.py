from django.db import models

class Person(models.Model):
    name = models.CharField(max_length=10, default="asdf")

class First(models.Model):
    first_field = models.CharField(max_length=10)
    second_field = models.CharField(max_length=10)

class Second(models.Model):
    third_field = models.CharField(max_length=10)
