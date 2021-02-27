import datetime

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
        return self.sold_price / 100

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
        return self.list_price / 100

    @list_price.setter
    def list_price(self, price):
        """ Set sold price given float """
        if price >= 0:
            # Convert to integer (as cents) to avoid floating point imprecision
            self.list_price_cents = int(price * 100)
            self.save()
        else:
            raise ValueError("Price should not be negative.")

    def __str__(self):
        return f"{self.make} {self.model} ({self.year})"


def do_all_the_things():
    """ Execute all operations described in specification """

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
        name="Matt's Car Emporium and Hibachi Dinner Warehouse",
        owner=user,
        year_established=1988,
    )

    # Define car1
    ford = CarMakeOption.objects.create(company_name="Ford")
    escape = CarModelOption.objects.create(model_name="Escape", company=ford)
    black = CarColorOption.objects.create(color_name="Black")
    Car.objects.create(
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
    Car.objects.create(
        make=subaru,
        model=forrester,
        year=2015,
        color=grey,
        dealership=dealer,
        mileage=30001,
        list_price_cents=1458700,
        sold_price_cents=1458805,
        # sold_date=datetime.date.today() - datetime.timedelta(days=400),  # Comment/uncomment to test old_dealerships
    )

    # Define car3
    fusion = CarModelOption.objects.create(model_name="Fusion", company_id=2)
    red = CarColorOption.objects.create(color_name="Red")
    Car.objects.create(
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
    smartcar = CarModelOption.objects.create(model_name="car", company_id=2)
    green = CarColorOption.objects.create(color_name="green")
    Car.objects.create(
        make=smart,
        model=smartcar,
        year=2012,
        color=green,
        dealership=dealer,
        mileage=6,
        list_price_cents=500,
        sold_price_cents=499,
        # sold_date=datetime.date.today() - datetime.timedelta(days=100),  # Comment/uncomment to test old_dealerships
    )

    # Write a query to find all cars (no matter the dealership) with mileage below an integer limit (e.g. 20,000 miles)
    five_digit_mileage_cars = Car.objects.filter(mileage__lt=100000)

    # Write a query to find all dealerships that have more than 3 cars on their lot that were established after 1980

    # This query counts how many cars each dealership has whose sold_date is null (therefore still on the lot, as asked)
    # And then filters out dealerships with 2 or fewer such cars and dealerships not established after 1980
    old_dealerships = Dealership.objects.annotate(
        num_cars=Count(Case(When(cars__sold_date__isnull=True, then=1), output_field=IntegerField(),))
    ).filter(year_established__gt=1980, num_cars__gte=3)
