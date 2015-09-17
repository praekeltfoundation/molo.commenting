from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.test import TestCase

from molo.commenting.models import MoloComment
from django_comments.models import CommentFlag
from django_comments import signals


class MoloCommentTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            'test', 'test@example.org', 'test')
        self.content_type = ContentType.objects.get_for_model(self.user)

    def mk_comment(self, comment):
        return MoloComment.objects.create(
            content_type=self.content_type,
            object_pk=self.user.pk,
            content_object=self.user,
            site=Site.objects.get_current(),
            user=self.user,
            comment=comment,
            submit_date=datetime.now())

    def mk_comment_flag(self, comment, flag):
        return CommentFlag.objects.create(
            user=self.user,
            comment=comment,
            flag_date=datetime.now(),
            flag=flag)

    def test_parent(self):
        first_comment = self.mk_comment('first comment')
        second_comment = self.mk_comment('second comment')
        second_comment.parent = first_comment
        second_comment.save()
        [child] = first_comment.children.all()
        self.assertEqual(child, second_comment)

    def test_auto_remove_off(self):
        comment = self.mk_comment('first comment')
        comment.save()
        comment_flag = self.mk_comment_flag(comment,
                                            CommentFlag.SUGGEST_REMOVAL)
        comment_flag.save()
        signals.comment_was_flagged.send(
            sender=comment.__class__,
            comment=comment,
            flag=comment_flag,
            created=True,
        )
        altered_comment = MoloComment.objects.get(pk=comment.pk)
        self.assertFalse(altered_comment.is_removed)

    def test_auto_remove_on(self):
        comment = self.mk_comment('first comment')
        comment.save()
        comment_flag = self.mk_comment_flag(comment,
                                            CommentFlag.SUGGEST_REMOVAL)
        comment_flag.save()
        with self.settings(COMMENTS_FLAG_THRESHHOLD=1):
            signals.comment_was_flagged.send(
                sender=comment.__class__,
                comment=comment,
                flag=comment_flag,
                created=True,
            )
        altered_comment = MoloComment.objects.get(pk=comment.pk)
        self.assertTrue(altered_comment.is_removed)
