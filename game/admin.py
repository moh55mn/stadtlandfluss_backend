# game/admin.py
from django.contrib import admin
from .models import Category, Term, Round, RoundParticipant, Submission, UnknownTerm, Vote, Highscore, WaitingPlayer

admin.site.register(Category)
admin.site.register(Term)
admin.site.register(Round)
admin.site.register(RoundParticipant)
admin.site.register(Submission)
admin.site.register(UnknownTerm)
admin.site.register(Vote)
admin.site.register(Highscore)
admin.site.register(WaitingPlayer)
