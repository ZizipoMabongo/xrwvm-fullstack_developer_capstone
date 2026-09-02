from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.http import JsonResponse
from django.contrib.auth import login, authenticate
import logging
import json
import os
import requests
from django.views.decorators.csrf import csrf_exempt
from .models import CarModel


logger = logging.getLogger(__name__)

backend_url = os.getenv(
    'backend_url', default="http://localhost:3030"
)
sentiment_analyzer_url = os.getenv(
    'sentiment_analyzer_url', default="http://localhost:5050/"
)


def analyze_review_sentiments(text):
    request_url = sentiment_analyzer_url + "analyze/" + text
    try:
        response = requests.get(request_url)
        return response.json()
    except Exception:
        return {"sentiment": "neutral"}


@csrf_exempt
def login_user(request):
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    user = authenticate(username=username, password=password)
    data = {"userName": username}
    if user is not None:
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
    return JsonResponse(data)


def logout_request(request):
    logout(request)
    data = {"userName": ""}
    return JsonResponse(data)


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
    except Exception:
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


def get_dealer_reviews(request, dealer_id):
    if request.method == "GET":
        endpoint = "/fetchReviews/dealer/" + str(dealer_id)
        url = backend_url + endpoint
        try:
            response = requests.get(url)
            reviews = response.json()
            for review_detail in reviews:
                sentiment = analyze_review_sentiments(
                    review_detail['review']
                )
                review_detail['sentiment'] = sentiment.get(
                    'sentiment', 'neutral'
                )
            return JsonResponse({"status": 200, "reviews": reviews})
        except Exception as e:
            return JsonResponse({"status": 500, "error": str(e)})


@csrf_exempt
def add_review(request):
    if request.user.is_anonymous is False:
        data = json.loads(request.body)
        try:
            endpoint = "/insert_review"
            url = backend_url + endpoint
            requests.post(url, json=data)
            return JsonResponse({"status": 200})
        except Exception as e:
            return JsonResponse({"status": 401, "message": str(e)})
    else:
        return JsonResponse({"status": 403, "message": "Unauthorized"})


def get_cars(request):
    car_models = CarModel.objects.select_related('car_make')
    cars = []
    for car_model in car_models:
        cars.append({
            "CarModel": car_model.name,
            "CarMake": car_model.car_make.name
        })
    return JsonResponse({"CarModels": cars})
