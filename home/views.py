from django.shortcuts import render,HttpResponse,redirect
from .models import *
from django.contrib.auth import views as auth_views
from django.views import generic
from django.urls import reverse_lazy
from .forms import LoginForm, RegisterForm
import json 
from django.db.models import    Q
from collections import defaultdict
from django.db.models import Max,Min
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as django_logout
from django.contrib.auth.models import auth
from django.contrib.auth import get_user_model
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
import math
from pytonik_time_ago.timeago import timeago
from django.contrib.auth.decorators import login_required
import geopy.distance
from geopy.geocoders import Nominatim
from django.contrib import messages 
import time
User = get_user_model()
import requests


def common(request):
    feature_data = {}
    cities = list(PropertyCities.objects.all().order_by('name').values_list('name', flat=True))
    status = list(StatusMaster.objects.all().values_list('status', flat=True))
    feature_data['cities'] = cities
    feature_data['status'] = status
    feature_data['feature_list'] = FeatureMaster.objects.all()
    recent_properties = Properties.objects.all().order_by('-pub_date')[:4]
    for property in recent_properties:
        property.price = ("{:,}".format(property.price))
    feature_data['recent_properties'] = recent_properties

    return {
        'common_properties_data':feature_data
        }


def get_furniture_list(properties):
    properties_list = []
    for property in properties:
        d = defaultdict(list)
        prop = PropertyFurnitureMapper.objects.filter(property = property)
        for furniture in prop:    
            furniture.furniture_type = int(furniture.furniture_type)
            if furniture.furniture_type == 1:
                d['room'].append(furniture.furniture_counts.furniture_counts)
            elif furniture.furniture_type == 2:
                d['bathrooms'].append(furniture.furniture_counts.furniture_counts)
            elif furniture.furniture_type == 3:
                d['garage'].append(furniture.furniture_counts.furniture_counts)
        
        properties_dict = {
            "title":property.title,
            "id":property.id,
            "adddress":property.adddress,
            'area':property.area,
            'beds':d['beds'],
            'room':",".join(d['room']),
            'bathrooms':",".join(d['bathrooms']),
            'image':property.image,
            "price":property.price,
        }
        properties_list.append(properties_dict)
    
    return properties_list

def get_discounted_price(property):
    if PropertyOffers.objects.filter(property=property).exists():
       is_offer = PropertyOffers.objects.get(property=property)
       discount_price = property.price//100 * is_offer.discount.value
       discount_data = {"discounted_price":discount_price,
       "old_price":property.price,  
       "offer": is_offer.discount.value
       }
       return discount_data

def clean_property_data(property,user_id= None):
    d = defaultdict(list)
    prop = PropertyFurnitureMapper.objects.filter(property = property)
    for furniture in prop:    
        furniture.furniture_type = int(furniture.furniture_type)
        if furniture.furniture_type == 1:
            d['room'].append(furniture.furniture_counts.furniture_counts)
        elif furniture.furniture_type == 2:
            d['bathrooms'].append(furniture.furniture_counts.furniture_counts)
        elif furniture.furniture_type == 3:
            d['garage'].append(furniture.furniture_counts.furniture_counts)

    is_checked = None
    if user_id is not None:
        if UserFavProperties.objects.filter(property=property).filter(user=user_id).exists():
            is_checked = UserFavProperties.objects.filter(property=property).filter(user=user_id)[0].is_checked
    
    status_ls = PropertyStatusMapper.objects.filter(property = property).values_list('status__status',flat=True)
    if "Completed" in status_ls:
        status = "Completed" 
    else:
        status = 'Off plan'

    properties_dict = {
        "title":property.title,
        "id":property.id,
        "adddress":property.adddress,
        'area':property.area,
        'beds':d['beds'],
        'room':", ".join(d['room']),
        'bathrooms':", ".join(d['bathrooms']),
        'image':property.image,
        "price":("{:,}".format(property.price)),
        "pub_date":convert_time_ago(property.pub_date),
        "is_favorite":is_checked,
        "status":status,
        "yields":property.yields,
        'city':property.get_city_display,
        'type':property.get_type_display,
    }
    return properties_dict
    

