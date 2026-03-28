from django.db import models

class AdminUser(models.Model):
    name = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Team(models.Model):
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=100, default='1234', blank=True)
    score = models.IntegerField(default=0)
    max_members = models.IntegerField(default=5)

    def __str__(self):
        return self.name

class Student(models.Model):
    name = models.CharField(max_length=100)
    section = models.CharField(max_length=50)
    register_no = models.CharField(max_length=50)
    team = models.ForeignKey(Team, related_name='students', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.team.name})"

class Question(models.Model):
    question = models.TextField()
    option1 = models.CharField(max_length=200)
    option2 = models.CharField(max_length=200)
    option3 = models.CharField(max_length=200)
    option4 = models.CharField(max_length=200)
    correct_answer = models.CharField(max_length=200)

    def __str__(self):
        return self.question[:50]
