"""cegrad URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url

from main import views

urlpatterns = [
    url(r'^ajax/get_wordcloud', views.get_wordcloud, name='get_wordcloud'),
    url(r'^ajax/get_users', views.get_users, name='get_users'),
    url(r'admin-panel', views.admin_panel, name='admin-panel'),
    url(r'get-comments$', views.get_comments, name='get-comments'),
    url(r'get-wordclouds$', views.get_wordclouds, name='get-wordclouds'),
    url(r'get-profiles$', views.get_profiles, name='get-profiles'),
    url(r'get-opinions$', views.get_opinions, name='get-opinions'),
    url(r'get-pics$', views.get_pics, name='get-pics'),
    url(r'get-best-results$', views.get_best_results, name='get-best-results'),
    url(r'import-placeholders$', views.import_placeholders, name='import-placeholders'),
    url(r'import-data$', views.import_data, name='import-data'),
    url(r'best_election$', views.question, name='question'),
    url(r'^comments$', views.comments, name='comments'),
    url(r'^sgp_config', views.sgp_config, name='sgp_config'),
    url(r'^ajax/get_suggestions', views.get_suggestions, name='get_suggestions'),
    url(r'^toggle-tolerant', views.toggle_tolerant, name='toggle-tolerant'),
    url(r'^accept-word', views.accept_word, name='accept-word'),
    url(r'^reject-word', views.reject_word, name='reject-word'),
    url(r'^profile/(?P<username>[\w.]+)$', views.profile, name='profile'),
    url(r'^comment/delete$', views.delete_comment, name='delete-comment'),
    url(r'^comment/edit', views.edit_comment, name='edit-comment'),
    url(r'^comment$', views.comment, name='comment'),
    url(r'^word$', views.word, name='word'),
    url(r'^opinion/delete$', views.delete_opinion, name='delete-opinion'),
    url(r'^opinion/edit$', views.edit_opinion, name='edit-opinion'),
    url(r'^opinion$', views.opinion, name='opinion'),
    url(r'^login$', views.login, name='login'),
    url(r'^logout$', views.logout, name='logout'),
    url(r'^edit_profile$', views.edit_profile, name='edit_profile'),
    url(r'^signup$', views.signup, name='signup'),
    url(r'^people$', views.people, name='people'),
    url(r'^forgot_password$', views.forgot_password, name='forgot_password'),
    url(r'^get_password', views.get_password, name='get_password'),
    url(r'^best_results$', views.best_result, name='best_results'),
    url(r'^best_participation$', views.most_category_participation, name='best_category_participation'),
    url(r'^review$', views.review_comment, name='review_comment'),
    url(r'^comment/(?P<comment_id>\d+)/appeal/$', views.appeal_comment, name='appeal-comment'),
    url(r'^comment/(?P<comment_id>\d+)/overrule/$', views.overrule_comment, name='overrule-comment'),
    url(r'^comment/(?P<comment_id>\d+)/appeal/deny/$', views.deny_appeal_comment, name='deny-appeal-comment'),
    url(r'^comments/appealed/$', views.appealed_comments, name='appealed-comments'),
    url(r'^set_reviewers$', views.set_reviewers, name='set-reviewers'),
    url(r'^$', views.index, name='home'),
    url(r'^timeline$', views.timeline_page, name='timeline'),
    url(r'^timeline/like$', views.timeline_toggle_like, name='like_timeline'),
]