def home_page(request):
    properties = Properties.objects.all()
    cleaned_properties = []
    for property_ in properties:
        prop = clean_property_data(property_)
        cleaned_properties.append(prop)
    team_members = TeamMembers.objects.all()
    return render(request,'user/index.html',{"properties":cleaned_properties,"team_members":team_members})


def about(request):
    return render(request,'user/about_us.html')


def property(request):
    return HttpResponse('property Page....')


def get_containing(choices, needle):
    containing = []
    for k, v in choices:
        if needle in v:
            containing.append(k)
    return containing


def property_list_by_type(request,in_type):
    if in_type == 'appartments':
        in_type = 'apartment'
    if in_type == 'studios':
        in_type = 'studio'
    type_dict = {}
    type_dict['type_id'] = 'type'
    type_dict['type_value'] = in_type
    feature_data = property_listing(request,type_dict)
    properties = feature_data['properties']
    return render(request,'user/property/properties-list-leftsidebar.html',{"properties":properties,"properties_data":feature_data})


def property_list_by_city(request,in_city):
    type_dict = {}
    type_dict['type_id'] = 'city'
    type_dict['type_value'] = in_city
    feature_data = property_listing(request,type_dict)
    properties = feature_data['properties']
    return render(request,'user/property/properties-list-leftsidebar.html',{"properties":properties,"properties_data":feature_data})


def convert_time_ago(time_date):
    time = time_date.strftime('%H:%M:%S')
    date = time_date
    mixed = str(date) + str(time)
    time_ago = timeago(f"{str(date)} {str(time)}").ago
    return time_ago.split(',')[0]
    return time_ago


def property_listing(request,type_dict=None):
    if type_dict == None:
        properties = Properties.objects.filter(is_underconstruction = False).filter(is_exclusive = False)

    elif type_dict['type_id'] == 'type':
        properties = Properties.objects.filter(type__in=get_containing(PROP_TYPE_CHOICES,type_dict['type_value'])).filter(is_underconstruction = False).filter(is_exclusive = False)
    
    elif type_dict['type_id'] == 'city':
        properties = Properties.objects.filter(city__in=get_containing(CITIES_CHOICES,type_dict['type_value'])).filter(is_underconstruction = False).filter(is_exclusive = False)
    

    sort_properties = request.GET.get('ordering', "") 
    
    query = {}
    query['status'] = request.GET.getlist('status', "")     
    query['type'] = request.GET.get('type', "")     
    query['price'] = request.GET.get('price', "")     
    query['city'] = request.GET.get('location', "")     
    query['bedrooms'] = request.GET.get('bedrooms', "")    
    query['bathrooms'] = request.GET.get('bathrooms', "")  
    query['balcony'] = request.GET.get('balcony', "")  
    query['garage'] = request.GET.get('garage', "")  
    query['min_area'] = request.GET.get('min_area', "") 
    query['max_area'] = request.GET.get('max_area', "") 
    query['min_price'] = request.GET.get('min_price', "") 
    query['max_price'] = request.GET.get('max_price', "") 
    query['features_list'] = request.GET.get('features_list', "") 
    query['features_list'] = [x for x in query['features_list'].split(',')]

    if request.GET.get('status', ""):
        properties = filter_property(query,properties)

    if sort_properties:
        properties_data = property_sorting(sort_properties,properties)
        properties = properties_data['properties']

    feature_data = {}    
    feature_data['selected_city'] = query['city']
    feature_data['selected_type']  = query['type']
    feature_data['selected_status']  = " ".join(query['status'])
    feature_data['selected_bedrooms']  = query['bedrooms']
    feature_data['selected_bathrooms']  = query['bathrooms']
    feature_data['selected_garage']  = query['garage']
    feature_data['selected_balcony']  = query['balcony']

    cleaned_properties = []
    for property_ in properties:
        try:
            prop = clean_property_data(property_,request.user)
        except:
            prop = clean_property_data(property_)

        cleaned_properties.append(prop)
    properties = cleaned_properties


    feature_data['properties'] = properties
    try:
        feature_data.update(properties_data)
    except:
        pass    

    PRODUCTS_PER_PAGE= 10
    page = request.GET.get('page',1)
    product_paginator = Paginator(properties, PRODUCTS_PER_PAGE)

    try:
        properties = product_paginator.page(page)
    except EmptyPage:
        properties = product_paginator.page(product_paginator.num_pages)
    except:
        properties = product_paginator.page(PRODUCTS_PER_PAGE)

    if type_dict is None:
        return render(request,'user/property/properties-list-leftsidebar.html',
        {"properties":properties,"properties_data":feature_data,
        'is_paginated':True, 'paginator':product_paginator,"page_obj":properties})

    return feature_data


