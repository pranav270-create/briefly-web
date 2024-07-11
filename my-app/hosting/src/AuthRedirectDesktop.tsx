import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import {baseUrl} from './env';

const OAuthRedirectDesktop = () => {
  const navigate = useNavigate();    

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    // Get the client secret from the backend
    fetch(`${baseUrl}/client_secret`, {
        method: 'GET',
        })
    .then(response => response.json())
    .then(data => {
    const clientSecret = data.client_secret;
    if (code) {
      // Prepare the data for the POST request
      const details = {
        code: code,
        code_verifier: localStorage.getItem('codeVerifier'),
        client_id: '673278476323-ignesslvadclj3gtq1sgolcr6l5ro531.apps.googleusercontent.com',
        client_secret: clientSecret,
        redirect_uri: 'http://localhost:5173/oauth-callback-desktop',
        grant_type: 'authorization_code',
      };

      // Convert the details object into URL-encoded form data
    let formBody = [];
    for (const property in details) {
      const encodedKey = encodeURIComponent(property);
      const encodedValue = encodeURIComponent(details[property]);
      formBody.push(encodedKey + "=" + encodedValue);
    }
    const formBodyString = formBody.join("&");

    // Send the request to the Google OAuth2 server
    fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formBodyString,
    })
    .then(response => response.json())
    .then(data => {
      console.log(data);
      localStorage.setItem('refreshToken', data.refresh_token);
      const accessToken = data.access_token;
      if (accessToken) {
        // Send the access token to your backend
        fetch(`${baseUrl}/token`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ access_token: accessToken}),
        })
        .then(response => response.json())
        .then(data => {
          console.log(data)
          // Store the JWT from your backend
          localStorage.setItem('jwtToken', data.access_token);
          localStorage.setItem('userEmail', JSON.stringify(data.user_email));
          localStorage.setItem('userFirstName', JSON.stringify(data.first_name));
          localStorage.setItem('userLastName', JSON.stringify(data.last_name));
          localStorage.setItem('userProfilePic', JSON.stringify(data.profile_pic));
          // Redirect to home with the updated data
          navigate('/');
        })
        .catch(error => {
          console.error('Error:', error);
          navigate('/');
        });
      } else {
        navigate('/');
      }

    })
    .catch(error => {
      console.error('Error:', error);
      navigate('/'); // Redirect to an error page or handle the error appropriately
    });
  }
})
}, [navigate]);

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
    }}>
      Authenticating User ... Please Wait
    </div>
  );
};

export default OAuthRedirectDesktop;