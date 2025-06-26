import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

function LoginSuccess() {
    const [loading, setLoading] = useState(true);
    const [userInfo, setUserInfo] = useState(null);
    const [error, setError] = useState(null);
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();

    useEffect(() => {
        const handleAuthSuccess = async () => {
            try {
                // Get parameters from URL
                const username = searchParams.get('username');
                const email = searchParams.get('email');
                const isKeycloak = searchParams.get('keycloak') === 'true';
                const errorParam = searchParams.get('error');

                if (errorParam) {
                    setError(errorParam);
                    setTimeout(() => {
                        navigate("/login?error=" + errorParam, { replace: true });
                    }, 3000);
                    return;
                }

                if (username && email) {
                    const user = {
                        username: username,
                        email: email,
                        isKeycloak: isKeycloak
                    };

                    setUserInfo(user);

                    console.log("✅ User authenticated successfully:", user);

                    // Show success message for 2 seconds then redirect
                    // Don't store sensitive data in sessionStorage - let Header check auth status securely
                    setTimeout(() => {
                        navigate("/", { replace: true });
                        window.location.reload(); // Reload to trigger Header auth check
                    }, 2000);
                } else {
                    // Missing required parameters
                    setError("Missing user information");
                    setTimeout(() => {
                        navigate("/login?error=missing_params", { replace: true });
                    }, 3000);
                }
            } catch (error) {
                console.error("Error handling authentication success:", error);
                setError("Processing failed");
                setTimeout(() => {
                    navigate("/login?error=processing_failed", { replace: true });
                }, 3000);
            } finally {
                setLoading(false);
            }
        };

        handleAuthSuccess();
    }, [navigate, searchParams]);

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            fontFamily: '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif'
        }}>
            <div style={{
                textAlign: 'center',
                padding: '40px',
                backgroundColor: 'white',
                borderRadius: '15px',
                boxShadow: '0 20px 40px rgba(0,0,0,0.1)',
                maxWidth: '500px',
                width: '90%',
                animation: 'fadeIn 0.6s ease-out'
            }}>
                {loading ? (
                    <>
                        <div style={{
                            width: '50px',
                            height: '50px',
                            border: '4px solid #f3f3f3',
                            borderTop: '4px solid #667eea',
                            borderRadius: '50%',
                            animation: 'spin 1s linear infinite',
                            margin: '0 auto 20px'
                        }}></div>
                        <h2 style={{ color: '#333', marginBottom: '10px' }}>
                            🔐 Processing Authentication...
                        </h2>
                        <p style={{ color: '#666', fontSize: '16px' }}>
                            Please wait while we complete your login.
                        </p>
                    </>
                ) : error ? (
                    <>
                        <div style={{ fontSize: '60px', marginBottom: '20px' }}>❌</div>
                        <h2 style={{ color: '#dc3545', marginBottom: '10px' }}>
                            Authentication Failed
                        </h2>
                        <p style={{ color: '#666', fontSize: '16px' }}>
                            Error: {error}
                        </p>
                        <p style={{ color: '#666', fontSize: '14px', marginTop: '20px' }}>
                            Redirecting to login page...
                        </p>
                    </>
                ) : userInfo ? (
                    <>
                        <div style={{ fontSize: '60px', marginBottom: '20px' }}>🎉</div>
                        <h2 style={{
                            color: '#28a745',
                            marginBottom: '10px',
                            background: 'linear-gradient(45deg, #667eea, #764ba2)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            backgroundClip: 'text'
                        }}>
                            Welcome to Voux!
                        </h2>
                        <p style={{ color: '#333', fontSize: '18px', marginBottom: '10px' }}>
                            Hello, <strong>{userInfo.username}</strong>! 👋
                        </p>
                        <p style={{ color: '#666', fontSize: '14px', marginBottom: '10px' }}>
                            📧 {userInfo.email}
                        </p>
                        {userInfo.isKeycloak && (
                            <p style={{
                                color: '#667eea',
                                fontSize: '12px',
                                marginBottom: '20px',
                                backgroundColor: '#f8f9ff',
                                padding: '8px 12px',
                                borderRadius: '6px',
                                border: '1px solid #e0e6ff'
                            }}>
                                🔐 Secured by Keycloak
                            </p>
                        )}
                        <p style={{ color: '#666', fontSize: '14px' }}>
                            Taking you to the home page...
                        </p>
                    </>
                ) : null}
            </div>

            <style>
                {`
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                    @keyframes fadeIn {
                        from {
                            opacity: 0;
                            transform: translateY(20px);
                        }
                        to {
                            opacity: 1;
                            transform: translateY(0);
                        }
                    }
                `}
            </style>
        </div>
    );
}

export default LoginSuccess; 