def property_listing_map(request):
    return render(request,'user/property/properties_map.html')

import time

def property_view(request,id):
    st = time.time()
    feature_data = dict()
    property = Properties.objects.get(id = id)
    prop_images = PropertyImage.objects.filter(property = property)
    features = PropertyFeatureMapper.objects.filter(property=property)
    feature_data['feature_list'] = features    
    status = list(PropertyStatusMapper.objects.filter(property=property).values_list('status__status',flat=True))
    feature_data['status_list'] = ", ".join(status)

    d = defaultdict(list)
    prop = PropertyFurnitureMapper.objects.filter(property = property)
    for furniture in prop:    
        furniture.furniture_type = int(furniture.furniture_type)
        if furniture.furniture_type == 1:
            d['room'].append(furniture.furniture_counts.furniture_counts)
        elif furniture.furniture_type == 2:
            d['bathrooms'].append(furniture.furniture_counts.furniture_counts)
        elif furniture.furniture_type == 3:
            d['garage'].append(furniture.furniture_counts.furniture_counts)

    
    furniture_data = {"room":" & ".join(d['room']),
                      "bathrooms":" & ".join(d['bathrooms']),
                       "beds":" & ".join(d['beds'])
                    }

    similar_properties = Properties.objects.filter(city = property.city)[:2]
    page_data = {'page_name':property.title}
    Calculated_data = MortgageCalculator(property.price) 
    if request.is_ajax(): 
        properties_list = SendPropertiesToMap(request,property)
        return JsonResponse({'data':properties_list}) 

    location_coord = json.dumps([{'latitude':property.lat,"longitude":property.lon}])

    images_gallery = PropertyImage.objects.filter(property = 16)[:3]
    ed = time.time()
    property.price = ("{:,}".format(property.price))
    return render(request,'user/property/properties-details1.html',{'property':property,'prop_images':prop_images,"furniture_data":furniture_data,
    "similar_properties":similar_properties,"feature_data":feature_data,"Calculated_data":Calculated_data,"images_gallery":images_gallery,  
    "page_data":page_data,"location_coord":location_coord})
    # return render(request,'user/property/properties-details1.html')


