# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2017-08-03 15:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtail_personalisation', '0012_remove_personalisablepagemetadata_is_segmented'),
        ('commenting', '0007_add_current_site_to_all_comments'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentDataRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expected_content', models.TextField(help_text="Content that we want to match in user's comment data.", verbose_name='expected content')),
                ('operator', models.CharField(choices=[(b'eq', 'equals'), (b'in', 'contains')], default=b'in', help_text='"Equals" operator will match only the exact content. "Contains" operator matches a part of a comment.', max_length=3, verbose_name='operator')),
                ('segment', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='commenting_commentdatarule_related', related_query_name='%(app_label)s_%(class)ss', to='wagtail_personalisation.Segment')),
            ],
            options={
                'verbose_name': 'comment data rule',
            },
        ),
    ]
