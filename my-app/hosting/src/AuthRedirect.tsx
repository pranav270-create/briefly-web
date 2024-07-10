import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import baseUrl from './env';

const OAuthRedirect = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const hash = window.location.hash.substring(1);
    const params = new URLSearchParams(hash);
    const accessToken = params.get('access_token');

    if (accessToken) {
      // Send the access token to your backend
      fetch(`${baseUrl}/token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ access_token: accessToken }),
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

export default OAuthRedirect;