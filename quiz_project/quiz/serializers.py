from rest_framework import serializers
from .models import Team, Student, Question

class TeamSerializer(serializers.ModelSerializer):
    members_count = serializers.SerializerMethodField()
    students_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'score', 'max_members', 'members_count', 'students_list']

    def get_members_count(self, obj):
        return obj.students.count()

    def get_students_list(self, obj):
        return [{"name": s.name, "section": s.section, "register_no": s.register_no} for s in obj.students.all()]

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'
