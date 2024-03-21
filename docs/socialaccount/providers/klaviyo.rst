Klaviyo
-------

You will need to register a Klaviyo app to obtain a client ID and secret.

App registration
****************

With a Klaviyo account, you can create a new OAuth app at::

    https://www.klaviyo.com/manage-apps

In the app creation form (optionally) fill in the development callback URL::

    http://127.0.0.1:8000/accounts/klaviyo/login/callback/

For production use a callback URL such as::

   https://{{yourdomain}}.com/accounts/klaviyo/login/callback/


Setting up provider
*******************

* ``name``, up to you to choose (optional)
* ``client_id``, is called "Client ID"
* ``secret``, is called "Client Secret"