def filter_property(query,properties):


    # Query Validation
    if query['city'] == 'City':
        query['city'] = ''

    if query['type'] == 'Type':
        query['type'] = ''

    if query['type'] == 'all_type':
        query['type'] = ''

    if len(query['features_list']) != 0:
        dt = PropertyFeatureMapper.objects.all()
        features_id = FeatureMaster.objects.filter(feature__in=query['features_list'])
        try:
            dt = dt.filter(feature=features_id[0])
            dt_ids = list(dt.values_list('property', flat=True))
            properties = properties.filter(id__in = dt_ids) 
        except:
            pass


    if not 'all' in query['status']:
        dt = PropertyStatusMapper.objects.all()
        status_id = StatusMaster.objects.filter(status__in=query['status'])
        dt = dt.filter(status__in=status_id)
        dt_ids = list(dt.values_list('property', flat=True))
        properties = properties.filter(id__in = dt_ids) 


    dt = PropertyFurnitureMapper.objects.all()
    if query['garage'] != 'Garage':
        dt1,dt2,dt3 = [],[],[]     
        dt1 = dt.filter(furniture_type__in=get_containing(FURNITURE_TYPE_CHOICES,"garage")).filter(
            furniture_counts=int(query['garage']))
        dt1 = list(dt1.values_list('property', flat=True))
        properties = properties.filter(id__in = dt1)  


    if query['bedrooms'] != 'Bedrooms': 
        dt2 = dt.filter(furniture_type__in=get_containing(FURNITURE_TYPE_CHOICES,"room")).filter(
            furniture_counts=int(query['bedrooms']))
        dt2 = list(dt2.values_list('property', flat=True))
        properties = properties.filter(id__in = dt2)

    if query['bathrooms'] != 'Bathroom': 
        dt3 = dt.filter(furniture_type__in=get_containing(FURNITURE_TYPE_CHOICES,"bathrooms")).filter(
            furniture_counts=int(query['bathrooms']))
        dt3 = list(dt3.values_list('property', flat=True))
        properties = properties.filter(id__in = dt3)
  

    properties = properties.filter(city__in=get_containing(CITIES_CHOICES,query["city"])).filter(
        price__range=(int(query['min_price']),int(query['max_price']))).filter(
        type__in = get_containing(PROP_TYPE_CHOICES,query['type'])
        )     

    #  .filter(
    #     area__range=(int(query['min_area']),int(query['max_area']))).
        
    return properties
 

def property_sorting(query,properties):
    properties_data = {}
    properties_data['is_price_low_high'] = ''
    properties_data['is_price_high_low'] = ''
    properties_data['is_latest_property'] = ''
    properties_data['is_oldest_property'] = ''

    if query:
        if query == "price_low_high":
            properties = properties.order_by('price')
            properties_data['is_price_low_high'] = 'selected'

        if query == 'price_high_low':
            properties = properties.order_by('price')[::-1]
            properties_data['is_price_high_low'] = 'selected'

        if query == "latest_property":
            properties = properties.order_by('pub_date')[::-1]
            properties_data['is_latest_property'] = 'selected'

        if query == "oldest_property":
            properties = properties.order_by('pub_date')
            properties_data['is_oldest_property'] = 'selected'
            
    properties_data['properties'] = properties
    return properties_data
    

def search(request):
    if request.is_ajax(): 
        query = request.GET.get('term', '')
        search_title = Properties.objects.filter(title__icontains=query.lower())
        search_type= Properties.objects.filter(type__in = get_containing(PROP_TYPE_CHOICES,query.lower()))

        results = []
        for type_name in (search_type): 
            if type_name.get_type_display() not in results:
                results.append(type_name.get_type_display())
        
        for title in search_title:
            if title.title not in results:
                results.append(title.title) 

        data = json.dumps(results)

        return HttpResponse(data)

    properties_data = {}
    query = request.GET.get('query', "") 
    properties_status = request.GET.getlist('properties_status', "") 
    properties = Properties.objects.filter(Q(title__contains=query) | Q(type__in=get_containing(PROP_TYPE_CHOICES,query.lower())))

    if not 'all' in properties_status:
        dt = PropertyStatusMapper.objects.all()
        status_id = StatusMaster.objects.filter(status__in=properties_status)
        dt = dt.filter(status__in=status_id)
        dt_ids = list(dt.values_list('property', flat=True))
        properties = properties.filter(id__in = dt_ids)

    sort_properties = request.GET.get('ordering', "") 
    if sort_properties:
        properties_data = property_sorting(sort_properties,properties)
        properties = properties_data['properties']

    fav_properties = list()
    try:
        for prop in properties:
            fav_properties.append(clean_property_data(prop,request.user)) 
            properties = fav_properties
    except:
        for prop in properties:
            fav_properties.append(clean_property_data(prop)) 
            properties = fav_properties      

    return render(request,'user/property/properties-list-leftsidebar.html',{"properties":properties,"properties_data":properties_data})


def send_mail():
    return None


