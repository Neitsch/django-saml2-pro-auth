from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import (HttpResponse, HttpResponseRedirect,
                         HttpResponseServerError)

from onelogin.saml2.auth import OneLogin_Saml2_Auth

from .utils import SAMLError, prepare_django_request

User = get_user_model()

def get_provider_index(request):
    """Helper to get the saml config index of a provider in order to grab
    the proper user map"""
    req = prepare_django_request(request)
    try:
        provider = req['get_data']['provider']
    except KeyError:
        raise SAMLError("No provider specified in request")

    for index, provider_obj in enumerate(settings.SAML_PROVIDERS):
        if provider_obj.keys()[0] == provider:
            return provider, index

    raise SAMLError("The provider: %s was not found in settings.py" % provider)

def get_clean_map(user_map, saml_data):
    print('user_map')
    print(user_map)

    final_map = dict()
    for usr_k, usr_v in user_map.iteritems():
        print('looping')
        if type(usr_v) is dict:
            print('is dict')
            print(usr_v)

            if 'index' in usr_v:
                print('has index')
                final_map[usr_k] = saml_data[usr_v['key']][usr_v['index']]
            else:
                print('no index')
                final_map[usr_k] = saml_data[usr_v['key']]
        else:
            print('no dict')
            final_map[usr_k] = saml_data[ user_map[usr_k] ]

    print(final_map)

    return final_map

class Backend(object):

    def authenticate(self, request):
        if not request.session['samlSessionIndex'] or not request.session['samlUserdata']:
            return None

        provider, provider_index = get_provider_index(request)
        user_map = settings.SAML_USERS_MAP[provider_index][provider]

        final_map = get_clean_map(user_map, request.session['samlUserdata']) 



        user, _ = User.objects.get_or_create(**final_map)
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
