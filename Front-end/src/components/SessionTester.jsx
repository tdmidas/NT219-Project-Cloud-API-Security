import React, { useState } from 'react';
import { useSessionManager } from '../hooks/useSessionManager';
import { authRequest } from '../services/authService';

const SessionTester = () => {
    const { sessionModal, initializeSession } = useSessionManager();
    const [testLog, setTestLog] = useState([]);
    const [isVisible, setIsVisible] = useState(false);

    const addLog = (message, type = 'info') => {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = { timestamp, message, type };
        setTestLog(prev => [...prev, logEntry]);
        console.log(`[${timestamp}] ${message}`);
    };

    const testQuickSession = async () => {
        addLog("🧪 Starting 10-second session test", 'info');

        try {
            // Simulate a quick session for testing
            const mockResponse = {
                access_token: "test_token_" + Date.now(),
                refresh_token: "test_refresh_" + Date.now(),
                expires_in: 10, // 10 seconds for quick testing
                refresh_expires_in: 600,
                message: "Test session initialized"
            };

            initializeSession(mockResponse);
            addLog("✅ 10-second test session started", 'success');
            addLog("⏰ Modal should appear in 10 seconds", 'info');
        } catch (error) {
            addLog(`❌ Test failed: ${error.message}`, 'error');
        }
    };

    const testRealLogin = async () => {
        addLog("🔐 Testing real login flow", 'info');

        try {
            const response = await authRequest({
                method: 'POST',
                url: '/auth/login',
                data: {
                    username: 'testuser123',
                    password: 'securepass123'
                }
            });

            if (response.data.success) {
                addLog("✅ Real login successful", 'success');
                addLog(`📊 Session: ${response.data.expires_in}s access, ${response.data.refresh_expires_in}s refresh`, 'info');

                initializeSession(response.data);
                addLog("🔄 Real session initialized", 'success');
            } else {
                addLog("❌ Login failed", 'error');
            }
        } catch (error) {
            addLog(`❌ Login error: ${error.message}`, 'error');
        }
    };

    const testRefreshToken = async () => {
        addLog("🔄 Testing refresh token manually", 'info');

        try {
            const refreshToken = sessionStorage.getItem('refreshToken');
            if (!refreshToken) {
                addLog("❌ No refresh token found", 'error');
                return;
            }

            const response = await authRequest({
                method: 'POST',
                url: '/auth/refresh',
                data: { refresh_token: refreshToken }
            });

            if (response.data.success) {
                addLog("✅ Manual refresh successful", 'success');
                addLog(`📊 New session: ${response.data.expires_in}s access`, 'info');

                // Update tokens
                sessionStorage.setItem('accessToken', response.data.access_token);
                if (response.data.refresh_token) {
                    sessionStorage.setItem('refreshToken', response.data.refresh_token);
                }
            } else {
                addLog("❌ Manual refresh failed", 'error');
            }
        } catch (error) {
            addLog(`❌ Refresh error: ${error.response?.data?.detail?.message || error.message}`, 'error');
        }
    };

    const clearLogs = () => {
        setTestLog([]);
        addLog("🧹 Logs cleared", 'info');
    };

    const getLogColor = (type) => {
        switch (type) {
            case 'success': return '#4CAF50';
            case 'error': return '#f44336';
            case 'warning': return '#ff9800';
            default: return '#333';
        }
    };

    if (!isVisible) {
        return (
            <button
                onClick={() => setIsVisible(true)}
                style={{
                    position: 'fixed',
                    bottom: '20px',
                    right: '20px',
                    background: '#007bff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '50%',
                    width: '60px',
                    height: '60px',
                    fontSize: '24px',
                    cursor: 'pointer',
                    zIndex: 9999,
                    boxShadow: '0 4px 12px rgba(0,123,255,0.3)'
                }}
                title="Open Session Tester"
            >
                🧪
            </button>
        );
    }

    return (
        <div style={{
            position: 'fixed',
            top: '20px',
            right: '20px',
            background: 'white',
            border: '2px solid #ddd',
            borderRadius: '12px',
            padding: '20px',
            width: '450px',
            maxHeight: '80vh',
            overflow: 'auto',
            zIndex: 9999,
            boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
            fontFamily: 'monospace'
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                <h3 style={{ margin: 0, color: '#333' }}>🧪 Session Tester</h3>
                <button
                    onClick={() => setIsVisible(false)}
                    style={{
                        background: '#f44336',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        padding: '4px 8px',
                        cursor: 'pointer'
                    }}
                >
                    ✖
                </button>
            </div>

            <div style={{ marginBottom: '15px' }}>
                <strong>📊 Modal Status:</strong>
                <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                    <div>Visible: {sessionModal.isVisible ? '✅ Yes' : '❌ No'}</div>
                    <div>Time Left: {sessionModal.timeLeft}s</div>
                    <div>Is Expired: {sessionModal.isSessionExpired ? 'Yes' : 'No'}</div>
                    <div>Processing: {sessionModal.isProcessing ? '⏳ Yes' : '❌ No'}</div>
                </div>
            </div>

            <div style={{ marginBottom: '15px' }}>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    <button
                        onClick={testQuickSession}
                        style={{
                            background: '#4CAF50',
                            color: 'white',
                            border: 'none',
                            padding: '8px 12px',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '12px'
                        }}
                    >
                        Quick Test (10s)
                    </button>

                    <button
                        onClick={testRealLogin}
                        style={{
                            background: '#2196F3',
                            color: 'white',
                            border: 'none',
                            padding: '8px 12px',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '12px'
                        }}
                    >
                        Real Login
                    </button>

                    <button
                        onClick={testRefreshToken}
                        style={{
                            background: '#ff9800',
                            color: 'white',
                            border: 'none',
                            padding: '8px 12px',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '12px'
                        }}
                    >
                        Test Refresh
                    </button>

                    <button
                        onClick={clearLogs}
                        style={{
                            background: '#f44336',
                            color: 'white',
                            border: 'none',
                            padding: '8px 12px',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '12px'
                        }}
                    >
                        Clear Logs
                    </button>
                </div>
            </div>

            <div style={{
                background: '#f8f9fa',
                border: '1px solid #e9ecef',
                borderRadius: '4px',
                padding: '10px',
                maxHeight: '300px',
                overflow: 'auto',
                fontSize: '11px'
            }}>
                <strong>📋 Test Logs:</strong>
                {testLog.length === 0 ? (
                    <div style={{ color: '#999', fontStyle: 'italic', marginTop: '8px' }}>
                        No logs yet. Run a test to see results.
                    </div>
                ) : (
                    testLog.map((log, index) => (
                        <div
                            key={index}
                            style={{
                                marginTop: '4px',
                                color: getLogColor(log.type),
                                borderLeft: `3px solid ${getLogColor(log.type)}`,
                                paddingLeft: '8px'
                            }}
                        >
                            <span style={{ color: '#666' }}>[{log.timestamp}]</span> {log.message}
                        </div>
                    ))
                )}
            </div>

            <div style={{ marginTop: '10px', fontSize: '10px', color: '#666' }}>
                💡 Tips: Use "Quick Test" to see modal behavior, "Real Login" for full flow, "Test Refresh" to manually refresh tokens.
            </div>
        </div>
    );
};

export default SessionTester; 