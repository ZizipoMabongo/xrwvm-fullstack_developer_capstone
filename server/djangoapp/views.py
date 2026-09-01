# Uncomment the required imports before adding the code

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import logout
from django.contrib import messages
from datetime import datetime

from django.http import JsonResponse
from django.contrib.auth import login, authenticate
import logging
import json
import os
import requests
from django.views.decorators.csrf import csrf_exempt
from .models import CarMake, CarModel
# from .populate import initiate


# Get an instance of a logger
logger = logging.getLogger(__name__)

backend_url = os.getenv('backend_url', default="http://localhost:3030")
sentiment_analyzer_url = os.getenv('sentiment_analyzer_url', default="http://localhost:5050/")


def analyze_review_sentiments(text):
    request_url = sentiment_analyzer_url + "analyze/" + text
    try:
        response = requests.get(request_url)
        return response.json()
    except:
        return {"sentiment": "neutral"}


# Create your views here.

# Create a `login_request` view to handle sign in request
@csrf_exempt
def login_user(request):
    # Get username and password from request.POST dictionary
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    # Try to check if provide credential can be authenticated
    user = authenticate(username=username, password=password)
    data = {"userName": username}
    if user is not None:
        # If user is valid, call login method to login current user
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
    return JsonResponse(data)

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    logout(request)  # Terminate user session
    data = {"userName": ""}  # Return empty username
    return JsonResponse(data)

# Create a `registration` view to handle sign up request
@csrf_exempt
def registration(request):
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    first_name = data['firstName']
    last_name = data['lastName']
    email = data['email']

    username_exist = False
    try:
        User.objects.get(username=username)
        username_exist = True
    except:
        logger.debug("{} is new user".format(username))

    if not username_exist:
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            email=email,
        )
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
        return JsonResponse(data)
    else:
        data = {"userName": username, "error": "Already Registered"}
        return JsonResponse(data)
        
# Create a `get_dealerships` view to fetch all dealers
def get_dealerships(request):
    if request.method == "GET":
        endpoint = "/fetchDealers"
        url = backend_url + endpoint
        try:
            response = requests.get(url)
            dealers = response.json()
            return JsonResponse({"status": 200, "dealers": dealers})
        except Exception as e:
            return JsonResponse({"status": 500, "error": str(e)})

# Create a `get_dealerships_by_state` view to fetch dealers by state
def get_dealerships_by_state(request, state):
    if request.method == "GET":
        if state == "All":
            endpoint = "/fetchDealers"
        else:
            endpoint = "/fetchDealers/" + state
        url = backend_url + endpoint
        try:
            response = requests.get(url)
            dealers = response.json()
            return JsonResponse({"status": 200, "dealers": dealers})
        except Exception as e:
            return JsonResponse({"status": 500, "error": str(e)})

# Create a `get_dealer_details` view to fetch a single dealer
def get_dealer_details(request, dealer_id):
    if request.method == "GET":
        endpoint = "/fetchDealer/" + str(dealer_id)
        url = backend_url + endpoint
        try:
            response = requests.get(url)
            dealer = response.json()
            return JsonResponse({"status": 200, "dealer": dealer})
        except Exception as e:
            return JsonResponse({"status": 500, "error": str(e)})

# Create a `get_dealer_reviews` view to fetch reviews for a dealer
def get_dealer_reviews(request, dealer_id):
    if request.method == "GET":
        endpoint = "/fetchReviews/dealer/" + str(dealer_id)
        url = backend_url + endpoint
        try:
            response = requests.get(url)
            reviews = response.json()
            for review_detail in reviews:
                response = analyze_review_sentiments(review_detail['review'])
                review_detail['sentiment'] = response.get('sentiment', 'neutral')
            return JsonResponse({"status": 200, "reviews": reviews})
        except Exception as e:
            return JsonResponse({"status": 500, "error": str(e)})

# Create an `add_review` view to submit a review
@csrf_exempt
def add_review(request):
    if request.user.is_anonymous is False:
        data = json.loads(request.body)
        try:
            endpoint = "/insert_review"
            url = backend_url + endpoint
            response = requests.post(url, json=data)
            return JsonResponse({"status": 200})
        except Exception as e:
            return JsonResponse({"status": 401, "message": str(e)})
    else:
        return JsonResponse({"status": 403, "message": "Unauthorized"})

# Create a `get_cars` view to fetch car makes and models
def get_cars(request):
    car_models = CarModel.objects.select_related('car_make')
    return JsonResponse({"CarModels": cars})