"""
My Very Own Car Dealership
by Matthew Smith-Burlage

Created: 2/26/2021
Last Edit: 2/27/2021

A car dealership represented by Django models with some testing functions.

Note:   To find implemented models, start on line 51.
        To find instantiated test data, start on line 181.
        To find solutions to requested queries, start on line 298.

        To find out how I actually *did* open my own dealership with my
            new found expertise just blindly run `open_dealership()`
            without looking at the code on line 382. :)

"""

import datetime
import time

from django.contrib.auth.models import User
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Count, When, IntegerField, Case


# Model validators

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

# Models


class Dealership(models.Model):
    """ Tracks each dealership instance """

    name = models.CharField(max_length=64)
    tag_line = models.CharField(max_length=250, null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.PROTECT)

    # Uses same year validation as cars for simplicity
    year_established = models.IntegerField(validators=[year_validator])

    def find_red_fords_under_30000(self):
        """
        Finds red fords under 30000 miles that are still on the lot (not sold)
        Returns them in descending order by list price
        """

        # Find cars from this dealership that match the requested criteria
        # Filter out cars that are not on the lot (aka already sold) and order the rest by list price

        return self.cars.filter(
            make__company_name="Ford",
            color__color_name='Red',
            mileage__lt=30000,
            sold_date__isnull=True
        ).order_by('-list_price_cents')

    # Related fields:)
    # - cars: QuerySet of Car Model objects that belong to the dealership (using `cars.all()`)

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
        """ Set sold price given a float """
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
        """ Set sold price given a float """
        if price >= 0:
            # Convert to integer (as cents) to avoid floating point imprecision
            self.list_price_cents = int(price * 100)
            self.save()
        else:
            raise ValueError("Price should not be negative.")

    def sell_car(self, sale_price):
        """ Marks car as sold today with price """
        if sale_price >= 0:
            self.sold_price = sale_price
            self.sold_date = datetime.date.today()
            self.save()
        else:
            raise ValueError("Price should not be negative.")

    def __str__(self):
        return f"{self.make} {self.model} ({self.year})"


# Testing functions

def populate_data():
    """ Adds test data to all needed models """

    # This could be refactored using for loops to make the code base
    # a bit smaller, but I've spelled out each car below for clarity.

    # Reset tables
    Dealership.objects.all().delete()
    User.objects.all().delete()
    Car.objects.all().delete()

    # Define dealership
    user = User.objects.create(
        username='rastley',
        first_name='Richard',
        last_name='Astley',
        email='rastley@aol.com'
    )
    user.set_password('NoStrangersToLove123!')

    dealer = Dealership.objects.create(
        name="Honest Rick's Car Emporium",
        tag_line="We will never let you down.",
        owner=user,
        year_established=1987,
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


def run_spec_queries(open_own_dealership=False):
    """
    Run the assigned queries front the specification based on the above models
    If specified, opens own car dealership, per specification :)
    """

    # Set up test data
    populate_data()

    # Run the queries

    # "Write a query to find all cars (no matter the dealership) with
    # mileage below an integer limit (eg 20,000 miles)"
    # -----------------------------------------------------------
    mileage_limit = 100000
    five_digit_mileage_cars = Car.objects.filter(mileage__lt=mileage_limit)

    # "Write a query to find all dealerships that have more than 3
    # cars on their lot that were established after 1980."
    # -----------------------------------------------------------
    # This query counts how many cars each dealership has
    # whose sold_date is null (aka still on the lot)
    # and then filters out dealerships with 2 or fewer such
    # cars and dealerships not established after 1980.
    # Of course, this could be done as a single line,
    # but this approach is much more readable.
    cars_on_lot = Count(Case(When(cars__sold_date__isnull=True, then=1), output_field=IntegerField(), ))
    old_dealers = Dealership.objects.annotate(num_cars=cars_on_lot).filter(year_established__gt=1980, num_cars__gte=3)

    # "Write a method for the dealership model that returns only red Fords under
    # 30,000 miles on their lot, ordered by price descending"
    # -----------------------------------------------------------
    dealership = Dealership.objects.first()
    red_fords_low_mileage = dealership.find_red_fords_under_30000()

    # Print results

    print("\"Write a query to find all cars (no matter the dealership) "
          "with mileage below an integer limit (eg 20,000 miles)\"")
    print(five_digit_mileage_cars)

    print("\"Write a query to find all dealerships that have more than 3 "
          "cars on their lot that were established after 1980.\"")
    print(old_dealers)

    print("\"Write a method for the dealership model that returns only red "
          "Fords under 30,000 miles on their lot, ordered by price descending\"")
    print(red_fords_low_mileage)

    input("Press enter to continue...")

    if open_own_dealership:
        open_dealership(dealership.name)


def run_tests():
    """ Run some tests. Of course, normally this would be done more methodically in tests.py. """

    cars = populate_data()

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


def do_all_the_things():
    run_tests()
    run_spec_queries(open_own_dealership=True)


def open_dealership(dealership_name="Honest Rick's Car Emporium"):
    """ Opens a car dealership """

    print("\"Open an actual car dealership with your newfound expertise :)\"")
    name = input("Okay, done. :) Please enter your name: ")

    print("\n\n\n\n")

    print(f'Hello {name}. Welcome to {dealership_name},')
    time.sleep(1)
    print("where we are...")

    for i in range(0, 3):
        time.sleep(1)
        print("\n\n")

    print("Never gonna give you up")
    time.sleep(2)
    print("Never gonna let you down")
    time.sleep(2)
    print("Never gonna run around ")
    time.sleep(2)
    print("and hurt you")
    time.sleep(2)
    print("\nNever gonna make you cry")
    time.sleep(2)
    print("Never gonna say goodbye")
    time.sleep(2)
    print("Never gonna tell a lie")
    time.sleep(2)
    print("and desert you")
    time.sleep(2)

    print("\n")

    print("More info: https://www.youtube.com/watch?v=dQw4w9WgXcQ")
