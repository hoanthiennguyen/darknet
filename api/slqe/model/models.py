from django.conf import settings
from django.db import models
from django_mysql.models import ListCharField
import jwt
from datetime import datetime, timedelta
import time


# Create your models here.


class Role(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

    @classmethod
    def create(cls, role_id, name):
        return cls(id=role_id, name=name)

    @classmethod
    def admin_role(cls):
        return cls.create(2, "ADMIN")

    @classmethod
    def customer_role(cls):
        return cls.create(1, "CUSTOMER")

    class Meta:
        db_table = 'role'


class User(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.CharField(max_length=255, null=True)
    uid = models.CharField(max_length=255, null=True, unique=True)
    password = models.CharField(max_length=255, null=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    phone = models.CharField(max_length=255, null=True)
    avatar_url = models.CharField(max_length=255, null=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        """
        Returns a string representation of this `User`.

        This string is used when a `User` is printed in the console.
        """
        return self.uid

    @property
    def token(self):
        """
        Allows us to get a user's token by calling `user.token` instead of
        `user.generate_jwt_token().

        The `@property` decorator above makes this possible. `token` is called
        a "dynamic property".
        """
        return self._generate_jwt_token()

    def _generate_jwt_token(self):
        """
        Generates a JSON Web Token that stores this user's ID and has an expiry
        date set to 60 days into the future.
        """
        dt = datetime.now() + timedelta(days=15)
        expired = time.mktime(dt.timetuple())
        token = jwt.encode({
            'id': self.id,
            'exp': int(expired)
        }, settings.SECRET_KEY, algorithm='HS256')

        return token

    @classmethod
    def create(cls, email, uid, password, phone, avatar_url, name, role):
        return cls(email=email, uid=uid, password=password, role=role, phone=phone, avatar_url=avatar_url, name=name)

    class Meta:
        db_table = 'user'


class Image(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.CharField(max_length=255)
    date_time = models.DateTimeField()
    expression = models.CharField(max_length=255, default=None)
    latex = models.CharField(max_length=255, default=None)
    roots = ListCharField(
        base_field=models.CharField(max_length=255),
        size=10,
        max_length=(10 * 256),
        default=None
        # 6 * 10 character nominals, plus commas
    )
    success = models.BooleanField(default=True)
    message = models.CharField(max_length=255, default='')

    class Meta:
        db_table = 'image'

    @classmethod
    def create(cls, user, url, date_time, expression, latex, roots, success, message):
        return cls(user=user, url=url + "_" + str(date_time), date_time=date_time, expression=expression,
                   latex=latex, roots=roots, success=success, message=message)


class ClassVersion(models.Model):
    id = models.AutoField(primary_key=True, default=None)
    version = models.CharField(max_length=255, unique=True)
    commit_hash = models.CharField(max_length=255)
    created_date = models.DateTimeField(default=datetime.now)
    description = models.CharField(max_length=255, default="")

    class Meta:
        db_table = 'class_version'


class WeightVersion(models.Model):
    id = models.AutoField(primary_key=True, default=None)
    version = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    created_date = models.DateTimeField(default=datetime.now, blank=True)
    is_active = models.BooleanField(default=False)
    class_version = models.ForeignKey(ClassVersion, on_delete=models.CASCADE)
    loss_function_path = models.CharField(max_length=255, default="")
    log_path = models.CharField(max_length=255, default="")

    @classmethod
    def create(cls, version, url, class_version, loss_function_path, log_path):
        return cls(version=version, url=url, class_version=class_version, loss_function_path=loss_function_path,
                   log_path=log_path)

    class Meta:
        db_table = 'weight_version'


class Notification(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=2550)
    created_date = models.DateTimeField(default=datetime.now)
    is_read = models.BooleanField(default=False)
    url = models.CharField(max_length=255, default=None)
    is_delete = models.BooleanField(default=False)
    is_success = models.BooleanField(default=False)
    loss_function_path = models.CharField(max_length=255, default="")
    log_path = models.CharField(max_length=255, default="")

    class Meta:
        db_table = 'notification'
