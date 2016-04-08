from bs4 import BeautifulSoup
from datetime import datetime
from django.contrib.admin.templatetags.admin_static import static
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase, Client

from molo.commenting.models import MoloComment
from molo.core.models import ArticlePage


class CommentingAdminTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            'testadmin', 'testadmin@example.org', 'testadmin')
        self.article = ArticlePage.objects.create(depth=5)
        self.content_type = ContentType.objects.get_for_model(self.article)
        self.client = Client()
        self.client.login(username='testadmin', password='testadmin')

    def mk_comment(self, comment, parent=None):
        return MoloComment.objects.create(
            content_type=self.content_type,
            object_pk=self.article.pk,
            content_object=self.article,
            site=Site.objects.get_current(),
            user=self.user,
            comment=comment,
            parent=parent,
            submit_date=datetime.now())

    def test_reply_link_on_comment(self):
        '''Every root comment should have the "Add reply" text and icon that
        has a link to the reply view for that comment.'''
        comment = self.mk_comment('comment text')
        changelist = self.client.get(
            reverse('admin:commenting_molocomment_changelist'))
        self.assertContains(
            changelist,
            '<img src="%s" alt="add" />' % (
                static('admin/img/icon_addlink.gif')),
            html=True)
        self.assertContains(
            changelist,
            '<a href="%s">Add reply</a>' % (
                reverse(
                    'admin:commenting_molocomment_reply',
                    kwargs={'parent': comment.pk})),
            html=True)

    def test_nested_replies(self):
        '''Replies to comments should be indented and ordered chronologically
        directly under the parent comment.'''
        comment = self.mk_comment('comment text')
        reply1 = self.mk_comment('reply 1 text', parent=comment)
        reply2 = self.mk_comment('reply 2 text', parent=comment)
        changelist = self.client.get(
            reverse('admin:commenting_molocomment_changelist'))

        html = BeautifulSoup(changelist.content, 'html.parser')
        table = html.find(id='result_list')
        [commentrow, reply1row, reply2row] = table.tbody.find_all('tr')
        self.assertTrue(comment.comment in commentrow.prettify())
        self.assertEqual(
            len(commentrow.find_all(style='padding-left:5px')), 1)
        self.assertTrue(reply1.comment in reply1row.prettify())
        self.assertTrue(reply2.comment in reply2row.prettify())
        self.assertEqual(
            len(reply1row.find_all(style='padding-left:15px')), 1)
        self.assertEqual(
            len(reply2row.find_all(style='padding-left:15px')), 1)

    def test_comments_reverse_chronological_order(self):
        '''The admin changelist view should display comments in reverse
        chronological order.'''
        comment1 = self.mk_comment('comment1')
        comment2 = self.mk_comment('comment2')
        comment3 = self.mk_comment('comment3')
        changelist = self.client.get(
            reverse('admin:commenting_molocomment_changelist'))

        html = BeautifulSoup(changelist.content, 'html.parser')
        table = html.find(id='result_list')
        [c3, c2, c1] = table.tbody.find_all('tr')
        self.assertTrue(comment3.comment in c3.prettify())
        self.assertTrue(comment2.comment in c2.prettify())
        self.assertTrue(comment1.comment in c1.prettify())

    def test_reply_to_comment_view(self):
        '''A get request on the comment reply view should return a form that
        allows the user to make a comment in reply to another comment.'''
        comment = self.mk_comment('comment')
        formview = self.client.get(
            reverse('admin:commenting_molocomment_reply', kwargs={
                'parent': comment.pk,
            }))
        self.assertTemplateUsed(formview, 'admin/reply.html')

    def test_reply_to_comment(self):
        '''A valid form should create a new comment that is a reply to an
        existing comment.'''
        comment = self.mk_comment('comment')
        formview = self.client.get(
            reverse('admin:commenting_molocomment_reply', kwargs={
                'parent': comment.pk,
            }))

        html = BeautifulSoup(formview.content, 'html.parser')
        data = {
            i.get('name'): i.get('value') or ''
            for i in html.form.find_all('input') if i.get('name')
        }
        data['comment'] = 'test reply text'

        response = self.client.post(
            reverse('admin:commenting_molocomment_reply', kwargs={
                'parent': comment.pk,
            }), data=data)
        comment = MoloComment.objects.get(pk=comment.pk)
        [reply] = comment.get_children()
        self.assertEqual(reply.comment, 'test reply text')
        self.assertRedirects(
            response, '%s?c=%d' % (
                reverse('admin:commenting_molocomment_changelist'),
                reply.pk),
            target_status_code=302)

    def test_reply_to_comment_ignore_fields(self):
        '''The form for replying to the comment should ignore certain fields
        in the request, and instead set them using user information.'''
        comment = self.mk_comment('comment')
        formview = self.client.get(
            reverse('admin:commenting_molocomment_reply', kwargs={
                'parent': comment.pk,
            }))

        html = BeautifulSoup(formview.content, 'html.parser')
        data = {
            i.get('name'): i.get('value') or ''
            for i in html.form.find_all('input') if i.get('name')
        }
        data['comment'] = 'test reply text'
        data['name'] = 'foo'
        data['url'] = 'http://bar.org'
        data['email'] = 'foo@bar.org'

        self.client.post(
            reverse('admin:commenting_molocomment_reply', kwargs={
                'parent': comment.pk,
            }), data=data)
        comment = MoloComment.objects.get(pk=comment.pk)
        [reply] = comment.get_children()

        self.assertEqual(reply.user_name, 'testadmin')
        self.assertEqual(reply.user_email, 'testadmin@example.org')
        self.assertEqual(reply.user_url, '')
