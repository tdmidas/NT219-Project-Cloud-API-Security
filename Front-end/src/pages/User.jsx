import { useState, useEffect } from 'react';
import { checkAuthStatus } from '../services/authService';
import '../styles/User.css';
import avt from '../img/avatar/avt.jpg';


const User = () => {
    const [user, setUser] = useState(null);
    const [error, setError] = useState(null);
    const [vouchers, setVouchers] = useState([]);
    const [loading, setLoading] = useState(true);

    const handleUseVoucher = async (voucherId) => {
        try {
            console.log("Trying to delete voucher:", voucherId);
            // For now, just remove from local state since voucher integration needs work
            setVouchers(prev => prev.filter(voucher => voucher._id !== voucherId));
        }
        catch (error) {
            console.error("Failed to use (delete) voucher:", error);
            alert("Failed to use voucher. Please try again later.");
        }
    }

    useEffect(() => {
        const fetchUserProfile = async () => {
            try {
                setLoading(true);

                console.log("🔍 Fetching user profile securely...");

                // Use secure auth status check
                const authStatus = await checkAuthStatus();

                if (!authStatus.authenticated) {
                    console.log("🔄 User not authenticated, redirecting to login");
                    window.location.href = "/login";
                    return;
                }

                console.log("✅ User authenticated:", authStatus.user.username, authStatus.isKeycloak ? "(Keycloak)" : "(Traditional)");
                console.log("📋 User profile data:", authStatus.user);

                // Set user data from secure auth check
                setUser(authStatus.user);

                // For vouchers, set empty array for now since integration needs work
                // In a production environment, you'd want to have a separate voucher API
                // that's properly integrated with both auth systems
                setVouchers([]);

            } catch (error) {
                console.error('❌ Error fetching user profile:', error);
                setError("Failed to load profile. Please try again later.");

                // If authentication fails, redirect to login
                if (error.response?.status === 401 || error.response?.status === 403) {
                    console.log("🔄 Authentication failed, redirecting to login");
                    window.location.href = "/login";
                }
            } finally {
                setLoading(false);
            }
        };

        fetchUserProfile();
    }, []);

    if (loading) {
        return (
            <div className="loading">
                <div>Loading profile...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="loading">
                <div className="error-message">{error}</div>
            </div>
        );
    }

    if (!user) {
        return (
            <div className="loading">
                <div>No user data available</div>
            </div>
        );
    }

    return (
        <div className="user-profile">
            <div className="user-header">
                <img src={avt} alt="User Avatar" className="user-avatar" />
                <div className="user-info">
                    <h1>{user.username}</h1>
                    <p className="user-bio">{user.bio || "No bio available"}</p>
                    <div className="user-stats">
                        <div><strong>{user.vouchersPosted || 0}</strong> Vouchers Posted</div>
                        <div><strong>{user.vouchersSold || 0}</strong> Vouchers Sold</div>
                    </div>
                    <div className="user-theme">
                        <span>Theme: {user.theme || "light"}</span>
                    </div>
                    {user.email && (
                        <div className="user-email">
                            <span>📧 {user.email}</span>
                        </div>
                    )}
                </div>
            </div>

            {vouchers.length > 0 ? (
                vouchers.map((voucher) => (
                    <div key={voucher._id} className="user-card">
                        <div className="user-card-left">
                            <h3>{voucher.title}</h3>
                            <p>Loại: {voucher.voucherType}</p>
                            {voucher.category && <p>Danh mục: {voucher.category}</p>}
                            <p>Bắt đầu: {new Date(voucher.validityStart).toLocaleDateString()}</p>
                            <p>HSD: {new Date(voucher.validityEnd).toLocaleDateString()}</p>
                        </div>
                        <div className="user-card-right">
                            <p className="discount">Giảm <span className="discount-amount">{voucher.price}</span> đ</p>
                            <p>Đơn hàng tối thiểu: {voucher.minSpend}đ</p>
                            <p>Số lượng: {voucher.quantity}</p>
                            <div className="button-group">
                                <button className="banner-button" onClick={() => handleUseVoucher(voucher._id)}>Sử Dụng</button>
                            </div>
                        </div>
                    </div>
                ))
            ) : (
                <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
                    <p>No vouchers available</p>
                </div>
            )}
        </div>
    );
};

export default User;