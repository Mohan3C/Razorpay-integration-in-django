

import razorpay
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from .models import Payment
from django.contrib.auth import login,logout,authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

def signup(request):
    if request.method =="POST":
        username = request.POST.get("username")
        pass1 = request.POST.get("pass1")
        pass2 = request.POST.get("pass2")
        if pass1==pass2:
            user = User()
            user.username = username
            user.set_password(pass1)
            user.save()
            login(request,user)
            return redirect(checkout)
        
    return render(request,"signup.html")

def login_user(request):
    if request.method =="POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request,username=username,password=password)
        return redirect(checkout)
    return render(request,"login.html")

def logout_user(request):
    logout(request)
    return redirect(login_user)

# Step 1: Checkout Page
def checkout(request):
    return render(request, "checkout.html")


# Step 2: Create Razorpay Order after POST
@login_required
def makepayment(request):
    print("Request method:", request.method)
    print("User:", request.user)

    if request.method == "POST":
        amount = 39900  # paise (₹399.00)

        # Initialize Razorpay Client
        client = razorpay.Client(auth=(settings.KEY, settings.SECRET))

        # Create order on Razorpay
        payment = client.order.create({"amount": amount,"currency": "INR","payment_capture": "1"})
        print('***************************************')
        print(f'clint:{ client}')
        print('***************************************')
        # Save order in DB
        payment_obj = Payment()
        payment_obj.user = request.user
        payment_obj.razorpay_order_id = payment["id"]
        payment_obj.amount = amount
        payment_obj.status = "created"
        payment_obj.save()
        print('****************************')
        print(f"payment:{payment}")
        print('****************************')
        print(f"payment_obj:{payment_obj}")
        print('****************************')
        return render(request, "payment.html", {
            "payment": payment,
            "razorpay_key": settings.KEY,
            "amount": amount
        })

    return redirect("checkout")


# Step 3: Payment Success Callback (Signature Verification)
@csrf_exempt
@login_required
def payment_success(request):
    if request.method == "POST":
        client = razorpay.Client(auth=(settings.KEY, settings.SECRET))

        print("*************************")
        print("first step")
        print("******************************")
        data = request.POST
        params_dict = {
            "razorpay_order_id": data.get("razorpay_order_id"),
            "razorpay_payment_id": data.get("razorpay_payment_id"),
            "razorpay_signature": data.get("razorpay_signature")
        }
        print("******************************")
        print("second step")
        print("**************************************")
        try:
            print("*************************************")
            print("verify payment")
            print("*************************************")
            # Verify payment signature
            client.utility.verify_payment_signature(params_dict)
            payment = Payment.objects.get(razorpay_order_id=params_dict["razorpay_order_id"])
            payment.razorpay_payment_id = params_dict["razorpay_payment_id"]
            payment.razorpay_signature = params_dict["razorpay_signature"]
            payment.status = "paid"
            payment.save()
            return render(request, "success.html", {"payment": payment})
        except:
            print("*************************************")
            print("payment failed")
            print("*************************************")
            return render(request, "failed.html")

    print("*************************************")
    print("it didn`t give a shit")
    print("*************************************")
    return redirect("checkout")
