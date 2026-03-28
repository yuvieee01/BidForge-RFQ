import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../utils/auth';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="sticky top-0 z-50 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        {/* Logo */}
        <NavLink to="/auctions" className="flex items-center gap-2 group">
          <span className="text-xl">🔨</span>
          <span className="font-bold text-slate-100 group-hover:text-blue-400 transition-colors">
            BritAuction <span className="text-blue-500">RFQ</span>
          </span>
        </NavLink>

        {/* Nav links */}
        {user && (
          <div className="flex items-center gap-6 text-sm">
            <NavLink
              to="/auctions"
              className={({ isActive }) =>
                `transition-colors font-medium ${isActive ? 'text-blue-400' : 'text-slate-400 hover:text-slate-200'}`
              }
            >
              Auctions
            </NavLink>
            {user.role === 'buyer' && (
              <NavLink
                to="/rfq/create"
                className={({ isActive }) =>
                  `transition-colors font-medium ${isActive ? 'text-blue-400' : 'text-slate-400 hover:text-slate-200'}`
                }
              >
                + New RFQ
              </NavLink>
            )}
          </div>
        )}

        {/* User info + logout */}
        {user ? (
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <p className="text-xs font-semibold text-slate-200">{user.name}</p>
              <p className="text-xs text-slate-500 capitalize">{user.role}</p>
            </div>
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-sm font-bold text-white">
              {user.name?.charAt(0).toUpperCase()}
            </div>
            <button
              onClick={handleLogout}
              className="text-xs text-slate-500 hover:text-red-400 transition-colors"
            >
              Sign out
            </button>
          </div>
        ) : (
          <NavLink to="/login" className="text-sm text-blue-400 hover:text-blue-300 font-medium transition-colors">
            Sign in →
          </NavLink>
        )}
      </div>
    </nav>
  );
}
