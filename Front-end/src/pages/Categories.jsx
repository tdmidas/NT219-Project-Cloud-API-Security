import React, {useEffect, useState}from 'react';
import { getUserVouchers } from "../services/voucherService";
import UserCard from "../components/Uservoucher";
import "../styles/Categories.css"; 

const categoryList = [
  { name: 'Tất cả danh mục', param: 'all' },
  { name: 'Thời trang', param: 'clothes' },
  { name: 'Thực phẩm', param: 'food' },
  { name: 'Điện tử', param: 'electronics' },
  { name: 'Nhà cửa', param: 'home' },
  { name: 'Du lịch', param: 'travel' },
  { name: 'Sức khỏe', param: 'health' },
  { name: 'Thể thao', param: 'sports' },
  { name: 'Làm đẹp', param: 'beauty' },
  { name: 'Sách', param: 'books' },
  { name: 'Đồ chơi', param: 'toys' },
  { name: 'Quà tặng', param: 'gifts' },
  { name: 'Thú cưng', param: 'pets' },
  { name: 'Nội thất', param: 'furniture' },
  { name: 'Ô tô', param: 'automotive' },
  { name: 'Phụ kiện', param: 'accessories' },
  { name: 'Văn phòng phẩm', param: 'stationery' },
  { name: 'Trẻ em', param: 'baby' },
  { name: 'Vườn', param: 'garden' },
  { name: 'Âm nhạc', param: 'music' },
  { name: 'Phim ảnh', param: 'movies' },
  { name: 'Trò chơi', param: 'games' },
  { name: 'Phần mềm', param: 'software' },
  { name: 'Dịch vụ', param: 'services' },
  { name: 'Khác', param: 'others' }
];

const UserVoucher = () => {
  const [vouchers, setVouchers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('Tất cả danh mục');
  const [filteredVouchers, setFilteredVouchers] = useState([]);

  useEffect(() => {
    const fetchUserVouchers = async () => {
      try {
        const data = await getUserVouchers();
        console.log("Vouchers fetched:", data);
        const voucherData = Array.isArray(data) ? data : [];
        setVouchers(voucherData);
        setFilteredVouchers(voucherData);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchUserVouchers();
  }, []);  const handleCategoryClick = (category, param) => {
    setSelectedCategory(category);
    if (category === 'Tất cả danh mục') {
      setFilteredVouchers(vouchers);
    } else {      const filtered = vouchers.filter(voucher => {
        if (!voucher.category) return false;
        return voucher.category === param;
      });
      
      setFilteredVouchers(filtered);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="deals-page">
      <div className="san-list-container">
        <h3 className="san-list-title">Lọc theo <span className="highlight">Danh mục</span></h3>
        <ul className="san-list">
          {categoryList.map((category, idx) => (
            <li key={idx} className="san-item">              <button
                className={`san-button ${selectedCategory === category.name ? 'active' : ''}`}
                onClick={() => handleCategoryClick(category.name, category.param)}
              >
                <span className="san-name">{category.name}</span>              <span className="san-count">
                  {category.name === 'Tất cả danh mục' 
                    ? vouchers.length 
                    : vouchers.filter(v => {
                        if (!v.category) return false;
                        return v.category === category.param;
                      }).length}
                </span>
              </button>
            </li>
          ))}
        </ul>
      </div>
      <div className="main-deals-container">
        <h2 className="title-main-deals">
          Danh sách Voucher
          {selectedCategory !== 'Tất cả danh mục' && (
            <span className="highlight"> - {selectedCategory}</span>
          )}
        </h2>
        <div className="voucher-grid">
          {filteredVouchers.map((voucher) => (
            <UserCard key={voucher._id} voucher={voucher} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default UserVoucher;