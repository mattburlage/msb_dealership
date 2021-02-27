"""
My Very Own Car Dealership
by Matthew Smith-Burlage

Created: 2/26/2021
Last Edit: 2/27/2021

A car dealership represented by Django models and some testing functions

"""

import datetime
import time

from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Count, When, IntegerField, Case


def is_not_negative(value):
    return value >= 0


def year_validator(value):
    """ Validates car year based on some reasonable assumptions """

    # Uses Model T release year to be safe, but you could reasonably increase this to be more restrictive.
    earliest_year = 1908

    # Assumes cars model year will never more than 1 year out from current year.
    years_out = 1
    latest_year = datetime.date.today().year + years_out

    if not earliest_year <= value <= latest_year:
        raise ValidationError(f"Invalid car year. Must be between {earliest_year} and {latest_year}.")


class Dealership(models.Model):
    """ Tracks each dealership instance """

    name = models.CharField(max_length=64)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)

    # Uses same year validation as cars for simplicity
    year_established = models.IntegerField(validators=[year_validator])

    def find_red_fords_under_30000(self):
        # Find cars from this dealership that match the requested criteria
        cars = self.cars.filter(make__company_name="Ford", color__color_name='Red', mileage__lt=30000)
        # Filter out cars that are not on the lot (aka already sold) and order them by list price
        return cars.filter(sold_date__isnull=True).order_by('-list_price_cents')

    # Related fields:
    # - cars: QuerySet of Car Model objects that belong to the dealership

    def __str__(self):
        return self.name


class CarMakeOption(models.Model):
    """ List of options for car maker in Car model """

    company_name = models.CharField(max_length=128)

    def __str__(self):
        return self.company_name


class CarColorOption(models.Model):
    """ List of options for car maker in Car model """

    color_name = models.CharField(max_length=128)

    def __str__(self):
        return self.color_name


class CarModelOption(models.Model):
    """ List of options for car models in Car model """

    company = models.ForeignKey(CarMakeOption, on_delete=models.CASCADE)
    model_name = models.CharField(max_length=128)

    def __str__(self):
        return self.model_name


class Car(models.Model):
    """ Tracks each individual car entry and if it is sold """

    make = models.ForeignKey(CarMakeOption, on_delete=models.PROTECT)
    model = models.ForeignKey(CarModelOption, on_delete=models.PROTECT)
    year = models.IntegerField(validators=[year_validator])
    color = models.ForeignKey(CarColorOption, on_delete=models.PROTECT)

    dealership = models.ForeignKey(Dealership, on_delete=models.CASCADE, related_name='cars')

    mileage = models.IntegerField(validators=[is_not_negative])
    list_price_cents = models.IntegerField(verbose_name="List Price", validators=[is_not_negative],
                                           help_text="Listing price from the dealership (in cents).")
    sold_price_cents = models.IntegerField(verbose_name="Sold Price", null=True, blank=True,
                                           validators=[is_not_negative],
                                           help_text="What the dealership is selling it for (in cents)")
    sold_date = models.DateField(null=True, blank=True,
                                 help_text="Date the car was sold. No value means the car has not been sold yet.")

    def is_sold(self):
        """ Method to determine if the car has been sold based on sold_date """
        return bool(self.sold_date)

    @property
    def sold_price(self):
        """ Return sold price as a float """
        if self.sold_price_cents:
            return self.sold_price_cents / 100
        else:
            return None

    @sold_price.setter
    def sold_price(self, price):
        """ Set sold price given float """
        if price >= 0:
            # Convert to integer (as cents) to avoid floating point imprecision
            self.sold_price_cents = int(price * 100)
            self.save()
        else:
            raise ValueError("Price should not be negative.")

    @property
    def list_price(self):
        """ Return list price as a float """
        return self.list_price_cents / 100

    @list_price.setter
    def list_price(self, price):
        """ Set sold price given float """
        if price >= 0:
            # Convert to integer (as cents) to avoid floating point imprecision
            self.list_price_cents = int(price * 100)
            self.save()
        else:
            raise ValueError("Price should not be negative.")

    def sell_car(self, sale_price):
        """ Marks car as sold today with price """
        self.sold_price = sale_price
        self.sold_date = datetime.date.today()
        self.save()

    def __str__(self):
        return f"{self.make} {self.model} ({self.year})"


