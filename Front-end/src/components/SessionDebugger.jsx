import React, { useState } from 'react';
import { useSessionManager } from '../hooks/useSessionManager';
import SessionExpiryModal from './SessionExpiryModal';

const SessionDebugger = () => {
    const {
        sessionModal,
        initializeSession,
        handleExtendSession,
        handleLogoutNow,
        hideModal
    } = useSessionManager();

    const [debugLog, setDebugLog] = useState([]);

    const addLog = (message) => {
        const timestamp = new Date().toLocaleTimeString();
        setDebugLog(prev => [...prev, `[${timestamp}] ${message}`]);
        console.log(message);
    };

    const testSession = () => {
        addLog("🧪 Starting session test with 5-second duration");

        // Simulate login response with very short session for testing
        const mockLoginResponse = {
            access_token: "test_token_" + Date.now(),
            refresh_token: "refresh_token_" + Date.now(),
            expires_in: 5, // 5 seconds for quick testing
            session_warning: "Test session will expire in 5 seconds"
        };

        initializeSession(mockLoginResponse);
        addLog("✅ Session initialized - modal should appear in 5 seconds");
    };

    const handleExtend = async () => {
        addLog("👤 User chose to extend session");
        const success = await handleExtendSession();
        if (success) {
            addLog("✅ Session extended successfully");
        } else {
            addLog("❌ Session extension failed");
        }
    };

    const handleLogout = async () => {
        addLog("👤 User chose to logout");
        await handleLogoutNow();
        addLog("✅ User logged out");
    };

    return (
        <div style={{
            position: 'fixed',
            top: '10px',
            right: '10px',
            background: 'white',
            border: '2px solid #ccc',
            padding: '15px',
            borderRadius: '8px',
            maxWidth: '400px',
            zIndex: 9999,
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
        }}>
            <h3>🔧 Session Debugger</h3>

            <button
                onClick={testSession}
                style={{
                    background: '#4CAF50',
                    color: 'white',
                    border: 'none',
                    padding: '8px 16px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    marginBottom: '10px'
                }}
            >
                Test 5-Second Session
            </button>

            <div style={{ marginBottom: '10px' }}>
                <strong>Modal Status:</strong> {sessionModal.isVisible ? '✅ Visible' : '❌ Hidden'}
                <br />
                <strong>Time Left:</strong> {sessionModal.timeLeft}s
                <br />
                <strong>Is Session Expired:</strong> {sessionModal.isSessionExpired ? 'Yes' : 'No'}
            </div>

            <div style={{
                background: '#f0f0f0',
                padding: '10px',
                borderRadius: '4px',
                maxHeight: '200px',
                overflow: 'auto',
                fontSize: '12px'
            }}>
                <strong>Debug Log:</strong>
                {debugLog.map((log, index) => (
                    <div key={index}>{log}</div>
                ))}
            </div>

            <button
                onClick={() => setDebugLog([])}
                style={{
                    background: '#ff6b6b',
                    color: 'white',
                    border: 'none',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    marginTop: '5px',
                    fontSize: '12px'
                }}
            >
                Clear Log
            </button>

            {/* Session Expiry Modal */}
            <SessionExpiryModal
                isVisible={sessionModal.isVisible}
                timeLeft={sessionModal.timeLeft}
                message={sessionModal.message}
                isSessionExpired={sessionModal.isSessionExpired}
                onExtendSession={handleExtend}
                onLogout={handleLogout}
            />
        </div>
    );
};

export default SessionDebugger; 