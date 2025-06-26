import React, { useEffect, useState, useRef } from 'react';
import { useSearchParams, useNavigate, useLocation } from 'react-router-dom';
import { getVouchersByPlatform, getVoucherCountByPlatform } from '../services/voucherService';
import VoucherList from '../components/Voucherlist.jsx';

// Logo các sàn
import shopeeLogo from "../img/san/shopee.png";
import lazadaLogo from "../img/san/lazada.png";
import tikiLogo from "../img/san/tiki.png";
import sendoLogo from "../img/san/sendo.png";
import nguyenKimLogo from "../img/san/nguyenkim.png";
import dienMayXanhLogo from "../img/san/dienmayxanh.png";
import fahasaLogo from "../img/san/fahasa.png";
import shopeefoodLogo from "../img/san/shopeefood.png";
import Logo from "../assets/icon.png";

import "../styles/Deals.css"; // CSS riêng cho Deals


const platformList = [
  { name: 'Tất cả các sàn', logo: Logo, param: 'all' },
  { name: 'Shopee', logo: shopeeLogo, param: 'shopee' },
  { name: 'Lazada', logo: lazadaLogo, param: 'lazada' },
  { name: 'Tiki', logo: tikiLogo, param: 'tiki' },
  { name: 'Sendo', logo: sendoLogo, param: 'sendo' },
  { name: 'Shopee Food', logo: shopeefoodLogo, param: 'shopeefood' },
  { name: 'Nguyễn Kim', logo: nguyenKimLogo, param: 'nguyen-kim' },
  { name: 'Điện Máy Xanh', logo: dienMayXanhLogo, param: 'dien-may-xanh' },
  { name: 'Fahasa', logo: fahasaLogo, param: 'fahasa' },
];

const platformMap = {
  'all': 'Tất cả các sàn',
  'shopee': 'Shopee',
  'lazada': 'Lazada',
  'tiki': 'Tiki',
  'sendo': 'Sendo',
  'shopeefood': 'Shopee Food',
  'nguyen-kim': 'Nguyễn Kim',
  'dien-may-xanh': 'Điện Máy Xanh',
  'fahasa': 'Fahasa'
};

const getPlatformFromUrl = (param) => platformMap[param] || 'Tất cả các sàn';

const getUrlFromPlatform = (platform) => {
  const found = Object.entries(platformMap).find(([key, value]) => value === platform);
  return found ? found[0] : 'all';
};

const Deals = (props) => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [selectedPlatform, setSelectedPlatform] = useState('Tất cả các sàn');
  const [filteredVouchers, setFilteredVouchers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [platformCounts, setPlatformCounts] = useState({});

  useEffect(() => {
    if (!searchParams.get('platform')) {
      navigate(`${location.pathname}?platform=all`, { replace: true });
    }
  }, [searchParams, navigate, location.pathname]);

  // Fetch số lượng voucher từng sàn khi load trang
  useEffect(() => {
    const fetchCounts = async () => {
      const counts = {};
      for (const p of platformList) {
        try {
          const count = await getVoucherCountByPlatform(p.param);
          counts[p.param] = count;
        } catch {
          counts[p.param] = 0;
        }
      }
      setPlatformCounts(counts);
    };
    fetchCounts();
  }, []);

  useEffect(() => {
    const platformParam = searchParams.get('platform') || 'all';
    setSelectedPlatform(getPlatformFromUrl(platformParam));
    setLoading(true);
    setError(null);
    
    getVouchersByPlatform(platformParam)
      .then(data => setFilteredVouchers(data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [searchParams]);

  const handlePlatformClick = (platform) => {
    setSelectedPlatform(platform);
    const urlParam = getUrlFromPlatform(platform);
    navigate(`?platform=${urlParam}`);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="deals-page">
      <div className="san-list-container">
        <h3 className="san-list-title">Lọc theo <span className="highlight">Sàn</span></h3>
        <ul className="san-list">
          {platformList.map((p, idx) => (
            <li key={idx} className="san-item">
              <button
                className={`san-button ${selectedPlatform === p.name ? 'active' : ''}`}
                onClick={() => handlePlatformClick(p.name)}
              >
                <img src={p.logo} alt={p.name} className="san-logo" />
                <span className="san-name">{p.name}</span>
                <span className="san-count">{platformCounts[p.param] ?? ''}</span>
              </button>
            </li>
          ))}
        </ul>
      </div>
      <div className="main-deals-container">
        <h2 className="title-main-deals">
          Danh sách mã giảm giá <span className="highlight">{selectedPlatform}</span>
        </h2>
        {loading ? (
          <div className="loading">Đang tải...</div>
        ) : error ? (
          <div className="error">{error}</div>
        ) : (
          <VoucherList vouchersData={filteredVouchers} setToast={props.setToast} />
        )}
      </div>
    </div>
  );
};

export default Deals;
