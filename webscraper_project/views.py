from django.shortcuts import render, redirect



def render_home(request):
    return redirect("/tours/")

def serve_react(request):
    return render(request, 'index.html') #React's build file

