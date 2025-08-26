# game/admin.py
from django.contrib import admin
from .models import Category, Term, Highscore

admin.site.register(Category)
admin.site.register(Term)
admin.site.register(Highscore)
#
