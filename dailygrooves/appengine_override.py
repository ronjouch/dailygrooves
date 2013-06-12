from oauth2client.appengine import OAuth2Decorator, \
    InvalidClientSecretsError, clientsecrets


class OAuth2DecoratorFromClientSecrets_ApprovalPromptForce(OAuth2Decorator):
    """
    Ugly override of OAuth2DecoratorFromClientSecrets, but using
    'approval_prompt': 'force'
    """

    def __init__(self, filename, scope, message=None):
        try:
            client_type, client_info = clientsecrets.loadfile(filename)
            if client_type not in [clientsecrets.TYPE_WEB, clientsecrets.TYPE_INSTALLED]:
                raise InvalidClientSecretsError('OAuth2Decorator doesn\'t support this OAuth 2.0 flow.')
            super(OAuth2DecoratorFromClientSecrets_ApprovalPromptForce,
                  self).__init__(
                      client_info['client_id'],
                      client_info['client_secret'],
                      scope,
                      client_info['auth_uri'],
                      client_info['token_uri'],
                      message,
                      approval_prompt='force')  # the only addition
        except clientsecrets.InvalidClientSecretsError:
            self._in_error = True
        if message is not None:
            self._message = message
        else:
            self._message = "Please configure your application for OAuth 2.0"