def get_properties(in_property):
    lon1 = in_property.lat
    lat1 = in_property.lon
    properties = Properties.objects.filter(city=in_property.city)
    properties_list = []
    for property in properties:
         # Point two 
        lon2 = property.lon
        lat2 = property.lat
        coords_1 = (lon1, lat1)
        coords_2 = (lon2, lat2)
        distance = geopy.distance.geodesic(coords_1, coords_2).km 

        properties_list.append({
            "id": int(property.id),
            "title": str(property.title),
            "listing_for": "Sale",
            "is_featured": True,
            'author': 'Jhon Doe',
            'date': '5 days ago',
            "latitude": float(property.lat),
            "longitude": float(property.lon),
            "address": str(property.adddress),
            "city": str(property.get_city_display),
            "area":11,
            'bathroom':1,
            "garage": 1,
            'bedroom':1,
            "image": "/media/"+str(property.image),
            "type_icon": "img/building.png",
            "distance":distance})

    properties_list.sort(key=lambda x: x["distance"])
    return properties_list

def MortgageCalculator(amount):
    # api_url = 'https://api.api-ninjas.com/v1/mortgagecalculator?loan_amount=200000&interest_rate=3.5&duration_years=30'
    # response = requests.get(api_url, headers={'X-Api-Key': 'rYZ4Iou2RpRetFDwGcTwqw==VDxKG0pogTTruwfg'})
    # if response.status_code == requests.codes.ok:
    #     pass
    # else:
    #     pass
        
    data = {}
    principal = amount
    calculatedInterest = 3 / 100 / 12
    calculatedPayments = 20 * 12
    x = math.pow(1+calculatedInterest,calculatedPayments)
    monthly = (principal * x * calculatedInterest) / (x - 1)

    if math.isfinite(monthly):
        data['monthlyPayment'] = round(monthly,2)
        data['totalPayment'] = round((monthly * calculatedPayments),2)
        data['totalInterest'] = round((monthly * calculatedPayments - principal),2)
    return data

def stamp_duty_calculator(request):
    return render(request,'user/calculators/stamp_duty.html')

def mortgage_calculator(request):
    return render(request,'user/calculators/mortgage.html')


def thankyou_page(request):
    return render(request,'user/thankyou_page.html')


def SendPropertiesToMap(request,property):
    # property = Properties.objects.last()
    properties_list = get_properties(property)
    return properties_list     


def get_favorite_properties(request):
    if request.is_ajax(): 
        query = request.POST.get('fav_properties', '')
        query = json.loads(query)[0]
        
        property_id = Properties.objects.get(id=int(query['property_id']))
        if UserFavProperties.objects.filter(property=property_id,user= request.user).exists():
            UserFavProperties.objects.filter(property=property_id,user= request.user).update(is_checked=query['status'])
        else:
            UserFavProperties(user=request.user,property=property_id,is_checked = query['status']).save()

    return HttpResponse('OK.')

def property_form(request):
    fname = request.POST.get('fname')
    lname = request.POST.get('lname')
    email = request.POST.get('email')
    phone = request.POST.get('phone')
    message =  request.POST.get('message')

    return redirect('/thankyou')
    
def blog(request):
    return HttpResponse('blog Page....')

def resources(request):
    return render(request,'user/resources.html')

def download_assets(request):
    download_assets = DownloadableAssets.objects.all()
    return render(request,'user/download_assets.html',{"download_assets":download_assets})

def team_meber_view(request,name,id):
    team_member = TeamMembers.objects.get(id=id)
    return render(request,'user/team_member_view.html',{'team_member':team_member})

def CityGuide(request,city=None):
    properties_list = []
    properties = Properties.objects.all()
    for property in properties:
        d = defaultdict(list)
        prop = PropertyFurnitureMapper.objects.filter(property = property)
        for furniture in prop:    
            furniture.furniture_type = int(furniture.furniture_type)
            if furniture.furniture_type == 1:
                d['room'].append(furniture.furniture_counts.furniture_counts)
            elif furniture.furniture_type == 2:
                d['bathrooms'].append(furniture.furniture_counts.furniture_counts)
            elif furniture.furniture_type == 3:
                d['garage'].append(furniture.furniture_counts.furniture_counts)
        
        properties_dict = {
            "title":property.title,
            "id":property.id,
            "adddress":property.adddress,
            'area':property.area,
            'beds':d['beds'],
            'room':",".join(d['room']),
            'bathrooms':",".join(d['bathrooms']),
            'image':property.image,
            "price":property.price
        }
        properties_list.append(properties_dict)
    return render(request,'user/city_guide.html',{"properties":properties_list})

