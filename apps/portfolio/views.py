from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib import messages

def home_view(request):
    projects = [
        {
            "title": "E-Commerce Web App",
            "description": "A high-performance e-commerce platform with a modern UI.",
            "image": "images/project1.jpg",
            "url": "#"
        },
        {
            "title": "AI Chatbot",
            "description": "Built an intelligent chatbot using AI and NLP.",
            "image": "images/project2.jpg",
            "url": "#"
        },
        {
            "title": "Portfolio Website",
            "description": "Designed a sleek, responsive personal portfolio.",
            "image": "images/project3.jpg",
            "url": "#"
        }
    ]
    
    return render(request, "portfolio/home.html", {"projects": projects})
from django.shortcuts import render

def about_view(request):
    skills = [
        {"name": "Python", "icon": "images/python-icon.png"},
        {"name": "Django", "icon": "images/django-icon.png"},
        {"name": "JavaScript", "icon": "images/js-icon.png"},
        {"name": "React", "icon": "images/react-icon.png"},
    ]

    experiences = [
        {"title": "Full-Stack Developer", "company": "TechCorp", "year": "2021 - Present",
         "description": "Developed scalable web applications and APIs using Django and React."},
        {"title": "Software Engineer", "company": "Startup X", "year": "2019 - 2021",
         "description": "Built modern web solutions for e-commerce and finance sectors."},
    ]

    return render(request, "portfolio/about.html", {"skills": skills, "experiences": experiences})
from django.shortcuts import render

from django.shortcuts import render

# Sample Project Data (Replace with Database Query)
def projects_view(request):
    projects_list = [
        {
            "title": "Customer Service Automation",
            "description": "A Django-based internal tool that streamlined customer service workflows, reducing processing time significantly.",
            "challenge": "The existing system was slow and required manual data entry.",
            "solution": "Developed an automated workflow using Django and Google Cloud Functions.",
            "impact": "Reduced processing time by 40% and eliminated human errors.",
            "technology": "Django, Python, Google Cloud",
            "tags": ["Backend", "Automation", "Cloud"],
            "image": "images/project1.jpg",  # Ensure this file exists in static/images/
            "url": "https://github.com/yourgithub/customer-service-automation",
            "github": "https://github.com/yourgithub/customer-service-automation",
            "demo": "https://yourproject-demo.com"
        },
        {
            "title": "SaaS API Development",
            "description": "Designed a high-performance REST API for a SaaS platform, optimizing database queries and reducing latency.",
            "challenge": "High API response time and database overload due to inefficient queries.",
            "solution": "Refactored the database schema, added caching with Redis, and implemented Django REST Framework optimizations.",
            "impact": "Reduced API latency by 40% and improved uptime to 99.9%.",
            "technology": "Django REST Framework, PostgreSQL, Docker",
            "tags": ["Backend", "API", "Database Optimization"],
            "image": "images/project2.jpg",
            "url": "https://github.com/yourgithub/saas-api",
            "github": "https://github.com/yourgithub/saas-api",
            "demo": "https://yourproject-demo.com"
        },
        {
            "title": "AI-Powered Content Generator",
            "description": "Developed an AI-driven content generation tool using Python and OpenAI’s GPT-4 API.",
            "challenge": "Manual content creation was time-consuming and lacked personalization.",
            "solution": "Built an AI-powered text generator using FastAPI and OpenAI’s API.",
            "impact": "Reduced content generation time by 80% and increased engagement rates.",
            "technology": "Python, FastAPI, OpenAI API",
            "tags": ["AI", "Backend", "Machine Learning"],
            "image": "images/project3.jpg",
            "url": "https://github.com/yourgithub/ai-content-generator",
            "github": "https://github.com/yourgithub/ai-content-generator",
            "demo": "https://yourproject-demo.com"
        }
    ]

    return render(request, "portfolio/projects.html", {"projects": projects_list})

from core.utils import send_contact_form

def contact_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        # Validate form data
        if not name or not email or not message:
            messages.error(request, "All fields are required.")
            return redirect("contact")

        # Send email notification (update with your email settings)
        send_contact_form(message, email, name)

        # Display success message
        messages.success(request, "Your message has been sent successfully!")
        return redirect("contact")

    return render(request, "portfolio/contact.html")