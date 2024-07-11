import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';

import OAuthRedirect from './AuthRedirect';
import OAuthRedirectDesktop from './AuthRedirectDesktop';
import Home from './Home'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/oauth-callback" element={<OAuthRedirect />} />
        <Route path="/oauth-callback-desktop" element={<OAuthRedirectDesktop />} />
      </Routes>
    </Router>
  );
}

export default App;