def populate_data():
    """ Adds test data to all needed models """

    # Reset tables
    Dealership.objects.all().delete()
    User.objects.all().delete()
    Car.objects.all().delete()

    # Define dealership
    user = User.objects.create(
        username='sbuschemi',
        first_name='Steve',
        last_name='Buschemi',
        email='sbuschemi@comcast.org'
    )
    user.set_password('IWasGreatInTheIsland2005!')

    dealer = Dealership.objects.create(
        name="Rick's Loyal Car Emporium",
        owner=user,
        year_established=1988,
    )

    # Define car1
    ford = CarMakeOption.objects.create(company_name="Ford")
    escape = CarModelOption.objects.create(model_name="Escape", company=ford)
    black = CarColorOption.objects.create(color_name="Black")
    car1 = Car.objects.create(
        make=ford,
        model=escape,
        year=2007,
        color=black,
        dealership=dealer,
        mileage=100005,
        list_price_cents=400000,
        sold_price_cents=None,
        sold_date=None
    )

    # Define car2
    subaru = CarMakeOption.objects.create(company_name="Subaru")
    forrester = CarModelOption.objects.create(model_name="Forrester", company=subaru)
    grey = CarColorOption.objects.create(color_name="Grey")
    car2 = Car.objects.create(
        make=subaru,
        model=forrester,
        year=2015,
        color=grey,
        dealership=dealer,
        mileage=30001,
        list_price_cents=1458700,
        sold_price_cents=1458805,
        sold_date=datetime.date.today() - datetime.timedelta(days=400),  # Comment to test old_dealerships
    )

    # Define car3
    fusion = CarModelOption.objects.create(model_name="Fusion", company=ford)
    red = CarColorOption.objects.create(color_name="Red")
    car3 = Car.objects.create(
        make=ford,
        model=fusion,
        year=2011,
        color=red,
        dealership=dealer,
        mileage=28302,
        list_price_cents=1057900,
        sold_price_cents=None,
        sold_date=None,
    )

    # Define car4
    smart = CarMakeOption.objects.create(company_name='smart')
    smartcar = CarModelOption.objects.create(model_name="car", company=smart)
    green = CarColorOption.objects.create(color_name="green")
    car4 = Car.objects.create(
        make=smart,
        model=smartcar,
        year=2012,
        color=green,
        dealership=dealer,
        mileage=6,
        list_price_cents=500,  # Yes, this is meant to be $5.00. :)
        sold_price_cents=499,  # Same as above.
        sold_date=datetime.date.today() - datetime.timedelta(days=100),  # Comment to test old_dealerships
    )

    # Define additional cars
    Car.objects.create(
        make=ford,
        model=escape,
        year=2009,
        color=red,
        dealership=dealer,
        mileage=20000,
        list_price_cents=700000,
    )
    focus = CarModelOption.objects.create(model_name="focus", company=ford)

    Car.objects.create(
        make=ford,
        model=focus,
        year=2008,
        color=grey,
        dealership=dealer,
        mileage=130000,
        list_price_cents=540000,
    )

    return [car1, car2, car3, car4]


def do_all_the_things():
    """ Run some tests. Of course, normally this would be done more methodically in tests.py. """
    cars = populate_data()

    # Testing for the model itself

    # test list price int to float
    assert cars[0].list_price == 4000.00

    # test the .is_sold method
    assert cars[3].is_sold()

    # test moving a car from not sold to sold manually
    assert not cars[2].is_sold()
    cars[2].sold_price = 3456.23
    cars[2].sold_date = datetime.date.today()
    cars[2].save()
    assert cars[2].is_sold()

    # test the .sell_car method
    assert not cars[0].is_sold()
    cars[0].sell_car(15444.45)
    assert cars[0].is_sold()

    # Re-set up data to run specified queries
    populate_data()

    # Run queries asked for by specification

    print("\"Write a query to find all cars (no matter the dealership) "
          "with mileage below an integer limit (eg 20,000 miles)\"")
    mileage_limit = 100000
    print(f"Mileage limit: {mileage_limit}")
    five_digit_mileage_cars = Car.objects.filter(mileage__lt=mileage_limit)
    print(five_digit_mileage_cars)

    print("\n")
    time.sleep(1)

    print("\"Write a query to find all dealerships that have more than 3 "
          "cars on their lot that were established after 1980.\"")
    # This query counts how many cars each dealership has whose sold_date is null (aka still on the lot, as asked)
    # And then filters out dealerships with 2 or fewer such cars and dealerships not established after 1980
    old_dealerships = Dealership.objects.annotate(
        num_cars=Count(Case(When(cars__sold_date__isnull=True, then=1), output_field=IntegerField(), ))
    ).filter(year_established__gt=1980, num_cars__gte=3)
    print(old_dealerships)

    print("\n")
    time.sleep(1)

    print("\"Write a method for the dealership model that returns only red "
          "Fords under 30,000 miles on their lot, ordered by price descending\"")
    dealership = Dealership.objects.first()
    red_fords_low_mileage = dealership.find_red_fords_under_30000()
    print(red_fords_low_mileage)

    print("\n")
    time.sleep(1)

    print("\"Open an actual car dealership with your newfound expertise :)\"")
    print("Okay, done. Please enter your name:")
    name = input()

    for i in range(0, 15):
        print("\n")

    print(f'Welcome {name} to {dealership.name} where we are...')
    time.sleep(3)

    for i in range(0, 15):
        print("\n")

    print("Never gonna give you up")
    time.sleep(2)
    print("Never gonna let you down")
    time.sleep(2)
    print("Never gonna run around ")
    time.sleep(2)
    print("and hurt you")
