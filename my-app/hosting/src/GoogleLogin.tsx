import { useState, useEffect } from 'react';

import { setting } from './env';

type User = {
  name: string;
  email: string;
  imageUrl: string;
} | null; // Include 'null' to allow the initial state to be null


function generateCodeVerifier(): string {
  const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';
  const minLength = 43;
  const maxLength = 128;
  const length = Math.floor(Math.random() * (maxLength - minLength + 1)) + minLength;
  let codeVerifier = '';

  for (let i = 0; i < length; i++) {
    const randomIndex = Math.floor(Math.random() * characters.length);
    codeVerifier += characters[randomIndex];
  }

  return codeVerifier;
}

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
    // Parameters to pass to OAuth 2.
    let params = {
      'client_id': '673278476323-gd8p0jcn0lspqs3e8n9civolog1n1b55.apps.googleusercontent.com',
      'redirect_uri': 'https://briefly-2ba6d.web.app/oauth-callback',
      'response_type': 'token',
      'scope': 'https://mail.google.com/ https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/userinfo.email openid',
      'include_granted_scopes': 'true',
      'state': 'pass-through value'
    };
    if (setting === 'desktop') {
      const codeVerifier: string = generateCodeVerifier();
      const code_challenge: string = codeVerifier;
      localStorage.setItem('codeVerifier', codeVerifier);
      // Parameters to pass to OAuth 2.
      params = {
        'client_id': '673278476323-ignesslvadclj3gtq1sgolcr6l5ro531.apps.googleusercontent.com',
        'redirect_uri': 'http://localhost:5173/oauth-callback-desktop',
        'response_type': 'code',
        'scope': 'https://mail.google.com/ https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/userinfo.email openid profile',
        'code_challenge': code_challenge,
        'code_challenge_method': 'plain',
      };
    }

    // Create the URL with parameters
    const url = `${oauth2Endpoint}?${new URLSearchParams(params)}`;

    // Redirect to the OAuth 2.0 endpoint
    window.location.href = url;
  };

  return (
    <div>
    {user ? (
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <img src={user.imageUrl} alt="Profile" style={{ borderRadius: '50%', marginRight: '10px', padding: '5px', border: '1px solid #ccc', width: '60px' }} />
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