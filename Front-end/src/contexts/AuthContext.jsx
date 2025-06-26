import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { checkAuthStatus } from '../services/authService';

const AuthContext = createContext();

// Action types
const AUTH_ACTIONS = {
    SET_LOADING: 'SET_LOADING',
    SET_AUTHENTICATED: 'SET_AUTHENTICATED',
    SET_UNAUTHENTICATED: 'SET_UNAUTHENTICATED',
    UPDATE_USER: 'UPDATE_USER',
    LOGOUT: 'LOGOUT'
};

// Initial state
const initialState = {
    isAuthenticated: false,
    user: null,
    loading: true
};

// Reducer function
const authReducer = (state, action) => {
    switch (action.type) {
        case AUTH_ACTIONS.SET_LOADING:
            return {
                ...state,
                loading: action.payload
            };
        case AUTH_ACTIONS.SET_AUTHENTICATED:
            return {
                ...state,
                isAuthenticated: true,
                user: action.payload,
                loading: false
            };
        case AUTH_ACTIONS.SET_UNAUTHENTICATED:
            return {
                ...state,
                isAuthenticated: false,
                user: null,
                loading: false
            };
        case AUTH_ACTIONS.UPDATE_USER:
            return {
                ...state,
                user: { ...state.user, ...action.payload }
            };
        case AUTH_ACTIONS.LOGOUT:
            return {
                ...state,
                isAuthenticated: false,
                user: null,
                loading: false
            };
        default:
            return state;
    }
};

// AuthProvider component
export const AuthProvider = ({ children }) => {
    const [state, dispatch] = useReducer(authReducer, initialState);

    // Check authentication status on app load
    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        try {
            dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: true });
            const authStatus = await checkAuthStatus();

            if (authStatus.authenticated) {
                dispatch({
                    type: AUTH_ACTIONS.SET_AUTHENTICATED,
                    payload: authStatus.user
                });
                console.log("✅ User authenticated:", authStatus.user.username);
            } else {
                dispatch({ type: AUTH_ACTIONS.SET_UNAUTHENTICATED });
                console.log("❌ User not authenticated");
            }
        } catch (error) {
            console.error("Failed to check authentication:", error);
            dispatch({ type: AUTH_ACTIONS.SET_UNAUTHENTICATED });
        }
    };

    // Login function - to be called after successful login
    const login = (userData) => {
        dispatch({
            type: AUTH_ACTIONS.SET_AUTHENTICATED,
            payload: userData
        });
        console.log("✅ User logged in via context:", userData.username);
    };

    // Logout function
    const logout = () => {
        dispatch({ type: AUTH_ACTIONS.LOGOUT });
        console.log("👋 User logged out via context");
    };

    // Update user data
    const updateUser = (userData) => {
        dispatch({
            type: AUTH_ACTIONS.UPDATE_USER,
            payload: userData
        });
    };

    // Refresh auth status
    const refreshAuth = async () => {
        await checkAuth();
    };

    const value = {
        ...state,
        login,
        logout,
        updateUser,
        refreshAuth,
        checkAuth
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

// Custom hook to use auth context
export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export default AuthContext; 