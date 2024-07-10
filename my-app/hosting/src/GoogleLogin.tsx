import { useState, useEffect } from 'react';

type User = {
  name: string;
  email: string;
  imageUrl: string;
} | null; // Include 'null' to allow the initial state to be null

const GoogleLogin = () => {
  // Use the User type for the state
  const [user, setUser] = useState<User>(null);

  useEffect(() => {
    const email = JSON.parse(localStorage.getItem('userEmail') || 'null');  
    const firstName = JSON.parse(localStorage.getItem('userFirstName') || 'null');
    const lastName = JSON.parse(localStorage.getItem('userLastName') || 'null');
    const profilePic = JSON.parse(localStorage.getItem('userProfilePic') || 'null');

    if (email && firstName && lastName && profilePic) {
      // Update user state
      setUser({
        name: `${firstName} ${lastName}`,
        email: email,
        imageUrl: profilePic
      });
    }
  }, []);

  const oauthSignIn = () => {
    // Google's OAuth 2.0 endpoint for requesting an access token
    const oauth2Endpoint = 'https://accounts.google.com/o/oauth2/v2/auth';

    // Parameters to pass to OAuth 2.0 endpoint.
    const params = {
      'client_id': '673278476323-gd8p0jcn0lspqs3e8n9civolog1n1b55.apps.googleusercontent.com',
      'redirect_uri': 'https://briefly-2ba6d.web.app/oauth-callback',
      'response_type': 'token',
      'scope': 'https://mail.google.com/ https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/userinfo.email',
      'include_granted_scopes': 'true',
      'state': 'pass-through value'
    };

    // Create the URL with parameters
    const url = `${oauth2Endpoint}?${new URLSearchParams(params)}`;

    // Redirect to the OAuth 2.0 endpoint
    window.location.href = url;
  };

  return (
    <div>
    {user ? (
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <img src={user.imageUrl} alt="Profile" style={{ borderRadius: '50%', marginRight: '10px' }} />
        <div>
          <div>{user.name}</div>
          <div>{user.email}</div>
        </div>
      </div>
    ) : (
    <button
          onClick={oauthSignIn}
          style={{
            padding: '10px', // Adjust padding for circular shape
            width: '50px', // Fixed width for circle
            height: '50px', // Fixed height for circle
            border: 'none',
            borderRadius: '50%', // Make it circular
            cursor: 'pointer',
            fontSize: '20px',
            display: 'flex', // Use flex to center the text/icon
            alignItems: 'center', // Center vertically
            justifyContent: 'center', // Center horizontally
            position: 'absolute', // Position the button
            top: '0', // Top right corner
            right: '0' // Top right corner
          }}
      >
      <span style={{ fontFamily: 'Arial', fontWeight: 'bold', color: '#4285F4' }}>G</span>
  </button>
    )}
  </div>
  );
};

export default GoogleLogin;