def contact(request):
    return render(request,'user/contact.html')

def newsletter(request):
    return render(request,'user/dashboard/newsletter.html')


def login(request,is_new_registered=False):
    if is_new_registered == True:
        messages.success(request, "Your Account has been successfully created. Please Login!")
    page_data = {}
    next = request.GET.get('next')
    if request.POST:
        loginusername = request.POST['username']
        loginpassword = request.POST['password']
        if User.objects.filter(username=loginusername).exists():
            user = authenticate(username=loginusername, password=loginpassword)
            if user is not None:
                auth.login(request, user)
                if next is not None:
                    return redirect(next)
                else:
                    return redirect('/')
            else:
                page_data['error'] = 'Invalid credentials! Please try again'

        else:
            page_data['error'] = "Account Not Found.."

    return render(request, 'auth/login.html', {'page_data': page_data})


def logout(request):
    django_logout(request)
    return redirect('/login')


def register(request):
    page_data = {}
    if request.method == "POST":
        first_name = request.POST['fname']
        last_name = request.POST['lname']
        username = request.POST['username']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        email = request.POST['email']
        phone = request.POST['phone']
        if password1 == password2:
            if User.objects.filter(username=username).exists():
                page_data['error'] = 'Username Taken'
                # return redirect('register')

            elif User.objects.filter(email=email).exists():
                page_data['error'] = 'Email Taken'
                # return redirect('register')
            else:
                user = User.objects.create_user(
                    first_name=first_name, last_name=last_name, username=username,  email=email, password=password1)
                user.save()
                return redirect('login',is_new_registered = True)
        else:
            page_data['error'] = 'Password not maching'
            # return redirect('register')
    
    return render(request, 'auth/register.html', {'page_data': page_data})


@login_required(redirect_field_name='next',login_url = '/login')
def profile(request):
    page_data = {}
    user = Profile.objects.get(user = request.user)
    if len(request.POST.get('fname',"")) > 1:   
        fname = request.POST.get('fname',"")
        lname = request.POST.get('lname',"")
        phone = request.POST.get('phone',"")
        email = request.POST.get('email',"")
        city = request.POST.get('city',"")
        user.fname = fname
        user.lname = lname
        user.email = email
        user.mobile = phone
        user.city = city
        user.save()
        messages.success(request, "Profile Updated Successfully!")
    page_data['is_profile'] = 'active'
    return render(request,'user/dashboard/profile.html',{'user':user,"page_data":page_data})


@login_required(redirect_field_name='next',login_url = '/login')
def favorite_properties(request): 
    page_data = {}
    property_ids = UserFavProperties.objects.filter(user= request.user).filter(is_checked = True).values_list("property_id",flat=True)
    properties = Properties.objects.filter(id__in = property_ids)        
    fav_properties = list()
    for prop in properties:
        fav_properties.append(clean_property_data(prop,request.user))
    
    page_data['is_favorite_properties'] = 'active'  
    return render(request,'user/dashboard/favorite_properties.html',
    {'fav_properties':fav_properties,"page_data":page_data}
    )


@login_required(redirect_field_name='next',login_url = '/login')
def exclusive_properties(request): 
    page_data = {}
    properties = Properties.objects.filter(is_exclusive = True)  
    fav_properties = list()
    for prop in properties:
        fav_properties.append(clean_property_data(prop,request.user))      
    
    page_data['is_exclusive_properties'] = 'active'
    return render(request,'user/dashboard/exclusive_properties.html',
    {'exclusive_properties':fav_properties,"page_data":page_data}
    )


