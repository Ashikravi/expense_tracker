from django.urls import path

from . import views

urlpatterns = [
    path("", views.expense_list, name="expense_list"),
    path("<int:pk>/edit/", views.expense_edit, name="expense_edit"),
    path("<int:pk>/delete/", views.expense_delete, name="expense_delete"),
]
