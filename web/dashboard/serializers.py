from rest_framework import serializers

from dashboard.models import Plan, PlanRecord, CaseRecord, OaUser, Problem
from django.contrib.auth.models import User


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = '__all__'
        # fields = ['url', 'username', 'email', 'groups'


class PlanRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanRecord
        fields = '__all__'


class CaseRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseRecord
        fields = '__all__'


class ProblemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Problem
        fields = '__all__'


class OaUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = OaUser
        fields = ['username', 'password', 'email']
        # fields = '__all__'
