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
      localStorage.setItem('accessToken', accessToken);
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
        // Store the JWT from your backend
        localStorage.setItem('token', data.access_token);
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

  return <div>Processing authentication...</div>;
};

export default OAuthRedirect;