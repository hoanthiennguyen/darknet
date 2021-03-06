# Generated by Django 3.1.7 on 2021-03-21 15:43

from django.db import migrations, models
import django.db.models.deletion
import django_mysql.models


class Migration(migrations.Migration):

    dependencies = [
        ('slqe', '0002_auto_20210314_0801'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClassVersion',
            fields=[
                ('version', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('commit_hash', models.CharField(max_length=255)),
                ('date_time', models.DateTimeField()),
            ],
            options={
                'db_table': 'class_version',
            },
        ),
        migrations.AddField(
            model_name='image',
            name='expression',
            field=models.CharField(default=None, max_length=255),
        ),
        migrations.AddField(
            model_name='image',
            name='latex',
            field=models.CharField(default=None, max_length=255),
        ),
        migrations.AddField(
            model_name='image',
            name='roots',
            field=django_mysql.models.ListCharField(models.CharField(max_length=255), default=None, max_length=2560, size=10),
        ),
        migrations.AddField(
            model_name='user',
            name='password',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='uid',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='user',
            name='is_active',
            field=models.BooleanField(default=True, null=True),
        ),
        migrations.AlterModelTable(
            name='image',
            table='image',
        ),
        migrations.AlterModelTable(
            name='role',
            table='role',
        ),
        migrations.AlterModelTable(
            name='user',
            table='user',
        ),
        migrations.CreateModel(
            name='WeightVersion',
            fields=[
                ('version', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('url', models.CharField(max_length=255)),
                ('date_time', models.DateTimeField()),
                ('class_version', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='slqe.classversion')),
            ],
            options={
                'db_table': 'weight_version',
            },
        ),
    ]
