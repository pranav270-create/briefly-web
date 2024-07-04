import { GoogleLogin } from '@react-oauth/google';
import { jwtDecode } from "jwt-decode";

const GoogleSignIn = ({ onLoginSuccess }: any) => {
  const handleSuccess = (credentialResponse: any) => {
    const decoded = jwtDecode(credentialResponse.credential);
    console.log(decoded);
    
    // Send the ID token to your backend
    onLoginSuccess(credentialResponse.credential);
  };

  const handleError = () => {
    console.log('Login Failed');
  };

  return (
    <GoogleLogin
      onSuccess={handleSuccess}
      onError={handleError}
      useOneTap
    />
  );
};

export default GoogleSignIn;