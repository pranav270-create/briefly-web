const GoogleLogin = () => {
  const oauthSignIn = () => {
    // Google's OAuth 2.0 endpoint for requesting an access token
    const oauth2Endpoint = 'https://accounts.google.com/o/oauth2/v2/auth';

    // Parameters to pass to OAuth 2.0 endpoint.
    const params = {
      'client_id': '673278476323-gd8p0jcn0lspqs3e8n9civolog1n1b55.apps.googleusercontent.com',
      'redirect_uri': 'https://briefly-2ba6d.web.app/oauth-callback',
      'response_type': 'token',
      'scope': 'https://mail.google.com/ https://www.googleapis.com/auth/calendar',
      'include_granted_scopes': 'true',
      'state': 'pass-through value'
    };

    // Create the URL with parameters
    const url = `${oauth2Endpoint}?${new URLSearchParams(params)}`;

    // Redirect to the OAuth 2.0 endpoint
    window.location.href = url;
  };

  return (
    <button onClick={oauthSignIn}>Sign in with Google</button>
  );
};

export default GoogleLogin;