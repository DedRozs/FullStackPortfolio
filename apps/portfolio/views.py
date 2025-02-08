from django.shortcuts import render, get_object_or_404, redirect
from .models import Project, BlogPost
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings

def home_view(request):
    projects = Project.objects.all()[:3]  # Show latest 3 projects
    blogs = BlogPost.objects.all()[:3]  # Show latest 3 blog posts
    return render(request, "portfolio/home.html", {"projects": projects, "blogs": blogs})

def about_view(request):
    return render(request, "portfolio/about.html")  

def projects_view(request):
    projects = Project.objects.all()
    return render(request, "portfolio/projects.html", {"projects": projects})

def project_detail_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    return render(request, "portfolio/project_detail.html", {"project": project})

def blog_view(request):
    blogs = BlogPost.objects.all()
    return render(request, "portfolio/blog.html", {"blogs": blogs})

def blog_detail_view(request, blog_id):
    blog = get_object_or_404(BlogPost, id=blog_id)
    return render(request, "portfolio/blog_detail.html", {"blog": blog})

def contact_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        if name and email and message:
            send_mail(
                subject=f"New Contact from {name}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
            )
            messages.success(request, "Your message has been sent!")
            return redirect("contact")
        else:
            messages.error(request, "All fields are required.")

    return render(request, "portfolio/contact.html")
