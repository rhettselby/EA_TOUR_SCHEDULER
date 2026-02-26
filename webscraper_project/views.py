from django.shortcuts import render, redirect



def render_home(request):
    return redirect("/tours/")

