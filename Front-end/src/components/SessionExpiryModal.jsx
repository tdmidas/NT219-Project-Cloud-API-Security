import React, { useState, useEffect } from 'react';
import './SessionExpiryModal.css';

const SessionExpiryModal = ({
    isVisible,
    timeLeft,
    onExtendSession,
    onLogout,
    message = "Phiên đăng nhập đã hết thời gian quy định. Bạn có muốn tiếp tục không?",
    isSessionExpired = false,
    isProcessing = false
}) => {
    const [countdown, setCountdown] = useState(timeLeft || 10);
    const [isButtonDisabled, setIsButtonDisabled] = useState(false);

    useEffect(() => {
        console.log("🔔 SessionExpiryModal effect triggered:", {
            isVisible,
            timeLeft,
            isSessionExpired,
            isProcessing
        });

        if (!isVisible) return;

        setCountdown(timeLeft || 10);
        setIsButtonDisabled(false);

        const timer = setInterval(() => {
            setCountdown(prev => {
                if (prev <= 1) {
                    clearInterval(timer);
                    setIsButtonDisabled(true);
                    console.log("⏰ Countdown reached 0 - triggering auto logout");
                    onLogout(); // Tự động logout khi hết thời gian
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);

        return () => {
            console.log("🧹 SessionExpiryModal cleanup - clearing timer");
            clearInterval(timer);
        };
    }, [isVisible, timeLeft, onLogout]);

    if (!isVisible) return null;

    const handleExtendClick = async () => {
        if (isButtonDisabled || isProcessing) {
            console.log("⚠️ Extend button disabled or processing, ignoring click");
            return;
        }

        setIsButtonDisabled(true);
        console.log("🔄 User clicked extend button");

        try {
            await onExtendSession();
            console.log("✅ Extend session completed");
        } catch (error) {
            console.error("❌ Error extending session:", error);
            setIsButtonDisabled(false);
        }
    };

    const handleLogoutClick = async () => {
        if (isButtonDisabled || isProcessing) {
            console.log("⚠️ Logout button disabled or processing, ignoring click");
            return;
        }

        setIsButtonDisabled(true);
        console.log("🚪 User clicked logout button");

        try {
            await onLogout();
            console.log("✅ Logout completed");
        } catch (error) {
            console.error("❌ Error logging out:", error);
        }
    };

    return (
        <div className="session-expiry-overlay">
            <div className="session-expiry-modal">
                <div className="session-expiry-header">
                    <div className="warning-icon">⏰</div>
                    <h3>Phiên làm việc đã hết</h3>
                </div>

                <div className="session-expiry-content">
                    <p className="expiry-message">
                        Phiên đăng nhập của bạn đã hết thời gian quy định (30 giây).
                        <br />
                        Bạn có muốn gia hạn phiên để tiếp tục sử dụng không?
                    </p>
                    <div className="countdown-container">
                        <div className="countdown-circle">
                            <span className="countdown-number">{countdown}</span>
                        </div>
                        <p className="countdown-text">
                            Tự động đăng xuất sau <strong>{countdown}</strong> giây nếu không chọn
                        </p>
                    </div>
                </div>

                <div className="session-expiry-actions">
                    <button
                        className={`btn-logout ${isButtonDisabled || isProcessing ? 'disabled' : ''}`}
                        onClick={handleLogoutClick}
                        disabled={isButtonDisabled || isProcessing}
                    >
                        {isProcessing ? "Đang đăng xuất..." : "Đăng xuất"}
                    </button>
                    <button
                        className={`btn-extend ${isButtonDisabled || isProcessing ? 'disabled' : ''}`}
                        onClick={handleExtendClick}
                        disabled={isButtonDisabled || isProcessing}
                    >
                        {isProcessing ? "Đang gia hạn..." : "Gia hạn phiên"}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SessionExpiryModal; 