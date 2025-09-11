# accounts/urls_students.py
from django.urls import path
from .views_students import (
    TeacherStudentListView, 
    StudentDetailByIdView, 
    StudentStatisticsView
)

urlpatterns = [
    # Student management endpoints for teachers
    path('teacher/students/', TeacherStudentListView.as_view(), name='teacher-student-list'),
    path('teacher/students/<str:student_id>/', StudentDetailByIdView.as_view(), name='teacher-student-detail'),
    path('teacher/students-statistics/', StudentStatisticsView.as_view(), name='teacher-student-statistics'),
]