@login_required(redirect_field_name='next',login_url = '/login')
def my_properties(request): 
    page_data = {}
    properties = Properties.objects.filter(is_exclusive = True)  
    fav_properties = list()
    for prop in properties:
        fav_properties.append(clean_property_data(prop,request.user))   
    page_data['is_my_properties'] = 'active'   
    return render(request,'user/dashboard/exclusive_properties.html',
    {'exclusive_properties':fav_properties,"page_data":page_data}
    )


@login_required(redirect_field_name='next',login_url = '/login')
def monthly_offers(request):
    page_data = {}
    properties = Properties.objects.filter(id__in = list(PropertyOffers.objects.all().values_list('property_id',flat=True)))
    cleaned_properties = []
    for property in properties:
        dicounted_values = get_discounted_price(property)
        if dicounted_values is not None:
            cleaned_dict = clean_property_data(property)
            cleaned_dict.update({'discounted_price':dicounted_values['discounted_price'],
            'offer':dicounted_values['offer']})
            cleaned_properties.append(cleaned_dict)
    page_data['is_offers'] = 'active'
    return render(request,'user/dashboard/discounted_properties.html',{'properties':cleaned_properties,"page_data":page_data})


@login_required(redirect_field_name='next',login_url = '/login')
def submit_property(request):    
    page_data = {}
    if request.method =="POST":
        query = {}
        query['images'] = request.FILES.get('files', "")
        query['propery_images'] = request.POST.getlist('files', "")
        query['title'] = request.POST.get('title', "")     
        query['status'] = request.POST.getlist('status', "")     
        query['type'] = request.POST.get('type', "")     
        query['address'] = request.POST.get('address', "")     
        query['city'] = request.POST.get('city', "")     
        query['bedrooms'] = request.POST.getlist('bedrooms', "")    
        query['bathrooms'] = request.POST.getlist('bathrooms', "")  
        query['postalcode'] = request.POST.get('postalcode', "")  
        query['message'] = request.POST.get('message', "")  
        query['area'] = request.POST.get('area', "") 
        query['price'] = request.POST.get('price', "") 
        query['features_list'] = request.POST.get('features_list', "") 
        query['features_list'] = [x for x in query['features_list'].split(',')]

    page_data['is_submit'] = 'active'
    return render(request,'user/dashboard/submit_property.html',{"page_data":page_data})


def property_updates(request):
    constructions = list()
    cons_titles = list()
    construction_updates = ConstructionUpdates.objects.all().order_by('pub_date')
    for construction in construction_updates:
        if construction.property.title not in cons_titles:
            constructions.append(construction)
            cons_titles.append(construction.property.title)
    #    d['title'].append(construction.property.title)
    #    d['image'].append(construction.property.title)     

    return render(request,'user/dashboard/construction_update.html',{'construction_updates':constructions})


def construction_update_view(request,property_name):    
    constructions_lst = list()
    construction_update_ids = ConstructionUpdates.objects.filter(property__title=property_name)
    # construction_update_imgs = ConstructionUpdatesImage.objects.filter(property_update_id__in = construction_update_ids)
    for construction_id in construction_update_ids:
        construction_update_imgs = ConstructionUpdatesImage.objects.filter(property_update_id = construction_id)
        constructions_dict = {
            'images':construction_update_imgs,
            "id":construction_id.id,
            "pub_date":construction_id.pub_date,
            "title":construction_id.title,
            "desc":construction_id.desc
        }
        constructions_lst.append(constructions_dict)

    page_data= {'page_name':construction_update_ids[0].property.title}
   

    return render(request,'user/dashboard/construction_update_view.html',{'page_data':page_data,
    "construction_update_imgs":construction_update_imgs,"constructions_lst":constructions_lst})


def faqs(request):
    return render(request,'user/faq.html')

def teams(request):
    team_members = TeamMembers.objects.all()
    return render(request,'user/teams.html',{'team_members':team_members})

def partners(request):
    return render(request,'user/partners.html')

class LoginView(auth_views.LoginView):
    form_class = LoginForm
    template_name = 'auth/login.html'


class RegisterView(generic.CreateView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('login')
